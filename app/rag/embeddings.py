from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import os

# Modelo multilingüe optimizado para texto técnico en español e inglés.
# Ventaja clave: corre en tu servidor, los documentos del cliente nunca
# salen a ninguna API externa.
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

def get_embedding_model():
    """
    Carga el modelo de embeddings.
    La primera vez descarga el modelo (~400MB), luego lo cachea localmente.
    """
    return SentenceTransformer(MODEL_NAME)


# Ruta absoluta para que funcione independientemente de desde dónde se ejecute
CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "chroma_db")

_chroma_client = None

def get_chroma_client():
    """Devuelve siempre la misma instancia del cliente ChromaDB."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client


def index_chunks(chunks: list[str], collection_name: str) -> int:
    """
    Convierte los chunks en vectores y los guarda en ChromaDB.
    Cada colección es un cliente o documento indexado por separado.
    Devuelve el número de chunks indexados.
    """
    model = get_embedding_model()
    client = get_chroma_client()

    # Si ya existe la colección la eliminamos para reindexar limpio
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(collection_name)

    # Generamos los embeddings en lotes para no saturar la memoria
    embeddings = model.encode(chunks, show_progress_bar=True).tolist()

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

    return len(chunks)


def search(query: str, collection_name: str, n_results: int = 5) -> list[str]:
    """
    Busca los chunks más relevantes para una pregunta.
    Convierte la pregunta en vector y busca los más similares en ChromaDB.
    """
    model = get_embedding_model()
    client = get_chroma_client()

    collection = client.get_collection(collection_name)
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )

    return results["documents"][0]