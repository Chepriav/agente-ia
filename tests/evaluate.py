import json
import sys
import os

# Añadir el directorio raíz al path para poder importar app/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.processor import process_document
from app.rag.embeddings import index_chunks
from app.rag.retrieval import hybrid_search
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()


def ask_rag(question: str, chunks: list[str], collection: str) -> str:
    """Hace una pregunta al pipeline RAG y devuelve la respuesta."""
    results = hybrid_search(question, collection, chunks)
    context = "\n\n".join(results)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"""Basándote SOLO en el siguiente contexto, responde la pregunta.
Si la respuesta no está en el contexto, di exactamente: "NO ENCONTRADO"

CONTEXTO:
{context}

PREGUNTA: {question}"""
        }]
    )
    return response.content[0].text


def evaluate_faithfulness(answer: str, context: str) -> float:
    """
    Evalúa si la respuesta está fundamentada en el contexto.
    Pregunta a Claude si la respuesta se puede deducir del contexto.
    Devuelve 1.0 si es fiel, 0.0 si no lo es.
    """
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": f"""¿La siguiente respuesta está completamente fundamentada en el contexto dado?
Responde SOLO con "SI" o "NO".

CONTEXTO: {context[:500]}

RESPUESTA: {answer[:300]}"""
        }]
    )
    return 1.0 if "SI" in response.content[0].text.upper() else 0.0


def evaluate_relevancy(question: str, answer: str) -> float:
    """
    Evalúa si la respuesta responde realmente la pregunta.
    Devuelve 1.0 si es relevante, 0.0 si no lo es.
    """
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": f"""¿La siguiente respuesta responde directamente la pregunta?
Responde SOLO con "SI" o "NO".

PREGUNTA: {question}

RESPUESTA: {answer[:300]}"""
        }]
    )
    return 1.0 if "SI" in response.content[0].text.upper() else 0.0


def run_evaluation(document_path: str, questions_path: str):
    """
    Ejecuta la evaluación completa del pipeline RAG.
    Mide faithfulness y answer relevancy sobre el conjunto de test.
    """
    print("Cargando documento...")
    result = process_document(document_path)
    index_chunks(result["chunks"], "eval_collection")
    chunks = result["chunks"]
    print(f"Documento procesado: {result['total_chunks']} chunks\n")

    with open(questions_path) as f:
        questions = json.load(f)

    faithfulness_scores = []
    relevancy_scores = []

    for i, item in enumerate(questions):
        question = item["question"]
        print(f"[{i+1}/{len(questions)}] {question}")

        # Obtener respuesta del RAG
        answer = ask_rag(question, chunks, "eval_collection")

        # Obtener contexto usado
        context_chunks = hybrid_search(question, "eval_collection", chunks)
        context = "\n\n".join(context_chunks)

        # Evaluar métricas
        faith = evaluate_faithfulness(answer, context)
        relev = evaluate_relevancy(question, answer)

        faithfulness_scores.append(faith)
        relevancy_scores.append(relev)

        print(f"  Faithfulness: {faith} | Relevancy: {relev}")

    # Resultados finales
    avg_faith = sum(faithfulness_scores) / len(faithfulness_scores)
    avg_relev = sum(relevancy_scores) / len(relevancy_scores)

    print(f"\n{'='*40}")
    print(f"RESULTADOS FINALES")
    print(f"{'='*40}")
    print(f"Faithfulness:     {avg_faith:.2f} (objetivo: > 0.80)")
    print(f"Answer Relevancy: {avg_relev:.2f} (objetivo: > 0.75)")

    if avg_faith >= 0.80 and avg_relev >= 0.75:
        print("\n✅ Pipeline aprobado - listo para producción")
    else:
        print("\n❌ Pipeline suspendido - revisar chunking o embeddings")


if __name__ == "__main__":
    run_evaluation("documento.pdf", "tests/test_questions.json")