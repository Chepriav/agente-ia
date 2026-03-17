import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
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

# --- Frontend ---
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/ui")
def ui():
    """Sirve la interfaz web del producto."""
    return FileResponse("app/static/index.html")


# --- API ---
class Message(BaseModel):
    text: str
    collection: str = "default"


@app.get("/")
def root():
    """Redirige la raíz a la interfaz web."""
    return RedirectResponse(url="/ui")


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
    Usa hybrid search para encontrar los chunks más relevantes.
    """
    if mensaje.collection not in chunks_cache:
        return {"response": "No hay documentos indexados en esta colección."}

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