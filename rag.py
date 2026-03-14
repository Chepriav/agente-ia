import os
from anthropic import Anthropic
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

load_dotenv()

# 1. LEER EL PDF
def leer_pdf(ruta):
    reader = PdfReader(ruta)
    texto = ""
    for pagina in reader.pages:
        texto += pagina.extract_text()
    print(f"✅ PDF leído: {len(texto)} caracteres")
    return texto

# 2. TROCEAR EL TEXTO
def trocear_texto(texto):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    trozos = splitter.split_text(texto)
    print(f"✅ Texto troceado: {len(trozos)} fragmentos")
    return trozos

# 3. GUARDAR EN CHROMADB
def crear_base_conocimiento(trozos):
    cliente = chromadb.Client()
    coleccion = cliente.create_collection("documentos")
    
    coleccion.add(
        documents=trozos,
        ids=[f"trozo_{i}" for i in range(len(trozos))]
    )
    print(f"✅ Base de conocimiento creada")
    return coleccion

# 4. BUSCAR FRAGMENTOS RELEVANTES
def buscar(coleccion, pregunta, n=3):
    resultados = coleccion.query(
        query_texts=[pregunta],
        n_results=n
    )
    return resultados["documents"][0]

# 5. PREGUNTAR A CLAUDE
def preguntar(coleccion, pregunta):
    client = Anthropic()
    fragmentos = buscar(coleccion, pregunta)
    contexto = "\n\n".join(fragmentos)

    respuesta = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Basándote SOLO en el siguiente contexto, responde la pregunta.
Si la respuesta no está en el contexto, dilo claramente.

CONTEXTO:
{contexto}

PREGUNTA: {pregunta}"""
        }]
    )
    return respuesta.content[0].text

# MAIN
print("📚 Cargando documento...")
texto = leer_pdf("documento.pdf")
trozos = trocear_texto(texto)
coleccion = crear_base_conocimiento(trozos)

print("\n🤖 Agente RAG listo. Escribe 'salir' para terminar.\n")

while True:
    pregunta = input("Tú: ")
    if pregunta.lower() == "salir":
        break
    respuesta = preguntar(coleccion, pregunta)
    print(f"\nAgente: {respuesta}\n")