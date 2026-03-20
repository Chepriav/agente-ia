import uuid
from datetime import datetime
from app.domain.entities.organization import Document, Organization
from app.domain.ports.embedding_port import EmbeddingPort
from app.domain.ports.vector_store_port import VectorStorePort
from app.domain.ports.document_repo_port import DocumentRepoPort


class UploadDocumentUseCase:
    """
    Caso de uso: subir un documento a la base de conocimiento de una organización.
    Orquesta el procesamiento, indexado y persistencia sin saber cómo se implementa cada cosa.
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
        """
        Recibe los chunks ya procesados y los indexa.
        El procesamiento del documento (leer PDF, trocear) es responsabilidad
        de la capa de infraestructura antes de llamar a este caso de uso.
        """
        # Asegurar que la organización existe
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

        # Generar embeddings e indexar en el vector store
        embeddings = self.embeddings.embed_texts(chunks)
        self.vector_store.index(org_id, chunks, embeddings)

        # Persistir el documento
        self.repo.save_document(document)

        return document