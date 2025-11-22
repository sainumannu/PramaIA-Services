"""
Router per la pagina di ricerca dei log.
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
import datetime as dt
from typing import Optional

from core.auth import get_api_key
from core.models import LogLevel, LogProject
from core.log_manager import LogManager

# Inizializza il router
router = search_router = APIRouter()

# Inizializza il gestore dei template
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "templates")
templates = Jinja2Templates(directory=templates_dir)

# Inizializza il gestore dei log
log_manager = LogManager()

@search_router.get("/", response_class=HTMLResponse)
async def search_logs(
    request: Request,
    project: Optional[str] = None,
    level: Optional[str] = None,
    module: Optional[str] = None,
    document_id: Optional[str] = None,  # Parametro per filtrare per ID documento
    file_name: Optional[str] = None,    # Parametro per filtrare per nome file
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "timestamp",         # Parametro per ordinare i risultati
    sort_order: str = "desc",           # Parametro per l'ordine di ordinamento
    limit: int = 100,
    offset: int = 0,
    # Disabilitato temporaneamente per lo sviluppo
    # api_key: str = Depends(get_api_key)
):
    """
    Pagina di ricerca dei log.
    
    Permette di filtrare i log in base a diversi criteri.
    """
    # Converti parametri in tipi appropriati
    # Per project, accetta sia la stringa diretta che il valore Enum
    project_param = project
    if project:
        try:
            # Verifica se il valore è un membro valido dell'enum
            project_param = LogProject(project)
        except ValueError:
            # Se non è un valore enum valido, lascialo come stringa
            project_param = project
    
    # Per il livello, accetta sia la stringa diretta che il valore Enum
    level_param = level
    if level:
        # Non convertire il livello in Enum, passa la stringa direttamente
        level_param = level
    
    start_datetime = None
    if start_date:
        try:
            start_datetime = dt.datetime.fromisoformat(start_date)
        except ValueError:
            start_datetime = None
    
    end_datetime = None
    if end_date:
        try:
            end_datetime = dt.datetime.fromisoformat(end_date)
        except ValueError:
            end_datetime = None
    
    # Ottieni log filtrati
    logs = log_manager.get_logs(
        project=project_param,
        level=level_param,
        module=module,
        document_id=document_id,
        file_name=file_name,
        start_date=start_datetime,
        end_date=end_datetime,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    
    # Se i filtri non restituiscono risultati, mostra lista vuota (comportamento corretto)
    # Non fare fallback a tutti i log - se un utente filtra e non trova nulla, deve vedere lista vuota
    
    # Identificare se la ricerca è per lifecycle o per un altro livello
    is_lifecycle_search = level == "lifecycle" if level else False
    
    # Nota: La logica di filtro è ora gestita completamente in log_manager.py
    # Non è più necessario post-processare qui dato che il backend ora gestisce correttamente
    # la separazione tra log lifecycle e altri livelli
    
    # Ordinamento speciale per eventi lifecycle per mostrare la sequenza temporale
    if is_lifecycle_search and file_name and not document_id:
        # Se c'è un filtro per nome file ma non per document_id, ordina cronologicamente (dal più vecchio)
        logs = sorted(logs, key=lambda x: x["timestamp"])
    
    # Calcola pagination
    total_logs = len(logs)  # Questo è una semplificazione, in realtà dovremmo contare tutti i log che corrispondono al filtro
    
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "logs": logs,
            "total": total_logs,
            "limit": limit,
            "offset": offset,
            "project": project,
            "level": level,
            "module": module,
            "document_id": document_id,
            "file_name": file_name, 
            "start_date": start_date,
            "end_date": end_date,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "title": "Ricerca Log - PramaIA LogService"
        }
    )


@search_router.get("/search")
async def search_redirect(request: Request):
    """Alias compatibile con i link esistenti che puntano a /dashboard/search: reindirizza a /dashboard/ mantenendo la query string."""
    query = request.url.query
    target = "/dashboard/" + ("?" + query if query else "")
    return RedirectResponse(url=target)

@search_router.get("/logservice", response_class=HTMLResponse)
async def logservice_page(
    request: Request,
    # Disabilitato temporaneamente per lo sviluppo
    # api_key: str = Depends(get_api_key)
):
    """
    Pagina dedicata al servizio di logging.
    
    Mostra informazioni sul servizio, client attivi, chiavi API e guide all'integrazione.
    """
    # Ottieni le impostazioni
    from core.config import get_settings
    import datetime as dt
    settings = get_settings()
    
    # Ottieni informazioni sullo stato del servizio
    uptime = dt.datetime.now() - log_manager.start_time if hasattr(log_manager, 'start_time') else "N/A"
    uptime_str = str(uptime).split('.')[0] if isinstance(uptime, dt.timedelta) else uptime
    
    # Recupera le statistiche sui client dal database
    conn = log_manager._get_connection()
    cursor = conn.cursor()
    
    # Ottieni il numero di connessioni attive e totali (stimato dai log recenti)
    cursor.execute("""
        SELECT COUNT(DISTINCT project || ':' || module) as active_connections
        FROM logs
        WHERE timestamp >= ?
    """, ((dt.datetime.now() - dt.timedelta(hours=1)).isoformat(),))
    active_connections = cursor.fetchone()["active_connections"]
    
    cursor.execute("SELECT COUNT(DISTINCT project || ':' || module) as total_connections FROM logs")
    total_connections = cursor.fetchone()["total_connections"]
    
    # Dati di stato del servizio
    service_status = {
        "is_running": True,
        "uptime": uptime_str,
        "active_connections": active_connections,
        "total_connections": total_connections,
        "logs_received_today": log_manager.get_logs_count(
            start_date=dt.datetime.now() - dt.timedelta(days=1)
        ),
        "db_size": log_manager.get_db_size(),
        "total_logs": log_manager.get_logs_count()
    }
    
    # Ottieni dati reali sui client attivi dal database
    cursor.execute("""
        SELECT 
            project,
            module,
            MAX(timestamp) as last_log_time,
            COUNT(*) as logs_sent
        FROM logs
        GROUP BY project, module
        ORDER BY last_log_time DESC
        LIMIT 10
    """)
    client_data = cursor.fetchall()
    
    # Crea la lista dei client attivi con dati reali
    active_clients = []
    for i, client in enumerate(client_data):
        # Calcola lo stato in base all'ultima attività
        last_log_time = dt.datetime.fromisoformat(client["last_log_time"])
        status = "online" if (dt.datetime.now() - last_log_time) < dt.timedelta(hours=1) else "idle"
        
        active_clients.append({
            "id": f"client-{i+1:03d}",
            "project": client["project"],
            "module": client["module"],
            "last_log_time": client["last_log_time"],
            "logs_sent": client["logs_sent"],
            "status": status
        })
    
    # Non chiudere ancora la connessione, verrà usata più avanti
    
    # Ottieni le chiavi API reali dal file di configurazione
    import os
    import json
    
    api_keys = []
    api_keys_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "api_keys.json")
    
    if os.path.exists(api_keys_path):
        try:
            with open(api_keys_path, "r") as f:
                api_keys_data = json.load(f)
                
            # Ottieni i timestamp dell'ultimo utilizzo di ciascuna chiave
            last_used_query = """
                SELECT project, MAX(timestamp) as last_used 
                FROM logs 
                GROUP BY project
            """
            cursor.execute(last_used_query)
            # Ottieni e archivia i risultati prima di chiudere la connessione
            last_used_data = {row["project"]: row["last_used"] for row in cursor.fetchall()}
            
            # Ora che abbiamo finito con il database, possiamo chiudere la connessione
            conn.close()
            
            # Formatta le chiavi API per la visualizzazione
            for key_name, key_info in api_keys_data.items():
                try:
                    if isinstance(key_info, str):
                        # Formato semplice: chiave come stringa
                        project = key_name
                        api_key = key_info
                    else:
                        # Formato esteso: chiave come dizionario
                        # Usa 'name' come fallback per il progetto se 'project' non è presente
                        project = key_info.get("project", key_info.get("name", key_name))
                        api_key = key_info.get("key", "")
                    
                    # Maschera la chiave API per sicurezza
                    key_masked = f"{api_key[:8]}{'*' * 8}" if len(api_key) > 8 else f"{api_key[:4]}{'*' * 4}"
                    
                    # Ottieni l'ultimo utilizzo, se disponibile
                    last_used = last_used_data.get(project, "Mai utilizzata")
                    
                    api_keys.append({
                        "id": key_name,  # Aggiungiamo l'ID della chiave (il nome nel dizionario)
                        "name": f"{project} API Key",
                        "key_masked": key_masked,
                        "project": project,
                        "created_at": key_info.get("created_at", "N/A") if isinstance(key_info, dict) else "N/A",
                        "last_used": last_used
                    })
                except Exception as e:
                    # Se c'è un errore nella gestione di una singola chiave, logga e continua
                    import logging
                    logging.getLogger("LogService").error(f"Errore nella formattazione della chiave API {key_name}: {str(e)}")
                    
                    # Aggiungi una voce di errore per questa chiave
                    api_keys.append({
                        "id": key_name,  # Aggiungiamo l'ID della chiave (il nome nel dizionario)
                        "name": f"Errore nella chiave {key_name}",
                        "key_masked": "ERRORE",
                        "project": key_name,
                        "created_at": "N/A",
                        "last_used": "N/A"
                    })
        except Exception as e:
            # Logga l'errore per la diagnosi
            import logging
            logging.getLogger("LogService").error(f"Errore nel caricamento delle chiavi API: {str(e)}")
            
            # In caso di errore, mostra un messaggio
            api_keys = [{
                "id": "error",  # Aggiungiamo un ID anche per il messaggio di errore
                "name": f"Errore nel caricamento delle chiavi API: {str(e)}",
                "key_masked": "N/A",
                "project": "N/A",
                "created_at": "N/A",
                "last_used": "N/A"
            }]
    else:
        # Se il file non esiste, mostra un messaggio
        api_keys = [{
            "id": "no_keys",  # Aggiungiamo un ID anche per il messaggio di nessuna chiave
            "name": "Nessuna chiave API configurata",
            "key_masked": "N/A", 
            "project": "N/A",
            "created_at": "N/A",
            "last_used": "N/A"
        }]
    
    return templates.TemplateResponse(
        "logservice.html",
        {
            "request": request,
            "title": "LogService - PramaIA LogService",
            "status": service_status,
            "clients": active_clients,
            "api_keys": api_keys,
            "settings": settings
        }
    )
