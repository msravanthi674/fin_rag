from fastapi import FastAPI
from dotenv import load_dotenv
from app.services.watcher_service import start_watcher
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os


load_dotenv()

app = FastAPI(title="FinRAG Intelligence Portal")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start background ticker watcher
start_watcher()

from app.routes.email_webhook import router as email_router
from app.routes.query import router as query_router
from app.routes.fin_ingest import router as fin_router

app.include_router(email_router)
app.include_router(query_router)
app.include_router(fin_router)

# Serve Frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# Serve CSS and JS directly in root if needed for the HTML to find them easily
@app.get("/{file_path:path}")
def serve_static_files(file_path: str):
    full_path = os.path.join(frontend_path, file_path)
    if os.path.exists(full_path):
        return FileResponse(full_path)
    return {"error": "Not Found"}