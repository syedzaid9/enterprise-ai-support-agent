"""
Knowledge Base Management Service for ResolveAI.
Handles admin document uploads (.txt, .pdf, .docx), text extraction, indexing, vector storage, and tenant isolation.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from app.db.database import get_db
from app.db.models import KnowledgeDocument, AuditLog
from app.rag.ingestion import extract_text_from_file
from app.rag.vectorstore import get_or_create_company_vectorstore, add_documents_to_company_store


def save_and_index_document(
    company_id: int,
    filename: str,
    content: Union[str, bytes],
    uploaded_by_user_id: Optional[int] = None,
    doc_type: str = "policy",
) -> Dict[str, Any]:
    """
    Save an uploaded knowledge document (.txt, .pdf, .docx) to storage,
    extract text, chunk & index into tenant vectorstore, and persist metadata in PostgreSQL.
    """
    company_kb_dir = Path(f"data/knowledge_base/company_{company_id}")
    company_kb_dir.mkdir(parents=True, exist_ok=True)
    file_path = company_kb_dir / filename

    # 1. Save file to disk
    if isinstance(content, bytes):
        with open(file_path, "wb") as f:
            f.write(content)
        extracted_text = extract_text_from_file(file_path)
    else:
        with open(file_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(content)
        extracted_text = content

    if not extracted_text.strip():
        raise ValueError(f"Could not extract readable text from document '{filename}'.")

    # 2. Split and Index into Company Vector Store
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    raw_doc = Document(page_content=extracted_text, metadata={"source": filename, "company_id": company_id})
    chunks = splitter.split_documents([raw_doc])

    add_documents_to_company_store(company_id=company_id, documents=chunks)

    # 3. Save to PostgreSQL
    with get_db() as db:
        existing = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.company_id == company_id, KnowledgeDocument.filename == filename)
            .first()
        )
        if existing:
            existing.chunk_count = len(chunks)
            existing.status = "active"
            doc_record = existing
        else:
            doc_record = KnowledgeDocument(
                company_id=company_id,
                filename=filename,
                doc_type=doc_type,
                uploaded_by=uploaded_by_user_id,
                status="active",
                chunk_count=len(chunks),
            )
            db.add(doc_record)
        db.flush()

        audit = AuditLog(
            company_id=company_id,
            user_id=uploaded_by_user_id,
            actor_type="admin",
            action="KNOWLEDGE_DOC_UPLOADED",
            target_type="knowledge",
            target_id=filename,
            details=f"Uploaded and indexed '{filename}' ({len(chunks)} chunks, format: {file_path.suffix})",
            status="SUCCESS",
        )
        db.add(audit)
        db.flush()

        return {
            "id": doc_record.id,
            "filename": doc_record.filename,
            "chunk_count": doc_record.chunk_count,
            "status": doc_record.status,
        }


def list_knowledge_documents(company_id: int) -> List[Dict[str, Any]]:
    """
    List all knowledge documents for a company.
    """
    with get_db() as db:
        docs = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.company_id == company_id)
            .order_by(KnowledgeDocument.created_at.desc())
            .all()
        )
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "doc_type": d.doc_type,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at.strftime("%d %b %Y, %I:%M %p") if d.created_at else "N/A",
            }
            for d in docs
        ]


def delete_knowledge_document(company_id: int, doc_id: int, admin_user_id: Optional[int] = None) -> bool:
    """
    Delete a knowledge document from database and storage.
    """
    with get_db() as db:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id, KnowledgeDocument.company_id == company_id).first()
        if not doc:
            return False

        filename = doc.filename
        db.delete(doc)
        db.flush()

        # Delete file if exists
        company_kb_dir = Path(f"data/knowledge_base/company_{company_id}")
        file_path = company_kb_dir / filename
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception:
                pass

        audit = AuditLog(
            company_id=company_id,
            user_id=admin_user_id,
            actor_type="admin",
            action="KNOWLEDGE_DOC_DELETED",
            target_type="knowledge",
            target_id=filename,
            details=f"Deleted knowledge document '{filename}'",
            status="SUCCESS",
        )
        db.add(audit)
        db.flush()
        return True
