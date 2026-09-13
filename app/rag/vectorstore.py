"""
Tenant-isolated Vector Store Management for ResolveAI.
Maintains distinct vector indexes per company_id using FAISS and sentence-transformers embeddings.
"""

from pathlib import Path
from typing import Dict, List, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.rag.ingestion import load_company_documents, split_documents

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# In-memory registry of company vector stores
_company_vector_stores: Dict[int, FAISS] = {}


def get_or_create_company_vectorstore(company_id: int = 1, force_reload: bool = False) -> FAISS:
    """
    Retrieve or initialize the FAISS vector index for a specific company tenant.
    """
    global _company_vector_stores

    if company_id in _company_vector_stores and not force_reload:
        return _company_vector_stores[company_id]

    documents = load_company_documents(company_id=company_id)
    chunks = split_documents(documents)

    if chunks:
        vector_store = FAISS.from_documents(chunks, embeddings)
    else:
        # Create an empty placeholder document for the tenant
        placeholder = [Document(page_content=f"ResolveAI Knowledge Base for Company {company_id}", metadata={"source": "system", "company_id": company_id})]
        vector_store = FAISS.from_documents(placeholder, embeddings)

    _company_vector_stores[company_id] = vector_store
    return vector_store


def add_documents_to_company_store(company_id: int, documents: List[Document]):
    """
    Add chunked documents to a company's vector store index.
    """
    global _company_vector_stores
    vstore = get_or_create_company_vectorstore(company_id=company_id)
    vstore.add_documents(documents)
    _company_vector_stores[company_id] = vstore


# Backward compatibility alias
create_vector_store = get_or_create_company_vectorstore
