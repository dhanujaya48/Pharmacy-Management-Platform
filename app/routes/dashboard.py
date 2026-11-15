import os
from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter(tags=["Dashboard UI"])

INDEX_HTML_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "index.html")
)


@router.get("/dashboard", response_class=HTMLResponse, summary="Visual Web Dashboard")
def get_dashboard():
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)
    return HTMLResponse("<h1>index.html not found</h1>", status_code=404)
