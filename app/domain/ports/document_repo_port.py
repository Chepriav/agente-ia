from abc import ABC, abstractmethod
from app.domain.entities.organization import Document, Organization


class DocumentRepoPort(ABC):
    """
    Contrato para persistir y recuperar organizaciones y documentos.
    El dominio no sabe si usa SQLite, PostgreSQL o MongoDB.
    """

    @abstractmethod
    def save_organization(self, org: Organization) -> None:
        """Guarda o actualiza una organización."""
        pass

    @abstractmethod
    def get_organization(self, org_id: str) -> Organization | None:
        """Recupera una organización por su ID."""
        pass

    @abstractmethod
    def save_document(self, document: Document) -> None:
        """Guarda un documento asociado a una organización."""
        pass

    @abstractmethod
    def get_documents(self, org_id: str) -> list[Document]:
        """Devuelve todos los documentos de una organización."""
        pass