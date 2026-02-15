from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from typing import Any, List, Optional
from pydantic import Field
import os

# Import Claude CLI client
from claude_cli_client import call_claude


# Custom LangChain LLM wrapper for Claude
class ClaudeLLM(LLM):
    """Custom LangChain LLM wrapper for Claude API"""

    model_name: str = Field(default="claude-3-5-sonnet-20241022")

    @property
    def _llm_type(self) -> str:
        return "claude"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Call Claude API"""
        return call_claude(prompt)

    @property
    def _identifying_params(self):
        """Return identifying parameters"""
        return {"model_name": self.model_name}


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
    # Use Claude via custom LLM wrapper
    llm = ClaudeLLM()

    chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    return chain


