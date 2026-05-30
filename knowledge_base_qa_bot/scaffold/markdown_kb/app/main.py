from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import pathlib

from .indexer import load_index_json
from .routes import router
from ui.routes import ui_router

app = FastAPI(title="Markdown Knowledge Base Q&A Bot")

# Mount the UI static assets directory (contains CSS, JS)
UI_STATIC_DIR = pathlib.Path(__file__).resolve().parents[1] / "ui" / "static"
app.mount("/ui/static", StaticFiles(directory=UI_STATIC_DIR), name="ui_static")

app.include_router(router)
app.include_router(ui_router)


@app.on_event("startup")
def load_persisted_index():
    load_index_json()
