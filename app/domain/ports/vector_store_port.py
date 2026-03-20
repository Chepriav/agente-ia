from abc import ABC, abstractmethod


class VectorStorePort(ABC):
    """
    Contrato para cualquier base de datos vectorial.
    El dominio no sabe si usa ChromaDB, Pinecone o Weaviate.
    """

    @abstractmethod
    def index(self, collection: str, chunks: list[str], embeddings: list[list[float]]) -> int:
        """Indexa chunks con sus embeddings. Devuelve el número indexado."""
        pass

    @abstractmethod
    def search(self, collection: str, query_embedding: list[float], n_results: int = 5) -> list[str]:
        """Busca los chunks más similares al embedding de la consulta."""
        pass

    @abstractmethod
    def delete_collection(self, collection: str) -> None:
        """Elimina todos los chunks de una colección."""
        pass