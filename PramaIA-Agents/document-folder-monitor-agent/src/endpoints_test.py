"""Endpoint di test per simulare disconnessione (modulo reso importabile per pytest).
Questo file espone una piccola FastAPI `app` con un endpoint di test. Se nel runtime
sono disponibili `logger`, `try_register` o `update_connection_state`, verranno usati;
altrimenti il codice li ignora per permettere la collection dei test.
"""

from fastapi import FastAPI
import logging

app = FastAPI()
logger = logging.getLogger(__name__)


@app.post("/monitor/offline")
async def force_offline():
    """Endpoint per simulare una disconnessione (solo per test)."""
    logger.info("Test: Simulazione disconnessione")
    # Tentativo di utilizzare le funzioni dell'agente se sono disponibili
    try:
        from . import try_register  # type: ignore
    except Exception:
        try_register = None

    try:
        from . import update_connection_state  # type: ignore
    except Exception:
        update_connection_state = None

    if callable(try_register):
        try:
            try_register(online=False)
        except Exception:
            logger.exception('try_register failed')

    if callable(update_connection_state):
        try:
            update_connection_state(False)
        except Exception:
            logger.exception('update_connection_state failed')

    return {"status": "success", "message": "Disconnessione simulata attivata"}
