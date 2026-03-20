import os
import chromadb
from app.domain.ports.vector_store_port import VectorStorePort


class ChromaVectorStore(VectorStorePort):
    """
    Implementación del vector store usando ChromaDB persistente.
    Cada organización tiene su propia colección aislada.
    """

    def __init__(self):
        # Ruta absoluta para que funcione independientemente del directorio de ejecución
        base_path = os.path.dirname(os.path.abspath(__file__))
        chroma_path = os.path.join(base_path, "..", "..", "..", "chroma_db")
        self.client = chromadb.PersistentClient(path=chroma_path)

    def index(self, collection: str, chunks: list[str], embeddings: list[list[float]]) -> int:
        """
        Indexa chunks con sus embeddings en la colección de la organización.
        Si la colección ya existe la elimina y reindexa limpio.
        """
        try:
            self.client.delete_collection(collection)
        except Exception:
            pass

        col = self.client.create_collection(
            name=collection,
            # Usamos embeddings propios, no los de ChromaDB
            metadata={"hnsw:space": "cosine"}
        )

        col.add(
            documents=chunks,
            embeddings=embeddings,
            ids=[f"chunk_{i}" for i in range(len(chunks))]
        )

        return len(chunks)

    def search(self, collection: str, query_embedding: list[float], n_results: int = 5) -> list[str]:
        """Busca los chunks más similares al embedding de la consulta."""
        try:
            col = self.client.get_collection(collection)
            results = col.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            return results["documents"][0]
        except Exception:
            return []

    def delete_collection(self, collection: str) -> None:
        """Elimina todos los chunks de una organización."""
        try:
            self.client.delete_collection(collection)
        except Exception:
            pass