import sqlite3
import os
import json
from datetime import datetime
from app.domain.entities.organization import Document, Organization
from app.domain.ports.document_repo_port import DocumentRepoPort


class SQLiteDocumentRepo(DocumentRepoPort):
    """
    Persistencia de organizaciones y documentos usando SQLite.
    SQLite es perfecto para este caso: sin servidor, sin configuración,
    el archivo vive junto al proyecto y escala hasta miles de documentos.
    Cuando el negocio crezca, migrar a PostgreSQL es cambiar solo este archivo.
    """

    def __init__(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_path, "..", "..", "..", "data", "antropia.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Crea las tablas si no existen."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    total_chunks INTEGER NOT NULL,
                    doc_type TEXT NOT NULL,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                )
            """)
            conn.commit()

    def save_organization(self, org: Organization) -> None:
        """Guarda o actualiza una organización."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO organizations (id, name, created_at)
                VALUES (?, ?, ?)
            """, (org.id, org.name, org.created_at.isoformat()))
            conn.commit()

    def get_organization(self, org_id: str) -> Organization | None:
        """Recupera una organización por su ID."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, name, created_at FROM organizations WHERE id = ?",
                (org_id,)
            ).fetchone()

        if row is None:
            return None

        return Organization(
            id=row[0],
            name=row[1],
            created_at=datetime.fromisoformat(row[2])
        )

    def save_document(self, document: Document) -> None:
        """Guarda un documento asociado a una organización."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents
                (id, filename, organization_id, uploaded_at, total_chunks, doc_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                document.id,
                document.filename,
                document.organization_id,
                document.uploaded_at.isoformat(),
                document.total_chunks,
                document.doc_type
            ))
            conn.commit()

    def get_documents(self, org_id: str) -> list[Document]:
        """Devuelve todos los documentos de una organización."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, filename, organization_id, uploaded_at, total_chunks, doc_type FROM documents WHERE organization_id = ?",
                (org_id,)
            ).fetchall()

        return [
            Document(
                id=row[0],
                filename=row[1],
                organization_id=row[2],
                uploaded_at=datetime.fromisoformat(row[3]),
                total_chunks=row[4],
                doc_type=row[5]
            )
            for row in rows
        ]
        