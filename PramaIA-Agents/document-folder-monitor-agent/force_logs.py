"""
Script per forzare l'invio di log al LogService dall'agente PDF Monitor.
Simula attività come se fossero generate dall'agente.
"""

import os
import sys
import time
import uuid
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazione dalle variabili d'ambiente
API_KEY = os.getenv("PRAMAIALOG_API_KEY", "pramaiaagents_api_key_123456")

# Nota: questo script ora usa il logger interno dell'agente per inviare i log.
# Non costruisce più direttamente LOG_SERVICE_URL per invii HTTP.


def _get_logger_funcs():
    """Prova ad importare il modulo `logger` dalla cartella `src` dell'agente.
    Restituisce quattro funzioni (info, warning, error, debug). In mancanza del
    modulo, restituisce fallback che scrivono su stdout."""
    src_path = os.path.join(os.path.dirname(__file__), "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    try:
        from logger import info as logger_info, warning as logger_warning, error as logger_error, debug as logger_debug
        return logger_info, logger_warning, logger_error, logger_debug
    except Exception:
        # Fallback minimo: funzioni che stampano su stdout
        def _print_info(msg, details=None, context=None):
            print("[INFO]", msg, json.dumps(details) if details else "", context or "")

        def _print_warning(msg, details=None, context=None):
            print("[WARNING]", msg, json.dumps(details) if details else "", context or "")

        def _print_error(msg, details=None, context=None):
            print("[ERROR]", msg, json.dumps(details) if details else "", context or "")

        def _print_debug(msg, details=None, context=None):
            print("[DEBUG]", msg, json.dumps(details) if details else "", context or "")

        return _print_info, _print_warning, _print_error, _print_debug


# Ottieni le funzioni logger (module-level cache)
logger_info, logger_warning, logger_error, logger_debug = _get_logger_funcs()


def send_log(level, message, details=None, context=None):
    """Invia un log al LogService usando il logger interno (se disponibile).
    Ritorna True se l'operazione è stata tentata, False su errori irreversibili."""
    try:
        mapped = {
            "debug": lambda: logger_debug(message, details=details, context=context),
            "info": lambda: logger_info(message, details=details, context=context),
            "warning": lambda: logger_warning(message, details=details, context=context),
            "error": lambda: logger_error(message, details=details, context=context),
            "critical": lambda: logger_error(message, details=details, context=context),
        }
        func = mapped.get(level.lower(), mapped["info"])
        func()
        # Log di debug locale per confermare l'invio
        try:
            logger_debug(f"Invio log tramite logger interno [{level}]: {message}")
        except Exception:
            print(f"Invio log tramite logger interno [{level}]: {message}")
        return True
    except Exception as e:
        print(f"[force_logs] Impossibile inviare log: {e}")
        return False


def simulate_agent_activity():
    """Simula diverse attività dell'agente"""
    print("=== Simulazione attività agente PDF Monitor ===")

    # Simula avvio agente
    send_log(
        "info",
        "PDF Monitor Agent avviato",
        details={
            "version": "1.3.0-sync",
            "startup_time": time.time()
        },
        context={
            "source": "main.py",
            "function": "startup"
        }
    )
    
    # Simula rilevamento cartelle
    folders = ["D:\\TestPramaIA", "C:\\Users\\fabmi\\AppData\\Local\\Temp\\pdf_monitor_test"]
    send_log(
        "info", 
        f"Rilevate {len(folders)} cartelle monitorate",
        details={
            "folders": folders,
            "autostart_folders": ["D:\\TestPramaIA"]
        },
        context={
            "source": "folder_monitor.py",
            "function": "get_folders"
        }
    )
    
    # Simula rilevamento file
    files = ["Autodichiarazione 1.pdf", "Proposta di Servizi.pdf", "regolamento_uffici_e_servizi.pdf"]
    for file in files:
        send_log(
            "info", 
            f"File rilevato: {file}",
            details={
                "file_name": file,
                "folder": "D:\\TestPramaIA",
                "detection_type": "existing"
            },
            context={
                "source": "folder_monitor.py",
                "function": "_scan_existing_files"
            }
        )
    
    # Simula nuova attività in tempo reale
    send_log(
        "info", 
        "Nuovo file rilevato: test_log_file.txt",
        details={
            "file_name": "test_log_file.txt",
            "relative_path": "test_log_file.txt",
            "full_path": "D:\\TestPramaIA\\test_log_file.txt",
            "event_type": "created"
        },
        context={
            "source": "folder_monitor.py",
            "function": "on_created"
        }
    )
    
    # Simula errore
    send_log(
        "error", 
        "Errore durante l'elaborazione del file",
        details={
            "file_name": "test_log_file.txt",
            "error": "Formato file non supportato: solo PDF sono supportati",
            "action": "upload"
        },
        context={
            "source": "smart_file_handler.py",
            "function": "_send_file_to_backend"
        }
    )
    
    # Simula warning
    send_log(
        "warning", 
        "Cartella temporaneamente non accessibile",
        details={
            "folder": "C:\\Users\\fabmi\\AppData\\Local\\Temp\\pdf_monitor_test",
            "retry_count": 3,
            "next_retry": time.time() + 60
        },
        context={
            "source": "reconciliation_service.py",
            "function": "reconcile_folder"
        }
    )
    
    # Simula attività di sincronizzazione
    send_log(
        "info", 
        "Sincronizzazione completata",
        details={
            "folders_synced": 1,
            "files_added": 1,
            "files_updated": 0, 
            "files_deleted": 0,
            "duration_ms": 1245
        },
        context={
            "source": "reconciliation_service.py",
            "function": "sync_folders"
        }
    )
    
    try:
        from .logger import info as _logger_info
        _logger_info("Simulazione completata: logs inviati al LogService")
    except Exception:
        # Se l'import fallisce (esecuzione standalone), stampiamo su stdout
        print("\n✅ Simulazione completata! Logs inviati al LogService.")
        print("Apri la dashboard del LogService per vedere i logs (URL configurato via BACKEND_URL o PRAMAIALOG_HOST/PORT)")

if __name__ == "__main__":
    simulate_agent_activity()
