import json
import sys
import os
import time

# Añadir el directorio raíz al path para poder importar app/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.processor import process_document
from app.rag.embeddings import index_chunks
from app.rag.retrieval import hybrid_search
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()


def ask_rag(question: str, chunks: list[str], collection: str) -> tuple[str, str]:
    """
    Hace una pregunta al pipeline RAG.
    Devuelve la respuesta y el contexto usado, los dos juntos para evaluar.
    """
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
    return response.content[0].text, context


def evaluate_faithfulness(answer: str, context: str) -> float:
    """
    Evalúa del 0 al 10 si la respuesta está fundamentada en el contexto.
    0 = inventado completamente, 10 = todo viene del contexto.
    """
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"""Evalúa del 0 al 10 si la respuesta está fundamentada en el contexto.
0 = la respuesta inventa información que no está en el contexto.
10 = toda la información de la respuesta viene directamente del contexto.

Responde SOLO con un número del 0 al 10, sin explicación.

CONTEXTO: {context[:600]}

RESPUESTA: {answer[:400]}

PUNTUACIÓN:"""
        }]
    )
    try:
        score = float(response.content[0].text.strip().split()[0])
        return min(max(score / 10.0, 0.0), 1.0)
    except Exception:
        return 0.0


def evaluate_relevancy(question: str, answer: str) -> float:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"""Evalúa del 0 al 10 si la respuesta responde directamente la pregunta.
0 = no responde la pregunta en absoluto.
10 = responde la pregunta de forma directa y completa.

Responde SOLO con un número del 0 al 10, sin explicación.

PREGUNTA: {question}

RESPUESTA: {answer[:400]}

PUNTUACIÓN:"""
        }]
    )
    raw = response.content[0].text.strip()
    try:
        score = float(raw.split()[0])
        return min(max(score / 10.0, 0.0), 1.0)
    except Exception as e:
        print(f"  Parse error: {e}")
        return 0.0

def run_evaluation(document_path: str, questions_path: str):
    print(f"Usando documento: {document_path}")
    print(f"Usando preguntas: {questions_path}")
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

        # Reintentar si la API está saturada
        for attempt in range(3):
            try:
                answer, context = ask_rag(question, chunks, "eval_collection")
                faith = evaluate_faithfulness(answer, context)
                relev = evaluate_relevancy(question, answer)
                break
            except Exception as e:
                if attempt < 2:
                    print(f"  API saturada, reintentando en 10s...")
                    time.sleep(10)
                else:
                    print(f"  Error después de 3 intentos: {e}")
                    faith, relev = 0.0, 0.0

        faithfulness_scores.append(faith)
        relevancy_scores.append(relev)
        print(f"  Faithfulness: {faith:.2f} | Relevancy: {relev:.2f}")

        # Pausa entre preguntas para no saturar la API
        time.sleep(2)

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
        if avg_faith < 0.80:
            print("   → Faithfulness baja: el modelo está inventando, revisar contexto")
        if avg_relev < 0.75:
            print("   → Relevancy baja: el retrieval no encuentra la información correcta")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        run_evaluation(sys.argv[1], sys.argv[2])
    else:
        run_evaluation("documento.pdf", "tests/test_questions.json")