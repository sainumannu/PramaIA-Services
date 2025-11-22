from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
from .folder_monitor import FolderMonitor
from .event_buffer import EventBuffer
from .logger import info, error, warning

app = FastAPI()

# Inizializza gli oggetti monitor ed event_buffer
monitor = FolderMonitor()
event_buffer = monitor.event_buffer

@app.post("/monitor/rescan_all", tags=["Maintenance"])
async def rescan_all_monitored_folders():
    """
    Esegue una scansione completa di tutte le cartelle monitorate e genera eventi 'created' per tutti i documenti trovati, anche se già presenti.
    """
    try:
        info("Ricevuta richiesta di scansione completa di tutti i file")

        # Verifica che monitor sia inizializzato correttamente
        if not hasattr(monitor, 'get_folders') or not callable(monitor.get_folders):
            raise AttributeError("L'oggetto monitor non ha il metodo get_folders")

        folders = monitor.get_folders()
        info(f"Cartelle da scansionare: {folders}")

        count = 0
        for folder in folders:
            if not os.path.exists(folder):
                warning(f"La cartella {folder} non esiste o non è accessibile")
                continue

            info(f"Scansione in corso per: {folder}")
            for root, dirs, files in os.walk(folder):
                for file in files:
                    # Lista di estensioni di documenti supportati
                    supported_extensions = ['.pdf', '.doc', '.docx', '.odt', '.txt', '.xls', '.xlsx', '.ods']
                    if any(file.lower().endswith(ext) for ext in supported_extensions):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(root, folder)
                        event_buffer.add_event('created', file, root)
                        count += 1

        info(f"Scansione completata: generati {count} eventi")
        return {"status": "success", "message": f"Scansione completata: {count} eventi generati"}
    except Exception as e:
        import traceback
        error(f"Errore durante la scansione completa: {str(e)}", details={"trace": traceback.format_exc()})
        return {"status": "error", "message": f"Errore durante la scansione completa: {str(e)}"}

from fastapi import HTTPException

app = FastAPI()

@app.delete("/monitor/events/clear", tags=["Monitoring"])
def clear_all_events():
    """
    Elimina tutti gli eventi dal buffer locale dell'agent PDF Monitor.
    """
    with sqlite3.connect(event_buffer.db_path) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM events")
        conn.commit()
    info("Tutti gli eventi eliminati dal buffer locale")
    return {"status": "success", "message": "Tutti gli eventi eliminati"}

@app.post("/monitor/clean-events", tags=["Maintenance"])
async def clean_events():
    """
    Endpoint per pulire manualmente gli eventi duplicati e aggiornare gli eventi bloccati.
    """
    try:
        # Pulizia eventi duplicati
        duplicates_removed = event_buffer.clean_duplicate_events()
        
        # Aggiornamento eventi bloccati
        stalled_updated = event_buffer.auto_update_stalled_events(max_age_hours=2)
        
        return {
            "status": "success", 
            "message": f"Pulizia completata: rimossi {duplicates_removed} eventi duplicati e aggiornati {stalled_updated} eventi bloccati",
            "details": {
                "duplicates_removed": duplicates_removed,
                "stalled_updated": stalled_updated
            }
        }
    except Exception as e:
        import traceback
        error(f"Errore durante la pulizia degli eventi: {str(e)}", details={"trace": traceback.format_exc()})
        return {"status": "error", "message": f"Errore durante la pulizia degli eventi: {str(e)}"}

@app.on_event("startup")
async def startup_event():
    info("Document Folder Monitor Plugin avviato. FastAPI in ascolto.")
    
    # Pulizia automatica degli eventi duplicati all'avvio
    try:
        info("Avvio pulizia automatica degli eventi duplicati...")
        cleaned_count = event_buffer.clean_duplicate_events()
        info(f"Pulizia automatica completata: {cleaned_count} eventi duplicati eliminati")
    except Exception as e:
        error(f"Errore durante la pulizia automatica: {str(e)}")

import os
# Leggi origins CORS da variabile d'ambiente (CORS_ORIGINS, separati da virgola)
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000")
# Aggiunta variante con https per sicurezza
cors_origins_env += ",https://localhost:3000,https://127.0.0.1:3000,https://localhost:5173,https://127.0.0.1:5173,https://localhost:8000,https://127.0.0.1:8000"

info(f"Configurazione CORS con origins: {cors_origins_env}")
origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

# Per debug temporaneo, possiamo permettere tutte le origini
enable_all_origins = os.getenv("CORS_ALLOW_ALL", "false").lower() == "true"
if enable_all_origins:
    warning("⚠️ CORS impostato per accettare TUTTE le origini (non sicuro)")
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if enable_all_origins else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
class FolderPathConfig(BaseModel):
    folder_path: str

@app.post("/monitor/configure", tags=["Monitoring"])
def configure_folder(config: FolderPathConfig):
    """
    Aggiunge una path da monitorare e la salva subito in configurazione, senza avviare la scansione.
    """
    info(f"Richiesta /monitor/configure ricevuta con payload: {config}")
    result = monitor.add_folder(config.folder_path)
    if result:
        info(f"Path aggiunta: {config.folder_path}")
        return {"status": "success", "message": f"Path aggiunta e salvata: {config.folder_path}"}
    else:
        warning(f"Path NON aggiunta: {config.folder_path}")
        return {"status": "error", "message": f"Path non aggiunta: {config.folder_path}"}

from fastapi import HTTPException
from typing import List, Optional

class MarkSentRequest(BaseModel):
    event_ids: List[int]

class EventStatusUpdate(BaseModel):
    event_id: int
    status: str
    document_id: Optional[str] = None
    error_message: Optional[str] = None

@app.get("/monitor/events", tags=["Monitoring"])
def get_unsent_events(limit: int = 100):
    """
    Restituisce gli eventi non ancora inviati al server (bufferizzati su SQLite).
    """
    return {"unsent_events": event_buffer.get_unsent_events(limit=limit)}

@app.get("/monitor/events/recent", tags=["Monitoring"])
def get_recent_events(limit: int = 100, include_history: bool = False):
    """
    Restituisce gli eventi più recenti, inclusi quelli già inviati.
    
    Args:
        limit: Numero massimo di eventi da restituire
        include_history: Se True, include anche gli eventi storici/archiviati
    """
    return {
        "events": event_buffer.get_recent_events(limit=limit, include_history=include_history),
        "include_history": include_history
    }

@app.post("/monitor/events/mark_sent", tags=["Monitoring"])
def mark_events_as_sent(req: MarkSentRequest):
    """
    Marca come inviati gli eventi con gli id specificati.
    """
    info(f"Comando ricevuto dal server: marca come inviati gli eventi con id: {req.event_ids}")
    event_buffer.mark_events_as_sent(req.event_ids)
    return {"status": "ok", "marked": req.event_ids}

@app.post("/monitor/events/update_status", tags=["Monitoring"])
def update_event_status(update: EventStatusUpdate):
    """
    Aggiorna lo stato di elaborazione di un evento specifico.
    """
    info(f"Aggiornamento stato evento {update.event_id} a '{update.status}'")
    success = event_buffer.update_event_status(
        update.event_id, 
        update.status, 
        update.document_id, 
        update.error_message
    )
    if not success:
        raise HTTPException(status_code=404, detail=f"Evento con id {update.event_id} non trovato")
    return {"status": "ok", "updated": update.event_id}

class FolderConfig(BaseModel):
    folder_paths: list[str]

@app.post("/monitor/start", tags=["Monitoring"])
def start_monitoring(config: FolderConfig):
    """
    Avvia il monitoraggio di una o più cartelle specifiche.
    Se non vengono specificate cartelle, avvia il monitoraggio su tutte le cartelle autostart configurate.
    """
    folder_paths = config.folder_paths
    
    # Se non sono state specificate cartelle, usa le cartelle autostart
    if not folder_paths:
        folder_paths = monitor.get_autostart_folders()
        info(f"Nessuna cartella specificata, utilizzo cartelle autostart: {folder_paths}")
    
    if not folder_paths:
        return {"status": "error", "message": "Nessuna cartella da monitorare specificata e nessuna cartella autostart configurata"}
    
    info(f"Comando ricevuto dal server: avvia monitoraggio sulle cartelle: {folder_paths}")
    started = []
    errors = []
    for folder in folder_paths:
        if not os.path.isdir(folder):
            errors.append(folder)
            continue
        try:
            monitor.start(folder)
            started.append(folder)
        except Exception as e:
            warning(f"Errore avvio monitoraggio per {folder}: {e}")
            errors.append(folder)
    
    if errors and not started:
        raise HTTPException(status_code=404, detail=f"Nessuna cartella valida trovata. Cartelle non esistenti o non accessibili: {errors}")
    elif errors:
        return {"status": "partial_success", "message": f"Monitoraggio avviato su {len(started)} cartelle. Errori su: {errors}", "started": started, "errors": errors}
    
    return {"status": "success", "message": f"Monitoraggio avviato sulle cartelle: {started}", "started": started}

@app.post("/monitor/start-autostart", tags=["Monitoring"])
def start_autostart_folders():
    """
    Avvia il monitoraggio di tutte le cartelle configurate con autostart.
    """
    info("Comando ricevuto dal server: avvia monitoraggio cartelle autostart")
    autostart_folders = monitor.get_autostart_folders()
    
    if not autostart_folders:
        return {"status": "info", "message": "Nessuna cartella autostart configurata"}
    
    started = monitor.start_autostart_folders()
    return {
        "status": "success", 
        "message": f"Monitoraggio autostart avviato su {started} cartelle: {autostart_folders}",
        "started_count": started,
        "folders": autostart_folders
    }

@app.post("/monitor/stop", tags=["Monitoring"])
def stop_monitoring():
    """
    Ferma il monitoraggio.
    """
    info("Comando ricevuto dal server: stop monitoraggio.")
    monitor.stop()
    return {"status": "success", "message": "Monitoraggio fermato."}

@app.get("/monitor/status", tags=["Monitoring"])
def get_monitor_status():
    """
    Restituisce lo stato attuale del monitor, inclusa la lista dei documenti trovati.
    """
    info("Comando ricevuto dal server: richiesta stato monitor.")
    return {
        "is_running": monitor.is_running(),
        "monitoring_folders": monitor.get_folders(),
        "detected_documents": monitor.get_documents(),
        "autostart_folders": monitor.get_autostart_folders()
    }

@app.get("/monitor/health", tags=["Maintenance"])
def get_monitor_health():
    """
    Restituisce informazioni dettagliate sulla salute del monitor e degli observer.
    Utile per debug e troubleshooting.
    """
    info("Richiesta stato di salute del monitor.")
    health = monitor._get_observer_health()
    return {
        "status": "healthy" if monitor.is_running() else "stopped",
        "is_running": monitor.is_running(),
        "health_details": health,
        "active_folders": monitor.get_active_folders(),
        "all_folders": monitor.get_folders()
    }

class AutostartConfig(BaseModel):
    folder_path: str
    autostart: bool = True

@app.post("/monitor/autostart", tags=["Monitoring"])
def set_folder_autostart(config: AutostartConfig):
    """
    Imposta o rimuove l'autostart per una cartella specifica.
    """
    info(f"Comando ricevuto: {'abilita' if config.autostart else 'disabilita'} autostart per {config.folder_path}")
    
    result = monitor.set_folder_autostart(config.folder_path, config.autostart)
    
    if result:
        action = "abilitato" if config.autostart else "disabilitato"
        return {"status": "success", "message": f"Autostart {action} per {config.folder_path}"}
    else:
        return {"status": "error", "message": f"Impossibile modificare autostart per {config.folder_path}"}

@app.delete("/monitor/events/{event_id}", tags=["Monitoring"])
def delete_event(event_id: int):
    """
    Elimina un evento dal buffer.
    """
    info(f"Comando ricevuto: elimina evento {event_id}")
    
    # Verifica prima se l'evento esiste
    with sqlite3.connect(event_buffer.db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM events WHERE id = ?", (event_id,))
        if not c.fetchone():
            raise HTTPException(status_code=404, detail=f"Evento con id {event_id} non trovato")
        
        # Elimina l'evento
        c.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
    
    return {"status": "success", "message": f"Evento {event_id} eliminato"}

@app.post("/monitor/events/{event_id}/retry", tags=["Monitoring"])
def retry_event(event_id: int):
    """
    Riprova l'elaborazione di un evento in errore.
    """
    info(f"Comando ricevuto: riprova elaborazione evento {event_id}")
    
    # Verifica prima se l'evento esiste e recupera i dettagli
    with sqlite3.connect(event_buffer.db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT file_name, folder FROM events WHERE id = ?", (event_id,))
        event_data = c.fetchone()
        
        if not event_data:
            raise HTTPException(status_code=404, detail=f"Evento con id {event_id} non trovato")
        
        file_name, folder = event_data
        file_path = os.path.join(folder, file_name)
        
        # Verifica se il file esiste ancora
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {file_path} non trovato")
        
        # Aggiorna lo stato dell'evento a 'processing'
        event_buffer.update_event_status(event_id, 'processing')
    
    # Invia il file al backend
    try:
        import requests
        BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
        BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", f"http://localhost:{BACKEND_PORT}")
        UPLOAD_URL = f"{BACKEND_BASE_URL}/api/document-monitor/upload/"
        
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            resp = requests.post(UPLOAD_URL, files=files, timeout=30)
        
        if resp.status_code == 200:
            info(f"PDF '{file_name}' reinviato al backend con successo.")
            
            # Estrai l'ID del documento dalla risposta
            document_id = None
            try:
                result = resp.json()
                info(f"Risposta completa dal backend: {result}")
                
                # Cerca il document_id in tutte le posizioni possibili
                if 'document_id' in result:
                    document_id = result['document_id']
                elif 'result' in result and isinstance(result['result'], dict) and 'document_id' in result['result']:
                    document_id = result['result']['document_id']
                elif 'workflow_result' in result and isinstance(result['workflow_result'], dict):
                    if 'document_id' in result['workflow_result']:
                        document_id = result['workflow_result']['document_id']
                    elif 'result' in result['workflow_result'] and isinstance(result['workflow_result']['result'], dict):
                        if 'document_id' in result['workflow_result']['result']:
                            document_id = result['workflow_result']['result']['document_id']
                        elif 'id' in result['workflow_result']['result']:
                            document_id = result['workflow_result']['result']['id']
                
                info(f"Document ID estratto: {document_id}")
            except Exception as ex:
                warning(f"Errore nell'estrazione del document_id: {ex}")
            
            # Aggiorna stato: completato
            event_buffer.update_event_status(event_id, 'completed', document_id)
            return {"status": "success", "message": f"Evento {event_id} rielaborato con successo", "document_id": document_id}
        else:
            error_msg = f"HTTP {resp.status_code}: {resp.text}"
            event_buffer.update_event_status(event_id, 'error', None, error_msg)
            return {"status": "error", "message": f"Errore reinvio: {error_msg}"}
    
    except Exception as e:
        error_msg = str(e)
        event_buffer.update_event_status(event_id, 'error', None, error_msg)
        error(f"Errore durante la rielaborazione: {error_msg}")
        return {"status": "error", "message": f"Errore durante la rielaborazione: {error_msg}"}

@app.post("/monitor/remove_folder", tags=["Monitoring"])
def remove_folder(config: FolderPathConfig):
    """
    Rimuove una cartella dal monitoraggio.
    """
    info(f"Comando ricevuto: rimuovi cartella {config.folder_path}")
    
    result = monitor.remove_folder(config.folder_path)
    
    if result:
        return {"status": "success", "message": f"Cartella rimossa: {config.folder_path}"}
    else:
        return {"status": "error", "message": f"Impossibile rimuovere cartella: {config.folder_path}"}

@app.post("/monitor/clean_duplicates", tags=["Maintenance"])
def clean_duplicate_events():
    """
    Elimina eventi duplicati per lo stesso file, mantenendo solo l'evento più recente
    o quello con document_id.
    """
    info(f"Comando ricevuto: pulizia eventi duplicati")
    
    try:
        cleaned_count = event_buffer.clean_duplicate_events()
        return {
            "status": "success", 
            "message": f"Pulizia completata: {cleaned_count} eventi duplicati eliminati"
        }
    except Exception as e:
        error_msg = str(e)
        error(f"Errore durante la pulizia: {error_msg}")
        return {
            "status": "error",
            "message": f"Errore durante la pulizia: {error_msg}"
        }

@app.get("/monitor/file_history/{file_name:path}", tags=["Events"])
def get_file_history(file_name: str):
    """
    Restituisce la storia completa di un file, inclusi tutti gli eventi e stati.
    Utile per debug e per visualizzare la timeline completa di un file.
    """
    info(f"Richiesta storia per file: {file_name}")
    
    try:
        history = event_buffer.get_file_history(file_name)
        return {
            "status": "success", 
            "file_name": file_name,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        error_msg = str(e)
        error(f"Errore nel recupero storia file {file_name}: {error_msg}")
        return {
            "status": "error",
            "message": f"Errore nel recupero storia: {error_msg}"
        }
