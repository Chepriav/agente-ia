import uuid
from app.domain.entities.organization import Document, Organization
from app.domain.ports.embedding_port import EmbeddingPort
from app.domain.ports.vector_store_port import VectorStorePort
from app.domain.ports.document_repo_port import DocumentRepoPort
from app.domain.utils import normalize_org_id


class UploadDocumentUseCase:
    """
    Caso de uso: subir un documento a la base de conocimiento de una organización.
    Orquesta el procesamiento, indexado y persistencia.
    """

    def __init__(
        self,
        embedding_port: EmbeddingPort,
        vector_store_port: VectorStorePort,
        document_repo_port: DocumentRepoPort,
    ):
        self.embeddings = embedding_port
        self.vector_store = vector_store_port
        self.repo = document_repo_port

    def execute(self, org_id: str, filename: str, chunks: list[str]) -> Document:
        # Normalizar para ChromaDB — sin espacios, acentos ni mayúsculas
        clean_org_id = normalize_org_id(org_id)

        # Asegurar que la organización existe en SQLite con el ID original
        org = self.repo.get_organization(org_id)
        if org is None:
            org = Organization(id=org_id, name=org_id)
            self.repo.save_organization(org)

        # Crear el documento
        document = Document(
            id=str(uuid.uuid4()),
            filename=filename,
            organization_id=org_id,
            total_chunks=len(chunks),
        )

        # Indexar en ChromaDB con el ID normalizado
        embeddings = self.embeddings.embed_texts(chunks)
        self.vector_store.index(clean_org_id, chunks, embeddings)

        # Persistir metadatos en SQLite
        self.repo.save_document(document)

        return document