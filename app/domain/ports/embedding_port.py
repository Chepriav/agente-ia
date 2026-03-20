from abc import ABC, abstractmethod


class EmbeddingPort(ABC):
    """
    Contrato que cualquier proveedor de embeddings debe cumplir.
    El dominio no sabe si usa Voyage AI, OpenAI o un modelo local.
    Solo sabe que puede pedir embeddings y los recibirá.
    """

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Convierte una lista de textos en vectores numéricos."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Convierte una pregunta en vector para buscar en el índice."""
        pass