from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from typing import Any, List, Optional
from pydantic import Field
import os

# Import Claude CLI client
from claude_cli_client import call_claude


# Simple RAG Chain class that doesn't use deprecated RetrievalQA
class SimpleRAGChain:
    """Simple RAG chain using Claude CLI"""

    def __init__(self, retriever):
        self.retriever = retriever

    def run(self, query: str) -> str:
        """Run the RAG chain"""
        # Retrieve relevant documents
        docs = self.retriever.get_relevant_documents(query)

        # Format context from retrieved documents
        context = "\n\n".join([doc.page_content for doc in docs])

        # Create prompt for Claude
        prompt = f"""Based on the following log excerpts, answer the question.

Log Context:
{context}

Question: {query}

Please provide a detailed answer based on the log information above."""

        # Call Claude
        response = call_claude(prompt)
        return response


# Load logs and embed
def build_vectorstore(log_path="logs/sample.log"):
    loader = TextLoader(log_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)

    # Use HuggingFace embeddings instead of Ollama
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    db = FAISS.from_documents(split_docs, embeddings)
    db.save_local("embeddings")
    return db

def build_vectorstore_from_all_logs(log_dir="logs"):
    all_docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    for filename in os.listdir(log_dir):
        if filename.endswith(".log"):
            filepath = os.path.join(log_dir, filename)
            loader = TextLoader(filepath)
            docs = loader.load()
            split_docs = splitter.split_documents(docs)
            all_docs.extend(split_docs)

    if not all_docs:
        raise ValueError("No .log files found to index.")

    # Use HuggingFace embeddings instead of Ollama
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    db = FAISS.from_documents(all_docs, embeddings)
    db.save_local("embeddings")
    return db

def get_qa_chain():
    # Use HuggingFace embeddings instead of Ollama
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    db = FAISS.load_local("embeddings", embeddings, allow_dangerous_deserialization=True)

    retriever = db.as_retriever(search_kwargs={"k": 3})

    # Use simple RAG chain instead of deprecated RetrievalQA
    chain = SimpleRAGChain(retriever)
    return chain


