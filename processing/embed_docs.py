"""
embed_docs.py
This will create chunks from the cleaned .txt files of our documentation, embed them, and store then in Pinecone vector store.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

from langchain_text_splitters import MarkdownTextSplitter
from langchain_community.document_loaders import TextLoader

# Get API keys
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_region = os.getenv("PINECONE_REGION")

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)

# Create the index
dim = 512
index_name = f"raccoon-docs-{dim}"

if not pc.has_index(index_name):
    pc.create_index(name=index_name,
                    dimension=dim,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=pinecone_region),
                    deletion_protection="enabled")
    print(f"Created Pinecone index: {index_name}")
else:
    print(f"Pinecone index `{index_name}` already exists.")


# Load in and chunk the markdown files
def load_and_chunk(folder_path: str) -> list[Document]:
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)
    all_chunks = []
    for file in Path(folder_path).rglob("*.md"):
        loader = TextLoader(str(file), encoding='utf-8')
        docs = loader.load()
        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)
    return all_chunks


docs = load_and_chunk("./data/clean_text_pages")
print(f"Loaded and chunked {len(docs)} document chunks.")


# Embed and store
def embed_and_store(docs: list[str]):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small",
                                  dimensions=dim,
                                  openai_api_type=openai_api_key)

    vectorstore = PineconeVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,
        index_name=index_name,
        pinecone_api_key=pinecone_api_key
    )

    print("Embeddings stored in Pinecone vector store.")


embed_and_store(docs)
