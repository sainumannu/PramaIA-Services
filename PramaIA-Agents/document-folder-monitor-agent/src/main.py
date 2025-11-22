import uvicorn
import os
import asyncio

"""
ATTENZIONE:
Avvia il server SOLO con il comando:
    uvicorn src.main:app --reload --port $PLUGIN_DOCUMENT_MONITOR_PORT
    oppure
    uvicorn src.main:app --reload --port $PLUGIN_PDF_MONITOR_PORT (per compatibilità)
Non usare 'python src/main.py' su Windows, altrimenti rischi di avviare più istanze o avere comportamenti inattesi.
Questo file serve solo come entrypoint per uvicorn.
"""
from .control_api import app, monitor
from .unified_file_handler import UnifiedFileHandler
from .reconciliation_service import reconciliation_service, trigger_reconciliation
from .recovery_sync import recovery_sync, update_connection_state, initialize_recovery_sync
from .logger import info, warning, error, debug, flush, close
from .event_buffer import event_buffer

import threading
import time
import requests
import random
import atexit
# Risolvi l'URL del backend con logica CORRETTA:
# 1) BACKEND_URL (se specificato)
# 2) BACKEND_HOST + BACKEND_PORT (il vero backend)
# PRAMAIALOG_HOST è SOLO per il LogService, NON per eventi del backend!
BACKEND_BASE_URL = os.getenv("BACKEND_URL")
if not BACKEND_BASE_URL:
    BACKEND_PORT = os.getenv("BACKEND_PORT") or "8000"
    BACKEND_HOST = os.getenv("BACKEND_HOST") or "localhost"
    BACKEND_BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

PLUGIN_PORT = os.getenv("PLUGIN_DOCUMENT_MONITOR_PORT") or os.getenv("PLUGIN_PDF_MONITOR_PORT") or "8001"
PLUGIN_HOST = os.getenv("PLUGIN_DOCUMENT_MONITOR_HOST") or os.getenv("PLUGIN_PDF_MONITOR_HOST") or "localhost"
PLUGIN_BASE_URL = os.getenv("PLUGIN_DOCUMENT_MONITOR_BASE_URL") or os.getenv("PLUGIN_PDF_MONITOR_BASE_URL") or f"http://{PLUGIN_HOST}:{PLUGIN_PORT}"

SERVER_URL = f"{BACKEND_BASE_URL}/api/document-monitor/clients/register"
CLIENT_ID = os.getenv("PLUGIN_CLIENT_ID") or "document-monitor-001"  # nuovo ID
CLIENT_NAME = os.getenv("PLUGIN_CLIENT_NAME") or "Document Folder Monitor"
CLIENT_ENDPOINT = PLUGIN_BASE_URL


# Configurazione per il meccanismo di retry
MAX_RETRY_ATTEMPTS = 10  # Numero massimo di tentativi iniziali
INITIAL_RETRY_DELAY = 5  # Secondi di attesa iniziale
MAX_RETRY_DELAY = 300    # Massimo ritardo tra i tentativi (5 minuti)
HEARTBEAT_INTERVAL = 60  # Intervallo di heartbeat periodico in secondi

# Stato globale per evitare log duplicati
last_online_state = None

def get_scan_paths():
    try:
        return monitor.get_folders()
    except Exception:
        return []

def try_register(online=True, attempt=1):
    global last_online_state
    """
    Tenta di registrare il client con il server.
    Implementa backoff esponenziale con jitter per evitare "thundering herd"
    """
    payload = {
        "id": CLIENT_ID,
        "name": CLIENT_NAME,
        "endpoint": CLIENT_ENDPOINT,
        "scanPaths": get_scan_paths(),
        "online": online
    }
    
    try:
        # Logga solo se il tentativo è effettivamente necessario
        if last_online_state != online:
            info(f"Tentativo {attempt} di registrazione al server: {SERVER_URL}")
        resp = requests.post(SERVER_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            if last_online_state != online:
                info(f"✅ Stato client inviato: online={online}")
            last_online_state = online
            # Aggiorna stato connessione
            update_connection_state(True)
            return True
        else:
            error(
                f"❌ Errore invio stato client: {resp.status_code} {resp.text}",
                details={"status_code": resp.status_code, "response": resp.text}
            )
            # Aggiorna stato connessione
            update_connection_state(False)
            return False
    except Exception as e:
        error(f"❌ Connessione al server fallita: {e}")
        # Aggiorna stato connessione
        update_connection_state(False)
        return False

def registration_loop():
    """
    Loop di registrazione con backoff esponenziale e jitter.
    Continua a tentare fino al successo, poi passa a heartbeat periodici.
    """
    attempt = 1
    registered = False
    
    # Fase 1: Registrazione iniziale con backoff esponenziale
    while attempt <= MAX_RETRY_ATTEMPTS and not registered:
        registered = try_register(online=True, attempt=attempt)
        
        if registered:
            info(f"✅ Registrazione riuscita al tentativo {attempt}")
            break
            
        # Calcola il ritardo con backoff esponenziale e jitter
        delay = min(INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
        # Aggiungi jitter (±20%)
        jitter = random.uniform(0.8, 1.2)
        adjusted_delay = delay * jitter
        
        info(f"Riprovo tra {adjusted_delay:.1f} secondi... (tentativo {attempt}/{MAX_RETRY_ATTEMPTS})")
        time.sleep(adjusted_delay)
        attempt += 1
    
    # Se dopo MAX_RETRY_ATTEMPTS non abbiamo ancora successo, continuiamo con intervalli più lunghi
    if not registered:
        warning(f"⚠️ Non è stato possibile registrarsi dopo {MAX_RETRY_ATTEMPTS} tentativi. Continuo con intervalli più lunghi.")
        
        while not registered:
            time.sleep(MAX_RETRY_DELAY)
            registered = try_register(online=True, attempt=attempt)
            attempt += 1
            
            if registered:
                info(f"✅ Registrazione riuscita al tentativo {attempt} dopo lunga attesa")
                break
    
    # Fase 2: Heartbeat periodico per mantenere la registrazione
    info(f"Avvio heartbeat periodico ogni {HEARTBEAT_INTERVAL} secondi")
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        if not try_register(online=True):
            warning("⚠️ Heartbeat fallito, riprovo...")
            # Se il heartbeat fallisce, facciamo 3 tentativi rapidi
            for i in range(3):
                time.sleep(5)
                if try_register(online=True):
                    info(f"✅ Heartbeat ripristinato al tentativo {i+1}")
                    break

def start_registration_thread():
    """Avvia il thread di registrazione"""
    info("Avvio thread di registrazione")
    t = threading.Thread(target=registration_loop, daemon=True)
    t.start()
    return t

import atexit
# Avvia la registrazione automatica all'avvio
registration_thread = start_registration_thread()

# Invio stato offline al server alla chiusura del plugin
def send_offline():
    info("Chiusura in corso, invio stato offline...")
    try_register(online=False)
    
atexit.register(send_offline)

# --- Endpoint per forzare la sincronizzazione dal server ---
from fastapi import Request
@app.post("/monitor/force-sync")
async def force_sync(request: Request):
    """
    Endpoint chiamato dal server per forzare la trasmissione degli eventi aggiornati.
    """
    # Qui dovresti implementare la logica per inviare gli eventi non ancora trasmessi
    # Ad esempio: chiama una funzione che invia gli eventi bufferizzati al backend
    send_events_to_backend()
    info("Comando ricevuto dal server: richiesta di sincronizzazione forzata.")
    return {"status": "sync_triggered"}

# --- Endpoint per forzare la riconciliazione di una cartella ---
from fastapi import Query
@app.post("/monitor/reconcile")
async def force_reconcile(folder_path: str = Query(..., description="Percorso della cartella da riconciliare")):
    """
    Endpoint per forzare manualmente la riconciliazione di una cartella.
    Utile per risolvere problemi di sincronizzazione.
    """
    info(f"Comando ricevuto: richiesta di riconciliazione per {folder_path}")
    try:
        result = await trigger_reconciliation(folder_path)
        if result['success']:
            stats = result.get('stats', {})
            return {
                "status": "success", 
                "message": f"Riconciliazione completata. File aggiunti: {stats.get('files_added', 0)}, "
                           f"aggiornati: {stats.get('files_updated', 0)}, "
                           f"eliminati: {stats.get('files_deleted', 0)}",
                "details": result
            }
        else:
            return {"status": "error", "message": f"Riconciliazione fallita: {result.get('error', 'Errore sconosciuto')}", "details": result}
    except Exception as e:
        error(f"Errore durante la riconciliazione di {folder_path}: {e}")
        return {"status": "error", "message": f"Errore: {str(e)}"}

# --- Endpoint per forzare una riregistrazione manuale ---
@app.post("/monitor/register")
async def force_register():
    """
    Endpoint per forzare manualmente la registrazione con il server.
    Utile per risolvere problemi di connessione.
    """
    success = try_register(online=True)
    if success:
        return {"status": "success", "message": "Registrazione manuale completata"}
    else:
        return {"status": "error", "message": "Registrazione manuale fallita"}

# --- Endpoint per controllare stato sincronizzazione ---
from datetime import datetime
from .recovery_sync import connection_state
@app.get("/monitor/sync-status")
async def get_sync_status():
    """
    Endpoint per ottenere lo stato del sistema di sincronizzazione.
    """
    try:
        # Stato connessione
        conn_status = {
            "connected": False,
            "consecutive_successes": 0,
            "consecutive_failures": 0,
            "last_connected": None,
            "last_disconnected": None,
            "disconnection_duration": None
        }
        
        if hasattr(connection_state, "connected"):
            conn_status["connected"] = connection_state.connected
            conn_status["consecutive_successes"] = connection_state.consecutive_successes
            conn_status["consecutive_failures"] = connection_state.consecutive_failures
            
            if connection_state.last_connected:
                conn_status["last_connected"] = connection_state.last_connected.isoformat()
                
            if connection_state.last_disconnected:
                conn_status["last_disconnected"] = connection_state.last_disconnected.isoformat()
                
            # Durata disconnessione
            disconnection_duration = connection_state.get_disconnection_duration()
            if disconnection_duration:
                conn_status["disconnection_duration"] = str(disconnection_duration)
                
        # Stato riconciliazione
        recon_status = {
            "running": False,
            "last_sync": {},
            "sync_interval": 0,
            "active_folders": []  # Aggiungiamo questa informazione
        }
        
        if reconciliation_service:
            recon_status["running"] = reconciliation_service.running
            recon_status["sync_interval"] = reconciliation_service.sync_interval
            
            # Formatta last_sync
            for folder, timestamp in reconciliation_service.last_sync.items():
                if isinstance(timestamp, datetime):
                    recon_status["last_sync"][folder] = timestamp.isoformat()
            
            # Aggiungi informazioni sulle cartelle attivamente monitorate
            try:
                active_folders = monitor.get_active_folders() if hasattr(monitor, "get_active_folders") else []
                recon_status["active_folders"] = active_folders
            except Exception as e:
                error(f"Errore nel recupero delle cartelle attive: {e}")
                    
        # Stato recovery sync
        recovery_status = {
            "enabled": False,
            "auto_reconcile": False
        }
        
        if recovery_sync:
            recovery_status["enabled"] = recovery_sync.enabled
            recovery_status["auto_reconcile"] = recovery_sync.auto_reconcile
            
        return {
            "status": "success",
            "connection": conn_status,
            "reconciliation": recon_status,
            "recovery": recovery_status
        }
        
    except Exception as e:
        error(f"Errore nel recupero dello stato di sincronizzazione: {e}")
        return {"status": "error", "message": f"Errore: {str(e)}"}
        
# --- Endpoint per test di disconnessione simulata ---
@app.post("/monitor/offline")
async def force_offline():
    """
    Endpoint per simulare una disconnessione (solo per test).
    """
    info("Test: Simulazione disconnessione")
    try_register(online=False)
    # Forza stato disconnesso
    update_connection_state(False)
    return {"status": "success", "message": "Disconnessione simulata attivata"}

# Funzione per avviare il monitoraggio delle cartelle configurate con autostart
def start_autostart_monitoring():
    """
    Funzione per avviare il monitoraggio delle cartelle autostart.
    Versione thread-safe che evita problemi con handle
    """
    info("Avvio monitoraggio cartelle autostart...")
    try:
        num_started = monitor.start_autostart_folders()
        if num_started > 0:
            info(f"✅ Avviate {num_started} cartelle con autostart")
        else:
            info("ℹ️ Nessuna cartella autostart configurata")
    except Exception as e:
        error(f"❌ Errore durante l'avvio delle cartelle autostart: {e}")

# Avvia l'autostart all'avvio del plugin
def trigger_autostart():
    # Attendiamo che l'app sia completamente avviata
    time.sleep(5)
    start_autostart_monitoring()

# Avvia l'autostart all'avvio del plugin
autostart_timer = threading.Timer(5.0, trigger_autostart)
autostart_timer.daemon = True
autostart_timer.start()

# Funzione per avviare il servizio di riconciliazione
@app.on_event("startup")
async def startup_reconciliation_service():
    """Avvia il servizio di riconciliazione all'avvio dell'applicazione"""
    info("Avvio servizio di riconciliazione...")
    try:
        await reconciliation_service.start()
        info("✅ Servizio di riconciliazione avviato con successo")
        
        # Inizializza recovery sync con servizio di riconciliazione
        initialize_recovery_sync(reconciliation_service)
        info("✅ Servizio recovery sync inizializzato")
    except Exception as e:
        error(f"❌ Errore durante l'avvio del servizio di riconciliazione: {e}")

# Funzione per fermare il servizio di riconciliazione
@app.on_event("shutdown")
async def shutdown_reconciliation_service():
    """Ferma il servizio di riconciliazione alla chiusura dell'applicazione"""
    info("Arresto servizio di riconciliazione...")
    try:
        # Disabilita recovery sync
        if recovery_sync:
            recovery_sync.disable()
            info("✅ Servizio recovery sync disabilitato")
            
        # Ferma servizio riconciliazione
        await reconciliation_service.stop()
        info("✅ Servizio di riconciliazione arrestato con successo")
        
        # Ferma il cleaner del database hash
        from .hash_db_cleaner import hash_db_cleaner
        hash_db_cleaner.stop()
        info("✅ Cleaner del database hash arrestato")
    except Exception as e:
        error(f"❌ Errore durante l'arresto dei servizi: {e}")

# --- Endpoint per stato del monitor ---
@app.get("/monitor/status")
async def monitor_status():
    """
    Endpoint per verificare lo stato del monitor.
    """
    return {
        "status": "running",
        "folders": monitor.get_folders() if hasattr(monitor, "get_folders") else [],
        "version": "1.4.0-document-monitor"
    }

# --- Endpoint per pulizia manuale del database hash ---
@app.post("/monitor/cleanup-hash-db")
async def cleanup_hash_db():
    """
    Endpoint per forzare manualmente la pulizia del database degli hash.
    """
    try:
        from .hash_db_cleaner import hash_db_cleaner
        removed_count = hash_db_cleaner.cleanup_hash_database()
        return {
            "status": "success",
            "message": f"Pulizia completata. Rimossi {removed_count} record obsoleti."
        }
    except Exception as e:
        error(f"Errore durante la pulizia del database hash: {e}")
        return {
            "status": "error",
            "message": f"Errore durante la pulizia: {str(e)}"
        }

# --- Endpoint per scansione completa di tutti i file ---
@app.post("/monitor/rescan_all")
async def rescan_all_monitored_folders():
    """
    Esegue una scansione completa di tutte le cartelle monitorate e genera eventi 'created' per tutti i file PDF trovati, anche se già presenti.
    """
    from .event_buffer import event_buffer
    
    try:
        info("[LOG] Ricevuta richiesta di scansione completa di tutti i file")
        
        # Verifica che monitor sia inizializzato correttamente
        if not hasattr(monitor, 'get_folders') or not callable(monitor.get_folders):
            raise AttributeError("L'oggetto monitor non ha il metodo get_folders")
        
        folders = monitor.get_folders()
        info(f"[LOG] Cartelle da scansionare: {folders}")
        
        count = 0
        for folder in folders:
            if not os.path.exists(folder):
                warning(f"[WARN] La cartella {folder} non esiste o non è accessibile")
                continue
                
            info(f"[LOG] Scansione in corso per: {folder}")
            for root, dirs, files in os.walk(folder):
                for file in files:
                    # Lista di estensioni di documenti supportati
                    supported_extensions = ['.pdf', '.doc', '.docx', '.odt', '.txt', '.xls', '.xlsx', '.ods']
                    if any(file.lower().endswith(ext) for ext in supported_extensions):
                        file_path = os.path.join(root, file)
                        event_buffer.add_event('created', file, root)
                        count += 1
                        
        info(f"[LOG] Scansione completata: generati {count} eventi")
        return {"status": "success", "message": f"Scansione completata: {count} eventi generati"}
    except Exception as e:
        import traceback
        error(f"[ERROR] Errore durante la scansione completa: {str(e)}")
        error(traceback.format_exc())
        return {"status": "error", "message": f"Errore durante la scansione completa: {str(e)}"}

# --- Worker per processare ed inviare eventi dal buffer ---
def event_sender_worker():
    """
    Worker che processa continuamente gli eventi dal buffer e li invia al backend.
    Gira in background e processa eventi con status 'aggiunto' o 'pending'.
    """
    import sqlite3
    from pathlib import Path
    
    # Path corretto al database nella directory del monitor agent
    db_path = Path(__file__).parent.parent / "event_buffer.db"
    
    while True:
        try:
            # Aspetta 5 secondi tra un ciclo e l'altro
            time.sleep(5)
            if not db_path.exists():
                continue
                
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Cerca eventi da processare
            cursor.execute("""
                SELECT id, event_type, file_name, folder, metadata
                FROM events 
                WHERE status IN ('aggiunto', 'pending') AND sent = 0
                LIMIT 10
            """)
            
            events = cursor.fetchall()
            conn.close()
            
            if not events:
                continue
            
            # Processa ogni evento
            for event in events:
                event_id, event_type, file_name, folder, metadata = event
                file_path = os.path.join(folder, file_name)
                
                # Verifica che il file esista ancora
                if not os.path.exists(file_path):
                    # Marca evento come failed
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("UPDATE events SET status = 'failed', error_message = ? WHERE id = ?",
                                 ("File non trovato", event_id))
                    conn.commit()
                    conn.close()
                    warning(f"[WORKER] File non trovato: {file_name}")
                    continue
                
                # Invia al backend
                try:
                    backend_base = os.getenv("BACKEND_URL")
                    if not backend_base:
                        backend_host = os.getenv("BACKEND_HOST", "localhost")
                        backend_port = os.getenv("BACKEND_PORT", "8000")
                        backend_base = f"http://{backend_host}:{backend_port}"
                    
                    upload_url = f"{backend_base}/api/document-monitor/upload/"
                    
                    with open(file_path, "rb") as f:
                        files = {"file": (file_name, f)}
                        data = {
                            "action": event_type,
                            "full_path": file_path,
                            "relative_path": file_name
                        }
                        
                        resp = requests.post(upload_url, files=files, data=data, timeout=30)
                    
                    if resp.status_code == 200:
                        # Successo - marca come inviato
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute("UPDATE events SET status = 'completed', sent = 1 WHERE id = ?", (event_id,))
                        conn.commit()
                        conn.close()
                        info(f"[WORKER] Evento {event_id} inviato con successo: {file_name}")
                    else:
                        # Errore - marca come failed
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute("UPDATE events SET status = 'failed', error_message = ? WHERE id = ?",
                                     (f"HTTP {resp.status_code}", event_id))
                        conn.commit()
                        conn.close()
                        error(f"[WORKER] Errore invio evento {event_id}: HTTP {resp.status_code}")
                        
                except Exception as e:
                    # Errore - marca come failed
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("UPDATE events SET status = 'failed', error_message = ? WHERE id = ?",
                                 (str(e)[:200], event_id))
                    conn.commit()
                    conn.close()
                    error(f"[WORKER] Errore invio evento {event_id}: {e}")
                    
        except Exception as e:
            error(f"[WORKER] Errore nel worker eventi: {e}")
            time.sleep(10)  # Aspetta più a lungo in caso di errore

# --- Job di manutenzione per pulizia eventi ---
def event_maintenance_job():
    """
    Job periodico per la pulizia degli eventi duplicati e aggiornamento degli eventi bloccati.
    Viene eseguito ogni 15 minuti per mantenere pulito il database degli eventi.
    """
    while True:
        try:
            # Aspetta 15 minuti prima di eseguire la manutenzione
            time.sleep(900)  # 900 secondi = 15 minuti
            
            info("[MANUTENZIONE] Avvio pulizia eventi duplicati...")
            duplicates_removed = event_buffer.clean_duplicate_events()
            info(f"[MANUTENZIONE] Pulizia completata: rimossi {duplicates_removed} eventi duplicati")
            
            info("[MANUTENZIONE] Verifica eventi bloccati...")
            stalled_updated = event_buffer.auto_update_stalled_events(max_age_hours=2)
            info(f"[MANUTENZIONE] Aggiornati {stalled_updated} eventi bloccati")
            
        except Exception as e:
            error(f"[ERROR] Errore durante il job di manutenzione degli eventi: {str(e)}")
            # Continua comunque con il prossimo ciclo
            continue

# Avvia il worker per processare ed inviare eventi
sender_thread = threading.Thread(target=event_sender_worker, daemon=True)
sender_thread.start()
info("[STARTUP] Event sender worker avviato")

# Avvia il job di manutenzione degli eventi in un thread separato
maintenance_thread = threading.Thread(target=event_maintenance_job, daemon=True)
maintenance_thread.start()
info("[STARTUP] Event maintenance job avviato")

# Avvia il job di pulizia del database hash
from .hash_db_cleaner import hash_db_cleaner
hash_db_cleaner.start()

# Funzione per avviare il monitoraggio delle cartelle configurate con autostart
def start_autostart_monitoring():
    info("[AUTOSTART] Avvio monitoraggio cartelle autostart...")
    try:
        num_started = monitor.start_autostart_folders()
        if num_started > 0:
            info(f"[AUTOSTART] Avviate {num_started} cartelle con autostart")
        else:
            info("[AUTOSTART] Nessuna cartella autostart configurata")
    except Exception as e:
        error(f"[AUTOSTART] Errore durante l'avvio delle cartelle autostart: {e}")

# Avvia il monitoraggio delle cartelle autostart dopo un breve ritardo
def delayed_autostart():
    # Aspetta 5 secondi per dare tempo al sistema di inizializzarsi
    time.sleep(5)
    start_autostart_monitoring()

# Avvia un thread separato per l'autostart
autostart_thread = threading.Thread(target=delayed_autostart, daemon=True)
autostart_thread.start()
info("[STARTUP] Autostart thread avviato")

# Qui potrai aggiungere altre route FastAPI (es: /semantic-search, /events, ...)

if __name__ == "__main__":
    # Disabilitato reload=True per evitare continui riavvii e messaggi "change detected"
    uvicorn.run(
        "src.main:app", 
        host=os.getenv("PLUGIN_DOCUMENT_MONITOR_HOST", "0.0.0.0") or os.getenv("PLUGIN_PDF_MONITOR_HOST", "0.0.0.0"), 
        port=int(PLUGIN_PORT), 
        reload=False  # Modificato da True a False
    )
