from pypdf import PdfReader
from docx import Document
import re


def read_document(path: str) -> str:
    """Lee un PDF o Word y devuelve el texto completo como string."""
    if path.endswith('.pdf'):
        reader = PdfReader(path)
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    elif path.endswith('.docx'):
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"Formato no soportado: {path}")


def detect_document_type(text: str) -> str:
    """
    Analiza las primeras 100 líneas del documento y decide
    si tiene estructura clara (títulos, secciones numeradas)
    o es texto libre sin jerarquía.
    Devuelve: 'structured' o 'unstructured'
    """
    lines = [l for l in text.split('\n') if l.strip()][:100]
    matches = 0

    for line in lines:
        line = line.strip()
        # Líneas numeradas tipo "1. Introducción" o "1) Objetivo"
        if re.match(r'^(\d+\.|\d+\))\s', line):
            matches += 1
        # Palabras clave de sección en inglés o español
        elif re.match(r'^(Chapter|Capítulo|Sección|Section)\s', line, re.I):
            matches += 1
        # Línea corta completamente en mayúsculas = probable título
        elif len(line) < 60 and line.isupper():
            matches += 1

    ratio = matches / max(len(lines), 1)
    return 'structured' if ratio > 0.05 else 'unstructured'


def chunk_by_sections(text: str) -> list[str]:
    """
    Para documentos estructurados.
    Usa los títulos como separadores y devuelve cada sección
    como un chunk completo con su contexto intacto.
    """
    title_pattern = re.compile(
        r'^(\d+\.|\d+\)|Chapter|Capítulo|Sección|Section|\b[A-Z][A-Z\s]{3,}\b)',
        re.MULTILINE | re.IGNORECASE
    )
    positions = [m.start() for m in title_pattern.finditer(text)]

    # Si no encuentra títulos, usar chunking por párrafos como fallback
    if not positions:
        return chunk_by_paragraphs(text)

    chunks = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        chunk = text[pos:end].strip()
        # Ignorar secciones vacías o demasiado cortas para ser útiles
        if len(chunk) > 100:
            chunks.append(chunk)

    return chunks


def chunk_by_paragraphs(text: str, overlap: int = 1) -> list[str]:
    """
    Para documentos no estructurados.
    Divide por párrafos naturales y añade overlap de 1 párrafo
    para no perder contexto en los límites entre chunks.
    """
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    chunks = []

    for i, paragraph in enumerate(paragraphs):
        # Ignorar párrafos demasiado cortos (encabezados, números de página)
        if len(paragraph) < 50:
            continue
        # El párrafo anterior actúa como contexto del chunk actual
        if i > 0 and overlap:
            chunk = paragraphs[i - 1] + "\n\n" + paragraph
        else:
            chunk = paragraph
        chunks.append(chunk)

    return chunks


def process_document(path: str) -> dict:
    """
    Función principal del procesador.
    Recibe la ruta de un documento, detecta su tipo,
    aplica el chunking correcto y devuelve todo listo para indexar.
    """
    text = read_document(path)
    doc_type = detect_document_type(text)

    if doc_type == 'structured':
        chunks = chunk_by_sections(text)
    else:
        chunks = chunk_by_paragraphs(text)

    return {
        "type": doc_type,
        "chunks": chunks,
        "total_chunks": len(chunks),
        "total_chars": len(text)
    }