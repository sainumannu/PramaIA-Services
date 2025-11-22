"""
Router per la dashboard web del servizio di logging.
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import datetime as dt
from typing import Optional

from core.auth import get_api_key
from core.models import LogLevel, LogProject
from core.log_manager import LogManager

# Inizializza il router
router = dashboard_router = APIRouter()

# Inizializza il gestore dei template
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "templates")
templates = Jinja2Templates(directory=templates_dir)

# Inizializza il gestore dei log
log_manager = LogManager()

@dashboard_router.get("/", response_class=HTMLResponse)
async def dashboard_home(
    request: Request,
    # Disabilitato temporaneamente per lo sviluppo
    # api_key: str = Depends(get_api_key)
):
    """
    Pagina principale della dashboard.
    
    Mostra una panoramica dei log recenti e statistiche generali.
    """
    # Ottieni statistiche recenti
    stats = log_manager.get_stats()
    
    # Ottieni log recenti (ultimi 100)
    recent_logs = log_manager.get_logs(limit=100)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "logs": recent_logs,
            "title": "Dashboard PramaIA LogService"
        }
    )

@dashboard_router.get("/search", response_class=HTMLResponse)
async def dashboard_search(
    request: Request,
    project: Optional[str] = None,
    level: Optional[str] = None,
    module: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
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
    project_enum = LogProject(project) if project else None
    level_enum = LogLevel(level) if level else None
    
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
        project=project_enum,
        level=level_enum,
        module=module,
        start_date=start_datetime,
        end_date=end_datetime,
        limit=limit,
        offset=offset
    )
    
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
            "start_date": start_date,
            "end_date": end_date,
            "title": "Ricerca Log - PramaIA LogService"
        }
    )

# Temporaneamente commentato - il template stats.html manca
# @dashboard_router.get("/stats", response_class=HTMLResponse)
# async def dashboard_stats(
#     request: Request,
#     project: Optional[str] = None,
#     days: int = 7,
#     # Disabilitato temporaneamente per lo sviluppo
#     # api_key: str = Depends(get_api_key)
# ):
#     """
#     Pagina di statistiche dei log.
#     
#     Mostra grafici e statistiche aggregate sui log.
#     """
#     # Converti parametri in tipi appropriati
#     project_enum = LogProject(project) if project else None
#     
#     # Calcola date per il periodo richiesto
#     end_date = datetime.now()
#     start_date = end_date - timedelta(days=days)
#     
#     # Ottieni statistiche
#     stats = log_manager.get_stats(
#         project=project_enum,
#         start_date=start_date,
#         end_date=end_date
#     )
#     
#     return templates.TemplateResponse(
#         "stats.html",
#         {
#             "request": request,
#             "stats": stats,
#             "project": project,
#             "days": days,
#             "title": "Statistiche Log - PramaIA LogService"
#         }
#     )

# Temporaneamente commentato - il template settings.html manca
# @dashboard_router.get("/settings", response_class=HTMLResponse)
# async def dashboard_settings(
#     request: Request,
#     # Disabilitato temporaneamente per lo sviluppo
#     # api_key: str = Depends(get_api_key)
# ):
#     """
#     Pagina di configurazione del servizio.
#     
#     Permette di visualizzare e modificare le impostazioni del servizio.
#     """
#     return templates.TemplateResponse(
#         "settings.html",
#         {
#             "request": request,
#             "title": "Impostazioni - PramaIA LogService"
#         }
#     )

@dashboard_router.get("/logservice", response_class=HTMLResponse)
async def dashboard_logservice(
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
