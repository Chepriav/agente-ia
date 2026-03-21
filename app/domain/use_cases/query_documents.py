from app.domain.ports.embedding_port import EmbeddingPort
from app.domain.ports.vector_store_port import VectorStorePort
from app.domain.ports.document_repo_port import DocumentRepoPort
from app.domain.utils import normalize_org_id


class QueryDocumentsUseCase:
    """
    Caso de uso: hacer una pregunta sobre los documentos de una organización.
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

    def execute(self, org_id: str, query: str, n_results: int = 5) -> dict:
        # Normalizar para buscar en ChromaDB con el mismo ID que se usó al indexar
        clean_org_id = normalize_org_id(org_id)

        # Verificar que la organización existe y tiene documentos
        org = self.repo.get_organization(org_id)
        if org is None:
            return {"context": [], "error": "Organization not found"}

        documents = self.repo.get_documents(org_id)
        if not documents:
            return {"context": [], "error": "No documents indexed for this organization"}

        # Buscar chunks relevantes
        query_embedding = self.embeddings.embed_query(query)
        chunks = self.vector_store.search(clean_org_id, query_embedding, n_results)

        return {
            "context": chunks,
            "org_id": org_id,
            "total_documents": len(documents),
            "error": None
        }