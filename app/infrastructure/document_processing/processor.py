import re
import statistics
import pdfplumber
from docx import Document as DocxDocument

MAX_CHUNK_SIZE = 1500
OVERLAP_RATIO = 0.2


def read_pdf(path: str) -> list[dict]:
    """
    Lee un PDF con pdfplumber extrayendo texto y tamaño de fuente.
    Devuelve lista de bloques con texto y tamaño para detectar títulos.
    """
    blocks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(extra_attrs=['size'])
            if not words:
                continue
            # Agrupar palabras en líneas por posición vertical
            lines = {}
            for word in words:
                y = round(word['top'], 0)
                if y not in lines:
                    lines[y] = {'text': '', 'size': word.get('size', 0)}
                lines[y]['text'] += ' ' + word['text']
                lines[y]['size'] = max(lines[y]['size'], word.get('size', 0))
            for y in sorted(lines):
                block = lines[y]
                block['text'] = block['text'].strip()
                if block['text']:
                    blocks.append(block)
    return blocks


def read_docx(path: str) -> list[dict]:
    """
    Lee un Word extrayendo párrafos con su estilo.
    Los estilos Heading son títulos reales.
    """
    doc = DocxDocument(path)
    blocks = []
    for para in doc.paragraphs:
        if not para.text.strip():
            continue
        is_heading = para.style is not None and para.style.name.startswith('Heading')
        blocks.append({
            'text': para.text.strip(),
            'is_heading': is_heading
        })
    return blocks


def detect_title_threshold(blocks: list[dict]) -> float:
    """
    Calcula el umbral de tamaño de fuente para considerar un bloque como título.
    Usa la mediana del texto normal y multiplica por 1.4.
    """
    sizes = [b['size'] for b in blocks if b.get('size', 0) > 0]
    if not sizes:
        return 0
    median = statistics.median(sizes)
    return median * 1.4


def chunk_structured(blocks: list[dict], is_title_fn) -> list[str]:
    """
    Agrupa bloques en chunks usando títulos como separadores.
    """
    chunks = []
    current_title = ""
    current_content = ""

    for block in blocks:
        text = block['text']
        if is_title_fn(block):
            if current_content.strip():
                section = (current_title + "\n\n" + current_content).strip()
                chunks.extend(split_with_overlap(section))
            current_title = text
            current_content = ""
        else:
            current_content += ("\n\n" if current_content else "") + text

    if current_content.strip():
        section = (current_title + "\n\n" + current_content).strip()
        chunks.extend(split_with_overlap(section))

    return chunks


def chunk_sliding_window(blocks: list[dict]) -> list[str]:
    """Ventana deslizante con overlap para texto sin estructura."""
    overlap_size = int(MAX_CHUNK_SIZE * OVERLAP_RATIO)
    chunks = []
    current = ""
    overlap_buffer = ""

    for block in blocks:
        text = block['text']
        if len(text) < 20:
            continue
        if len(current) + len(text) + 2 <= MAX_CHUNK_SIZE:
            current += ("\n\n" if current else "") + text
        else:
            if current:
                chunks.append(current)
                overlap_buffer = current[-overlap_size:]
            current = (overlap_buffer + "\n\n" + text).strip() if overlap_buffer else text
            overlap_buffer = ""

    if current:
        chunks.append(current)

    return chunks


def split_with_overlap(text: str) -> list[str]:
    """Divide texto largo con overlap."""
    if len(text) <= MAX_CHUNK_SIZE:
        return [text]

    overlap_size = int(MAX_CHUNK_SIZE * OVERLAP_RATIO)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    overlap_buffer = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= MAX_CHUNK_SIZE:
            current += (" " if current else "") + sentence
        else:
            if current:
                chunks.append(current)
                overlap_buffer = current[-overlap_size:]
            current = (overlap_buffer + " " + sentence).strip() if overlap_buffer else sentence
            overlap_buffer = ""

    if current:
        chunks.append(current)

    return chunks if chunks else [text[:MAX_CHUNK_SIZE]]


def process_document(path: str) -> dict:
    """
    Función principal. Detecta el tipo de documento y aplica
    la estrategia de chunking más adecuada.
    """
    if path.endswith('.pdf'):
        blocks = read_pdf(path)
        threshold = detect_title_threshold(blocks)
        title_count = sum(1 for b in blocks if b.get('size', 0) >= threshold)

        if title_count >= 2:
            doc_type = 'structured'
            chunks = chunk_structured(blocks, lambda b: b.get('size', 0) >= threshold)
        else:
            doc_type = 'unstructured'
            chunks = chunk_sliding_window(blocks)

    elif path.endswith('.docx'):
        blocks = read_docx(path)
        heading_count = sum(1 for b in blocks if b.get('is_heading'))

        if heading_count >= 2:
            doc_type = 'structured'
            chunks = chunk_structured(blocks, lambda b: b.get('is_heading'))
        else:
            doc_type = 'unstructured'
            chunks = chunk_sliding_window(blocks)
    else:
        raise ValueError(f"Unsupported format: {path}")

    chunks = [c for c in chunks if len(c.strip()) > 100]

    return {
        "type": doc_type,
        "chunks": chunks,
        "total_chunks": len(chunks),
        "total_chars": sum(len(c) for c in chunks)
    }