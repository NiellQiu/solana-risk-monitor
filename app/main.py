from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(title="Personal Solana Risk Monitor")
app.include_router(router)

web_dir = Path(__file__).resolve().parent.parent / "web"
app.mount("/web", StaticFiles(directory=web_dir), name="web")


@app.get("/")
def index():
    return FileResponse(web_dir / "index.html")
