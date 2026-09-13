"""
Document Ingestion & Chunking for ResolveAI.
Loads company-specific policy files (.txt, .pdf, .docx) and splits them into semantic chunks.
"""

from pathlib import Path
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def extract_text_from_file(file_path: Path) -> str:
    """
    Extract text from .txt, .pdf, and .docx documents.
    """
    ext = file_path.suffix.lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except Exception:
            return ""

    elif ext == ".docx":
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(str(file_path)) as docx:
                tree = ET.fromstring(docx.read("word/document.xml"))
                paragraphs = []
                for node in tree.iter():
                    if node.tag.endswith("}p"):
                        text = "".join(node.itertext()).strip()
                        if text:
                            paragraphs.append(text)
                return "\n\n".join(paragraphs)
        except Exception:
            return ""

    return ""


def load_company_documents(company_id: int = 1) -> List[Document]:
    """
    Load .txt, .pdf, and .docx documents for a specific company tenant.
    Falls back to base knowledge documents in data/knowledge_base if tenant-specific folder is empty.
    """
    documents = []
    supported_patterns = ["*.txt", "*.pdf", "*.docx"]

    # 1. Check company-specific knowledge directory
    company_kb_dir = Path(f"data/knowledge_base/company_{company_id}")
    if company_kb_dir.exists():
        for pattern in supported_patterns:
            for file_path in company_kb_dir.glob(pattern):
                try:
                    text = extract_text_from_file(file_path)
                    if text.strip():
                        doc = Document(
                            page_content=text,
                            metadata={"company_id": company_id, "source": file_path.name}
                        )
                        documents.append(doc)
                except Exception:
                    pass

    # 2. Check base knowledge base if default company (ID 1)
    if not documents and company_id == 1:
        base_kb_dir = Path("data/knowledge_base")
        if base_kb_dir.exists():
            for pattern in supported_patterns:
                for file_path in base_kb_dir.glob(pattern):
                    try:
                        text = extract_text_from_file(file_path)
                        if text.strip():
                            doc = Document(
                                page_content=text,
                                metadata={"company_id": 1, "source": file_path.name}
                            )
                            documents.append(doc)
                    except Exception:
                        pass

    return documents


def load_documents() -> List[Document]:
    """Backward compatibility loader for default company."""
    return load_company_documents(company_id=1)


def split_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into chunks suitable for semantic vector retrieval.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    return splitter.split_documents(documents)
