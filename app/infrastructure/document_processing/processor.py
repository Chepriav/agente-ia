import re
from pypdf import PdfReader
from docx import Document as DocxDocument


def read_document(path: str) -> str:
    """Lee un PDF o Word y devuelve el texto completo."""
    if path.endswith('.pdf'):
        reader = PdfReader(path)
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    elif path.endswith('.docx'):
        doc = DocxDocument(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"Unsupported format: {path}")


def detect_document_type(text: str) -> str:
    """
    Analiza las primeras 100 líneas y decide si el documento
    tiene estructura clara o es texto libre.
    Devuelve: 'structured' o 'unstructured'
    """
    lines = [l for l in text.split('\n') if l.strip()][:100]
    matches = 0

    for line in lines:
        line = line.strip()
        if re.match(r'^(\d+\.|\d+\))\s', line):
            matches += 1
        elif re.match(r'^(Chapter|Capítulo|Sección|Section)\s', line, re.I):
            matches += 1
        elif len(line) < 60 and line.isupper():
            matches += 1

    ratio = matches / max(len(lines), 1)
    return 'structured' if ratio > 0.05 else 'unstructured'


def chunk_by_sections(text: str) -> list[str]:
    """
    Para documentos estructurados.
    Usa los títulos como separadores y devuelve cada sección completa.
    """
    title_pattern = re.compile(
        r'^(\d+\.|\d+\)|Chapter|Capítulo|Sección|Section|\b[A-Z][A-Z\s]{3,}\b)',
        re.MULTILINE | re.IGNORECASE
    )
    positions = [m.start() for m in title_pattern.finditer(text)]

    if not positions:
        return chunk_by_paragraphs(text)

    chunks = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        chunk = text[pos:end].strip()
        if len(chunk) > 100:
            chunks.append(chunk)

    return chunks


def chunk_by_paragraphs(text: str, overlap: int = 1) -> list[str]:
    """
    Para documentos no estructurados.
    Divide por párrafos naturales con overlap de 1 párrafo.
    """
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    chunks = []

    for i, paragraph in enumerate(paragraphs):
        if len(paragraph) < 50:
            continue
        if i > 0 and overlap:
            chunk = paragraphs[i - 1] + "\n\n" + paragraph
        else:
            chunk = paragraph
        chunks.append(chunk)

    return chunks


def process_document(path: str) -> dict:
    """
    Función principal. Lee el documento, detecta su tipo y lo trocea.
    Devuelve chunks listos para indexar junto con metadata.
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