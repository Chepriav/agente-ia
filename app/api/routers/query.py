import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.api.dependencies import get_query_use_case

router = APIRouter(prefix="/org", tags=["query"])


def get_anthropic_client():
    """Inicializa el cliente dentro de la función para que .env ya esté cargado."""
    from anthropic import Anthropic
    return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class QueryRequest(BaseModel):
    question: str
    language: str = "es"


SYSTEM_PROMPTS = {
    "es": "Eres un asistente experto. Responde de forma clara y concisa basándote únicamente en el contexto proporcionado.",
    "en": "You are an expert assistant. Answer clearly and concisely based only on the provided context."
}

NO_CONTEXT_MESSAGES = {
    "es": "No encontré información relevante en los documentos para responder esta pregunta.",
    "en": "I could not find relevant information in the documents to answer this question."
}


@router.post("/{org_id}/query")
def query_documents(org_id: str, request: QueryRequest):
    """
    Hace una pregunta sobre los documentos de una organización.
    Soporta español e inglés mediante el parámetro language.
    """
    use_case = get_query_use_case()
    result = use_case.execute(org_id=org_id, query=request.question)

    if result["error"]:
        raise HTTPException(status_code=404, detail=result["error"])

    if not result["context"]:
        return {"answer": NO_CONTEXT_MESSAGES.get(request.language, NO_CONTEXT_MESSAGES["es"])}

    context = "\n\n".join(result["context"])

    prompts = {
        "es": f"""Basándote SOLO en el siguiente contexto, responde la pregunta.
Si la respuesta no está en el contexto, dilo claramente.

CONTEXTO:
{context}

PREGUNTA: {request.question}""",
        "en": f"""Based ONLY on the following context, answer the question.
If the answer is not in the context, say so clearly.

CONTEXT:
{context}

QUESTION: {request.question}"""
    }

    response = get_anthropic_client().messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPTS.get(request.language, SYSTEM_PROMPTS["es"]),
        messages=[{"role": "user", "content": prompts.get(request.language, prompts["es"])}]
    )

    return {
        "answer": response.content[0].text,
        "org_id": org_id,
        "language": request.language,
        "context_chunks_used": len(result["context"])
    }