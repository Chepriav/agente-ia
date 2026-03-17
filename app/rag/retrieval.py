from rank_bm25 import BM25Okapi
from app.rag.embeddings import search as semantic_search, get_chroma_client
import numpy as np


def bm25_search(query: str, chunks: list[str], n_results: int = 5) -> list[str]:
    """
    Búsqueda por términos exactos con BM25.
    Útil para códigos internos, referencias, siglas y nombres propios
    que la búsqueda semántica no captura bien.
    """
    # Tokenización simple: lowercase y split por espacios
    tokenized_corpus = [chunk.lower().split() for chunk in chunks]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Devolver los índices con mayor puntuación
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
    Combina búsqueda semántica y BM25.
    alpha controla el balance:
      - alpha=1.0 → solo semántico
      - alpha=0.0 → solo BM25
      - alpha=0.5 → equilibrio (valor por defecto)
    Para corpus con mucha terminología técnica exacta, bajar alpha a 0.3.
    Para corpus conceptual y narrativo, subir alpha a 0.7.
    """
    # Búsqueda semántica
    semantic_results = semantic_search(query, collection_name, n_results * 2)

    # Búsqueda BM25
    bm25_results = bm25_search(query, chunks, n_results * 2)

    # Combinar eliminando duplicados, priorizando según alpha
    seen = set()
    combined = []

    # Los resultados semánticos tienen peso alpha
    for chunk in semantic_results:
        if chunk not in seen:
            seen.add(chunk)
            combined.append((chunk, alpha))

    # Los resultados BM25 tienen peso (1 - alpha)
    for chunk in bm25_results:
        if chunk not in seen:
            seen.add(chunk)
            combined.append((chunk, 1 - alpha))
        else:
            # Si ya existe, aumentar su puntuación combinada
            for i, (c, score) in enumerate(combined):
                if c == chunk:
                    combined[i] = (c, score + (1 - alpha))
                    break

    # Ordenar por puntuación combinada y devolver los mejores
    combined.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in combined[:n_results]]