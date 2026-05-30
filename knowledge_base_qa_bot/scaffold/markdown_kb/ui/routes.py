import pathlib
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

ui_router = APIRouter()

# Absolute path to the index.html inside our static/ folder
UI_DIR = pathlib.Path(__file__).resolve().parent
INDEX_HTML_PATH = UI_DIR / "static" / "index.html"

@ui_router.get("/", response_class=HTMLResponse)
def get_dashboard():
    """
    Serves the premium single-page web dashboard.
    """
    if INDEX_HTML_PATH.exists():
        with INDEX_HTML_PATH.open("r", encoding="utf-8") as f:
            return f.read()
    return "<h1>UI Dashboard: index.html is missing inside static/</h1>"
