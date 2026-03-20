import os
from functools import lru_cache
from app.domain.use_cases.upload_document import UploadDocumentUseCase
from app.domain.use_cases.query_documents import QueryDocumentsUseCase
from app.infrastructure.vector_store.chroma_store import ChromaVectorStore
from app.infrastructure.repositories.sqlite_document_repo import SQLiteDocumentRepo


def get_embedding_provider():
    """
    Selecciona el proveedor de embeddings según la variable de entorno.
    EMBEDDINGS_PROVIDER=voyage → Voyage AI (producción)
    EMBEDDINGS_PROVIDER=local  → sentence-transformers (desarrollo)
    """
    provider = os.getenv("EMBEDDINGS_PROVIDER", "voyage")

    if provider == "voyage":
        from app.infrastructure.embeddings.voyage_embeddings import VoyageEmbeddings
        return VoyageEmbeddings()
    else:
        from app.infrastructure.embeddings.local_embeddings import LocalEmbeddings
        return LocalEmbeddings()


@lru_cache()
def get_vector_store():
    return ChromaVectorStore()


@lru_cache()
def get_document_repo():
    return SQLiteDocumentRepo()


def get_upload_use_case() -> UploadDocumentUseCase:
    return UploadDocumentUseCase(
        embedding_port=get_embedding_provider(),
        vector_store_port=get_vector_store(),
        document_repo_port=get_document_repo()
    )


def get_query_use_case() -> QueryDocumentsUseCase:
    return QueryDocumentsUseCase(
        embedding_port=get_embedding_provider(),
        vector_store_port=get_vector_store(),
        document_repo_port=get_document_repo()
    )