"""
Router per la visualizzazione del ciclo di vita dei documenti.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from core.auth import get_api_key

# Inizializza il router
router = APIRouter()

# Inizializza il gestore dei template
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/lifecycle", response_class=HTMLResponse)
async def lifecycle_view(
    request: Request,
    # api_key: str = Depends(get_api_key)  # Disabilitato temporaneamente per lo sviluppo
):
    """
    Pagina per visualizzare il ciclo di vita dei documenti.
    """
    return templates.TemplateResponse(
        "lifecycle.html",
        {
            "request": request,
            "title": "Ciclo di Vita Documenti - PramaIA LogService"
        }
    )