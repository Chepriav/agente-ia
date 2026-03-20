import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.api.dependencies import get_upload_use_case, get_document_repo
from app.infrastructure.document_processing.processor import process_document

router = APIRouter(prefix="/org", tags=["organizations"])


@router.post("/{org_id}/upload")
async def upload_document(
    org_id: str,
    file: UploadFile = File(...),
    org_name: str = Form(None)
):
    """
    Sube un documento a la base de conocimiento de una organización.
    Si la organización no existe la crea automáticamente.
    """
    # Validar formato
    if not (file.filename.endswith('.pdf') or file.filename.endswith('.docx')):
        raise HTTPException(status_code=400, detail="Only PDF and Word documents are supported")

    # Guardar archivo temporalmente
    upload_path = f"documents/{org_id}"
    os.makedirs(upload_path, exist_ok=True)
    file_path = f"{upload_path}/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Procesar documento
    result = process_document(file_path)

    # Ejecutar caso de uso
    use_case = get_upload_use_case()
    document = use_case.execute(
        org_id=org_id,
        filename=file.filename,
        chunks=result["chunks"]
    )
    document.doc_type = result["type"]

    return {
        "document_id": document.id,
        "filename": document.filename,
        "type": result["type"],
        "total_chunks": result["total_chunks"],
        "org_id": org_id
    }


@router.get("/{org_id}/documents")
def list_documents(org_id: str):
    """Lista todos los documentos indexados de una organización."""
    repo = get_document_repo()
    org = repo.get_organization(org_id)

    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    documents = repo.get_documents(org_id)

    return {
        "org_id": org_id,
        "total_documents": len(documents),
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "total_chunks": doc.total_chunks,
                "type": doc.doc_type
            }
            for doc in documents
        ]
    }