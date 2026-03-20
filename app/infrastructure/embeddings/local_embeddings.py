import os
from app.domain.ports.embedding_port import EmbeddingPort


class LocalEmbeddings(EmbeddingPort):
    """
    Implementación local usando sentence-transformers.
    Solo para desarrollo en Mac — no usar en producción por el peso de PyTorch.
    """

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, show_progress_bar=True).tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.model.encode([query]).tolist()[0]
