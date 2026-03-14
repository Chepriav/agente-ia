from fastapi import FastAPI
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
import os

load_dotenv()

app = FastAPI()
client = Anthropic()

SYSTEM_PROMPT = """Eres un asistente experto en tecnología.
Respondes de forma clara, concisa y práctica."""

historial = []

# --- RAG setup ---
def leer_pdf(ruta):
    reader = PdfReader(ruta)
    texto = ""
    for pagina in reader.pages:
        texto += pagina.extract_text()
    return texto

def inicializar_rag():
    if not os.path.exists("documento.pdf"):
        print("⚠️ No se encontró documento.pdf, RAG desactivado")
        return None
    texto = leer_pdf("documento.pdf")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    trozos = splitter.split_text(texto)
    cliente_chroma = chromadb.Client()
    coleccion = cliente_chroma.create_collection("documentos")
    coleccion.add(
        documents=trozos,
        ids=[f"trozo_{i}" for i in range(len(trozos))]
    )
    print(f"✅ RAG inicializado con {len(trozos)} fragmentos")
    return coleccion

coleccion = inicializar_rag()

# --- Modelos ---
class Mensaje(BaseModel):
    texto: str

# --- Endpoints ---
@app.get("/")
def root():
    return {"estado": "funcionando"}

@app.post("/chat")
def chat(mensaje: Mensaje):
    historial.append({"role": "user", "content": mensaje.texto})
    respuesta = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=historial
    )
    mensaje_agente = respuesta.content[0].text
    historial.append({"role": "assistant", "content": mensaje_agente})
    return {"respuesta": mensaje_agente}

@app.post("/rag")
def rag(mensaje: Mensaje):
    if coleccion is None:
        return {"respuesta": "RAG no disponible: no hay documento cargado en el servidor."}
    resultados = coleccion.query(
        query_texts=[mensaje.texto],
        n_results=3
    )
    contexto = "\n\n".join(resultados["documents"][0])
    respuesta = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Basándote SOLO en el siguiente contexto, responde la pregunta.
Si la respuesta no está en el contexto, dilo claramente.

CONTEXTO:
{contexto}

PREGUNTA: {mensaje.texto}"""
        }]
    )
    return {"respuesta": respuesta.content[0].text}