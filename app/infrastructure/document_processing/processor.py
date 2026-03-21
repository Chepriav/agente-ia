import re
import statistics
from unstructured.partition.auto import partition
from unstructured.documents.elements import Title, NarrativeText, Text, ListItem, Table

MAX_CHUNK_SIZE = 1500
OVERLAP_RATIO = 0.2  # 20% de overlap


def read_document(path: str) -> list:
    """
    Lee un PDF o Word usando unstructured.
    Devuelve elementos tipados con metadata de formato.
    """
    return partition(filename=path)


def get_element_height(element) -> float:
    """Extrae la altura de un elemento desde sus coordenadas."""
    coords = element.metadata.to_dict().get('coordinates', {})
    points = coords.get('points', [])
    if points and len(points) >= 3:
        return points[2][1] - points[0][1]
    return 0.0


def detect_real_titles(elements: list) -> set:
    """
    Detecta qué elementos son títulos reales de forma genérica.

    Para documentos con coordenadas (PDF): usa altura relativa.
    Un título real tiene altura significativamente mayor al texto normal.

    Para documentos sin coordenadas (Word): confía en los Title de unstructured.
    """
    title_indices = set()

    # Comprobar si el documento tiene coordenadas
    has_coordinates = any(
        get_element_height(el) > 0
        for el in elements[:50]
    )

    if not has_coordinates:
        # Word u otro formato — confiar directamente en Title de unstructured
        for i, el in enumerate(elements):
            if isinstance(el, Title):
                title_indices.add(i)
        return title_indices

    # PDF — usar altura relativa para filtrar falsos positivos
    heights = [get_element_height(el) for el in elements if get_element_height(el) > 0]

    if not heights:
        return title_indices

    # Calcular la mediana de altura del texto normal
    median_height = statistics.median(heights)

    # Un título real tiene altura al menos 1.4x la mediana
    title_threshold = median_height * 1.4

    for i, el in enumerate(elements):
        if isinstance(el, Title):
            height = get_element_height(el)
            if height == 0 or height >= title_threshold:
                title_indices.add(i)

    return title_indices


def chunk_by_sections(elements: list, title_indices: set) -> list[str]:
    """
    Para documentos estructurados.
    Cada sección (título + contenido) = un chunk.
    Si supera MAX_CHUNK_SIZE se subdivide con overlap.
    """
    chunks = []
    current_title = ""
    current_content = ""

    for i, el in enumerate(elements):
        text = str(el).strip()
        if not text:
            continue

        if i in title_indices:
            # Guardar sección anterior
            if current_content.strip():
                section = (current_title + "\n\n" + current_content).strip()
                chunks.extend(split_with_overlap(section))
            current_title = text
            current_content = ""
        else:
            current_content += ("\n\n" if current_content else "") + text

    # Última sección
    if current_content.strip():
        section = (current_title + "\n\n" + current_content).strip()
        chunks.extend(split_with_overlap(section))

    return chunks


def chunk_by_sliding_window(elements: list) -> list[str]:
    """
    Para documentos sin estructura clara.
    Ventana deslizante con overlap del 20%.
    Garantiza que ninguna información queda partida entre chunks.
    """
    overlap_size = int(MAX_CHUNK_SIZE * OVERLAP_RATIO)
    chunks = []
    current = ""
    overlap_buffer = ""

    for el in elements:
        text = str(el).strip()
        if not text or len(text) < 20:
            continue

        if len(current) + len(text) + 2 <= MAX_CHUNK_SIZE:
            current += ("\n\n" if current else "") + text
        else:
            if current:
                chunks.append(current)
                # Overlap: guardar los últimos overlap_size chars como inicio del siguiente chunk
                overlap_buffer = current[-overlap_size:] if len(current) > overlap_size else current

            current = (overlap_buffer + "\n\n" + text).strip() if overlap_buffer else text
            overlap_buffer = ""

    if current:
        chunks.append(current)

    return chunks


def split_with_overlap(text: str) -> list[str]:
    """
    Divide un texto largo respetando límites naturales en este orden:
    1. Párrafos (\n)
    2. Frases (. ! ?)
    3. Corte forzado si no hay ningún separador natural
    Con overlap del 20% entre chunks consecutivos.
    """
    if len(text) <= MAX_CHUNK_SIZE:
        return [text]

    overlap_size = int(MAX_CHUNK_SIZE * OVERLAP_RATIO)

    # Intentar dividir por párrafos primero
    paragraphs = [p.strip() for p in re.split(r'\n+', text) if p.strip()]

    # Si los párrafos son demasiado largos, dividir por frases
    fine_chunks = []
    for p in paragraphs:
        if len(p) <= MAX_CHUNK_SIZE:
            fine_chunks.append(p)
        else:
            # Dividir por frases
            sentences = re.split(r'(?<=[.!?])\s+', p)
            current = ""
            for sentence in sentences:
                if len(current) + len(sentence) + 1 <= MAX_CHUNK_SIZE:
                    current += (" " if current else "") + sentence
                else:
                    if current:
                        fine_chunks.append(current)
                    # Si la frase sola supera el límite, corte forzado
                    if len(sentence) > MAX_CHUNK_SIZE:
                        for i in range(0, len(sentence), MAX_CHUNK_SIZE - overlap_size):
                            fine_chunks.append(sentence[i:i + MAX_CHUNK_SIZE])
                    else:
                        current = sentence
            if current:
                fine_chunks.append(current)

    # Agrupar chunks pequeños con overlap
    chunks = []
    current = ""
    overlap_buffer = ""

    for piece in fine_chunks:
        if len(current) + len(piece) + 2 <= MAX_CHUNK_SIZE:
            current += ("\n\n" if current else "") + piece
        else:
            if current:
                chunks.append(current)
                overlap_buffer = current[-overlap_size:] if len(current) > overlap_size else current
            current = (overlap_buffer + "\n\n" + piece).strip() if overlap_buffer else piece
            overlap_buffer = ""

    if current:
        chunks.append(current)

    return chunks if chunks else [text[:MAX_CHUNK_SIZE]]


def process_document(path: str) -> dict:
    """
    Función principal. Lee el documento con unstructured,
    detecta títulos reales de forma genérica y aplica
    la estrategia de chunking más adecuada.
    """
    elements = read_document(path)
    title_indices = detect_real_titles(elements)

    # Si hay suficientes títulos reales, usar chunking por secciones
    if len(title_indices) >= 2:
        chunks = chunk_by_sections(elements, title_indices)
        doc_type = 'structured'
    else:
        chunks = chunk_by_sliding_window(elements)
        doc_type = 'unstructured'

    # Filtrar chunks vacíos o demasiado cortos
    chunks = [c for c in chunks if len(c.strip()) > 100]

    return {
        "type": doc_type,
        "chunks": chunks,
        "total_chunks": len(chunks),
        "total_chars": sum(len(c) for c in chunks)
    }