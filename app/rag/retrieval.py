from rank_bm25 import BM25Okapi
from app.rag.embeddings import search as semantic_search
from sentence_transformers import CrossEncoder
import numpy as np

# Modelo de reranking open-source que corre en tu servidor.
# Más lento que los embeddings pero más preciso para ordenar resultados.
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker = None


def get_reranker():
    """Carga el modelo de reranking una sola vez y lo reutiliza."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker


def bm25_search(query: str, chunks: list[str], n_results: int = 5) -> list[str]:
    """
    Búsqueda por términos exactos con BM25.
    Útil para códigos internos, referencias, siglas y nombres propios
    que la búsqueda semántica no captura bien.
    """
    tokenized_corpus = [chunk.lower().split() for chunk in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(query.lower().split())
    top_indices = np.argsort(scores)[::-1][:n_results]
    return [chunks[i] for i in top_indices if scores[i] > 0]


def hybrid_search(
    query: str,
    collection_name: str,
    chunks: list[str],
    n_results: int = 5,
    alpha: float = 0.5
) -> list[str]:
    """
    Combina búsqueda semántica y BM25, luego aplica reranking.
    El reranking reordena los candidatos con un modelo más preciso
    para que el contexto que llega al LLM sea el más relevante posible.
    """
    # Paso 1: obtener candidatos con búsqueda híbrida (más de los que necesitamos)
    semantic_results = semantic_search(query, collection_name, n_results * 2)
    bm25_results = bm25_search(query, chunks, n_results * 2)

    # Paso 2: combinar eliminando duplicados
    seen = set()
    candidates = []

    for chunk in semantic_results:
        if chunk not in seen:
            seen.add(chunk)
            candidates.append((chunk, alpha))

    for chunk in bm25_results:
        if chunk not in seen:
            seen.add(chunk)
            candidates.append((chunk, 1 - alpha))
        else:
            for i, (c, score) in enumerate(candidates):
                if c == chunk:
                    candidates[i] = (c, score + (1 - alpha))
                    break

    # Ordenar candidatos por puntuación combinada
    candidates.sort(key=lambda x: x[1], reverse=True)
    candidate_chunks = [chunk for chunk, _ in candidates[:n_results * 2]]

    if not candidate_chunks:
        return []

    # Paso 3: reranking con cross-encoder
    # El cross-encoder evalúa cada par (pregunta, chunk) juntos,
    # lo que da una puntuación de relevancia mucho más precisa
    reranker = get_reranker()
    pairs = [(query, chunk) for chunk in candidate_chunks]
    scores = reranker.predict(pairs)

    # Ordenar por puntuación del reranker y devolver los mejores
    ranked = sorted(zip(candidate_chunks, scores), key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in ranked[:n_results]]