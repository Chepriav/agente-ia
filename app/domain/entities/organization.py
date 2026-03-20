from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Document:
    """Representa un documento subido por una organización."""
    id: str
    filename: str
    organization_id: str
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    total_chunks: int = 0
    doc_type: str = "unknown"


@dataclass
class Organization:
    """Representa una organización cliente con su base de conocimiento."""
    id: str
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    documents: list[Document] = field(default_factory=list)