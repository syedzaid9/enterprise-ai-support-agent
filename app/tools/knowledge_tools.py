"""
Knowledge retrieval tools for ResolveAI agent.
"""

from typing import Optional
from langchain_core.tools import tool
from app.rag.retriever import get_company_retriever


@tool
def search_company_policy(query: str, company_id: Optional[int] = 1) -> str:
    """
    Search the company knowledge base for official policies, FAQs, and support guidelines.
    Use this tool when answering questions about refunds, cancellations, shipping, warranties, or billing policies.
    """
    try:
        cid = int(company_id) if company_id else 1
        retriever = get_company_retriever(company_id=cid)
        documents = retriever.invoke(query)

        if not documents:
            return "No relevant information found in the official company policies."

        results = []
        for document in documents:
            source = document.metadata.get("source", "knowledge_base")
            results.append(
                f"Source: {source}\n"
                f"Content: {document.page_content}"
            )
        return "\n\n".join(results)

    except Exception as e:
        return f"Error searching company policies: {str(e)}"