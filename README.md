# raccoon-chatbot
An AI chatbot that answers technical questions about RACCOON's finite element framework using up to date documentation. It utilizes retrieval-augmented-generation (RAG) to provide accurate answers based on the documentation.

## Goals
Project Goals: New users of RACCOON often struggle to navigate its extensive syntax and function library. They may not know what tools are available or how to locate them, and even when found, the documentation may lack clear explanations. This chatbot aims to serve as an intelligent assistant that helps users locate and understand RACCOON features.

Personal Goals: Gain hands-on experience with LangChain and LangGraph by developing a fully functional RAG-based application. The project also serves as a way to deepen my understanding of building AI assistants that are accurate, domain-specific, and production-ready.

## Stack Used
- **LangChain**: building the RAG pipeline  
- **LangGraph**: graph-based control flow for managing agent behavior  
- **OpenAI API**: used for embedding generation and llm responses
- **Pinecone**: vector database for fast and scalable semantic search 
- **BeautifulSoup & Requests**: For scraping and cleaning RACCOON documentation
- **Streamlit**: for frontend application 

## How to Run
1. Clone this repository
2. Install the relevant packages from `requirements.txt`
3. Run app locally with: 
```bash
streamlit run app.py
```

