import re
import unicodedata


def normalize_org_id(org_id: str) -> str:
    """
    Normaliza un org_id para que sea válido en ChromaDB y consistente.
    - Convierte a minúsculas
    - Elimina acentos y caracteres especiales
    - Reemplaza espacios y caracteres no válidos por guiones
    - Elimina guiones duplicados
    
    Ejemplos:
        "Carmen Mola"  → "carmen-mola"
        "Policía Nacional" → "policia-nacional"
        "carmen%20mola" → "carmen-mola"
        "INTEC S.A." → "intec-s-a"
    """
    # Decodificar URL encoding (%20, etc.)
    org_id = org_id.replace("%20", " ")

    # Convertir a minúsculas
    org_id = org_id.lower()

    # Eliminar acentos (normalizar unicode NFD y quitar diacríticos)
    org_id = unicodedata.normalize("NFD", org_id)
    org_id = "".join(c for c in org_id if unicodedata.category(c) != "Mn")

    # Reemplazar cualquier carácter no válido por guión
    org_id = re.sub(r"[^a-z0-9]+", "-", org_id)

    # Eliminar guiones al inicio y al final
    org_id = org_id.strip("-")

    # Eliminar guiones duplicados
    org_id = re.sub(r"-+", "-", org_id)

    return org_id