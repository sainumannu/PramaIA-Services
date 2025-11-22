"""
Middleware per il monitoraggio delle operazioni di LogService.
"""

import time
import logging
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("LogService.Middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware per registrare le richieste HTTP e i loro tempi di risposta.
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log della richiesta
        logger.info(f"Richiesta {request.method} a {request.url.path}")
        
        # Per le ricerche nella dashboard, registra i parametri di filtro
        if request.url.path == "/dashboard/" and request.method == "GET":
            query_params = dict(request.query_params)
            logger.info(f"Parametri di ricerca: {query_params}")
        
        # Esegui la richiesta
        response = await call_next(request)
        
        # Calcola il tempo di esecuzione
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log della risposta
        logger.info(f"Risposta {response.status_code} in {process_time:.2f}s")
        
        return response

def setup_middleware(app: FastAPI):
    """
    Configura il middleware per l'applicazione.
    """
    app.add_middleware(LoggingMiddleware)