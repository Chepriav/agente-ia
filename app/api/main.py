from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.api.routers import organization, query
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Antropia",
    description="RAG multi-tenant para bases de conocimiento empresariales",
    version="0.1.0"
)

# --- Routers ---
app.include_router(organization.router)
app.include_router(query.router)

# --- Frontend ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    """Redirige la raíz a la interfaz web."""
    return RedirectResponse(url="/ui")

@app.get("/ui")
def ui():
    from fastapi.responses import FileResponse
    return FileResponse("app/static/index.html")

@app.get("/health")
def health():
    """Endpoint de salud para verificar que la API está funcionando."""
    return {"status": "ok", "version": "0.1.0"}