import os
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model  # chat model
from langchain_openai import OpenAIEmbeddings  # embeddings model
from langchain_pinecone import PineconeVectorStore  # pinecone vector store
from pinecone import Pinecone  # pinecone vector store

from langgraph.graph import MessagesState, StateGraph, END  # for message-based graph state
from langchain_core.tools import tool  # defines a function as a schema
from langchain_core.messages import SystemMessage, AIMessage  # system message
from langgraph.prebuilt import ToolNode, tools_condition  # executes tools
from langgraph.checkpoint.memory import MemorySaver  # enables conversation memory

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_region = os.getenv("PINECONE_REGION")

# Instatiate LLM and embeddings model
llm = init_chat_model("gpt-4.1-nano-2025-04-14",
                      model_provider="openai",
                      temperature=0.2)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small",
                              dimensions=512,
                              api_key=openai_api_key)

# Intatiate vector store
pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index("raccoon-docs-512")
vector_store = PineconeVectorStore(embedding=embeddings, index=index)


# Create retrieval function that will be used as a tool to grab related documents
@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve RACCOON documentation related to a query"""
    retrieved_docs = vector_store.similarity_search(query=query, k=4)
    summary = "\n\n".join(
        f"Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
        for doc in retrieved_docs)
    return summary, retrieved_docs


# --- Define Nodes ---
def query_or_respond(state: MessagesState):
    """Generate tool call for retrieval or respond."""
    llm_with_tools = llm.bind_tools([retrieve
                                     ])  # these are the available tools to use
    response = llm_with_tools.invoke(
        state["messages"]
    )  # decides whether it can answer directly, or a tool needs to be called
    return {
        "messages": [response]
    }  # MessagesState appends messages to state instead of overwriting


tools = ToolNode([retrieve])  # node for retrieval tool

def generate(state: MessagesState):
    """Generate answer."""
    # Get generated ToolMessages
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # Fomat prompt
    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_message_content = (
        "You are an expert assistant answering questions strictly based on the RACCOON documentation. "
        "Use only the retrieved context below to answer the user's question. "
        "Do not provide general knowledge or external explanations, answer only if the information is directly supported by the documentation. "
        "If the answer is not in the context, say you don't know. "
        "Be concise and use no more than three sentences. "
        "\n\n"
        f"{docs_content}")
    conversation_messages = [
        message for message in state["messages"]
        if message.type in ("human", "system") or (
            message.type == "ai" and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_message_content)] + conversation_messages

    # Run
    response = llm.invoke(prompt)
    return {"messages": [response]}


# Add memory
memory = MemorySaver()

# --- Building Graph ---
graph_builder = StateGraph(state_schema=MessagesState)

graph_builder.add_node(query_or_respond)
graph_builder.add_node(tools)
graph_builder.add_node(generate)

graph_builder.set_entry_point("query_or_respond")
graph_builder.add_conditional_edges(
    "query_or_respond",
    tools_condition,
    {
        END: END,
        "tools": "tools"
    },
)
graph_builder.add_edge("tools", "generate")
graph_builder.add_edge("generate", END)

graph = graph_builder.compile(checkpointer=memory)

# Visualize the graph
graph_image = graph.get_graph().draw_mermaid_png()
with open("ai_graph.png", "wb") as f:
    f.write(graph_image)


# Wrapper function to import in front end application
def process_input(input_message: str):
    config = {"configurable": {"thread_id": "abc123"}}
    for chunk, metadata in graph.stream(
        {"messages": [{
            "role": "user",
            "content": input_message
        }]},
            stream_mode="messages",
            config=config):
        if isinstance(chunk, AIMessage):
            yield chunk.content
