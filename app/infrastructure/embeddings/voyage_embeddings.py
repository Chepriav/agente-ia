import voyageai
import os
from app.domain.ports.embedding_port import EmbeddingPort


class VoyageEmbeddings(EmbeddingPort):
    """
    Implementación de embeddings usando Voyage AI.
    Ventajas para producción:
    - Cero peso en el servidor (llamada HTTP)
    - Modelo multilingüe de alta calidad
    - 50M tokens/mes gratuitos
    """

    def __init__(self):
        self.client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
        # voyage-3-lite es el modelo más eficiente para documentos empresariales
        self.model = "voyage-3-lite"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Genera embeddings para una lista de textos.
        Voyage AI acepta hasta 128 textos por llamada.
        """
        # Procesamos en lotes de 128 para respetar el límite de la API
        all_embeddings = []
        batch_size = 128

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            result = self.client.embed(batch, model=self.model, input_type="document")
            all_embeddings.extend(result.embeddings)

        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        """
        Genera embedding para una consulta.
        Usa input_type='query' que Voyage AI optimiza diferente a los documentos.
        """
        result = self.client.embed([query], model=self.model, input_type="query")
        return result.embeddings[0]