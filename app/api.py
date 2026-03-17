import os
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
from app.rag.processor import process_document
from app.rag.embeddings import index_chunks
from app.rag.retrieval import hybrid_search

load_dotenv()

app = FastAPI()
client = Anthropic()

SYSTEM_PROMPT = """Eres un asistente experto en tecnología.
Respondes de forma clara, concisa y práctica."""

historial = []
chunks_cache = {}


class Message(BaseModel):
    text: str
    collection: str = "default"


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/debug")
def debug():
    from app.rag.embeddings import get_chroma_client
    client_chroma = get_chroma_client()
    collections = client_chroma.list_collections()
    return {
        "collections": [c.name for c in collections],
        "cache_keys": list(chunks_cache.keys())
    }


@app.post("/chat")
def chat(mensaje: Message):
    """Conversación general sin contexto de documentos."""
    historial.append({"role": "user", "content": mensaje.text})
    respuesta = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=historial
    )
    mensaje_agente = respuesta.content[0].text
    historial.append({"role": "assistant", "content": mensaje_agente})
    return {"response": mensaje_agente}


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("default")
):
    """
    Recibe un PDF o Word, lo procesa y lo indexa en ChromaDB.
    Este es el endpoint que usará el cliente para subir sus documentos.
    """
    path = f"documents/{file.filename}"
    os.makedirs("documents", exist_ok=True)

    with open(path, "wb") as f:
        f.write(await file.read())

    resultado = process_document(path)
    index_chunks(resultado["chunks"], collection)
    chunks_cache[collection] = resultado["chunks"]

    return {
        "message": "Documento indexado correctamente",
        "type": resultado["type"],
        "total_chunks": resultado["total_chunks"],
        "collection": collection
    }


@app.post("/rag")
def rag(mensaje: Message):
    """
    Responde preguntas usando los documentos indexados.
    """
    print(f"Cache keys: {list(chunks_cache.keys())}")
    print(f"Buscando colección: {mensaje.collection}")

    if mensaje.collection not in chunks_cache:
        return {"response": "No hay documentos indexados en esta colección.", "collection": mensaje.collection}

    chunks = chunks_cache[mensaje.collection]
    resultados = hybrid_search(mensaje.text, mensaje.collection, chunks)
    contexto = "\n\n".join(resultados)

    respuesta = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Basándote SOLO en el siguiente contexto, responde la pregunta.
Si la respuesta no está en el contexto, dilo claramente.

CONTEXTO:
{contexto}

PREGUNTA: {mensaje.text}"""
        }]
    )
    return {"response": respuesta.content[0].text}