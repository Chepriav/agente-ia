from pypdf import PdfReader
from docx import Document
import re

def detectar_tipo_documento(texto: str) -> str:
    """
    Analiza el texto y decide qué estrategia de chunking usar.
    Devuelve: 'estructurado' o 'no_estructurado'
    """
    lineas = texto.split('\n')
    lineas_no_vacias = [l for l in lineas if l.strip()]
    
    # Busca patrones típicos de documentos estructurados
    patrones_titulo = 0
    for linea in lineas_no_vacias[:100]:  # analiza las primeras 100 líneas
        linea = linea.strip()
        # Línea corta en mayúsculas o numerada = probable título
        if re.match(r'^(\d+\.|\d+\))', linea):  # "1. Introducción"
            patrones_titulo += 1
        elif re.match(r'^(Chapter|Capítulo|Sección|Section)\s', linea, re.I):
            patrones_titulo += 1
        elif len(linea) < 60 and linea.isupper():  # "INTRODUCCIÓN"
            patrones_titulo += 1

    ratio = patrones_titulo / max(len(lineas_no_vacias[:100]), 1)
    
    if ratio > 0.05:  # más del 5% de líneas son títulos
        return 'estructurado'
    return 'no_estructurado'


def leer_pdf(ruta: str) -> str:
    reader = PdfReader(ruta)
    texto = ""
    for pagina in reader.pages:
        texto += pagina.extract_text() + "\n"
    return texto


def leer_word(ruta: str) -> str:
    doc = Document(ruta)
    texto = ""
    for parrafo in doc.paragraphs:
        texto += parrafo.text + "\n"
    return texto


def leer_documento(ruta: str) -> str:
    if ruta.endswith('.pdf'):
        return leer_pdf(ruta)
    elif ruta.endswith('.docx'):
        return leer_word(ruta)
    else:
        raise ValueError(f"Formato no soportado: {ruta}")