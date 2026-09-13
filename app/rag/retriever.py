"""
Tenant-isolated Retriever Factory for ResolveAI.
"""

from app.rag.vectorstore import get_or_create_company_vectorstore


def get_company_retriever(company_id: int = 1, k: int = 3):
    """
    Returns a retriever scoped exclusively to a company's knowledge base.
    """
    vector_store = get_or_create_company_vectorstore(company_id=company_id)
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )


def get_retriever(company_id: int = 1):
    """Backward compatibility retriever."""
    return get_company_retriever(company_id=company_id)
