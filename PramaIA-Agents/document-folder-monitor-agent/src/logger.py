"""
Modulo di logging avanzato per Document Monitor Agent.

Fornisce un'interfaccia unificata per il logging
che funziona sia con PramaIA-LogService che in modalità locale.

Configurazione via variabili d'ambiente:
- PRAMAIALOG_API_KEY: Chiave API per il LogService
- PRAMAIALOG_HOST: Host del LogService (default: localhost)
- PRAMAIALOG_PORT: Porta del LogService (default: 8081)
- PRAMAIALOG_PROTOCOL: Protocollo da utilizzare (default: http://)
- PRAMAIALOG_ENABLED: Abilita/disabilita l'integrazione (default: true)
"""

import os
import logging
import sys
import importlib.util
import time
import hashlib
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

# Dizionario globale per tenere traccia degli eventi recenti per la deduplicazione
_recent_modification_events = {}

# Carica variabili d'ambiente: tenta prima la .env della cartella dell'agente, poi la .env nella root del repo,
# poi fallback al comportamento di load_dotenv() che cerca nella CWD. Questo evita che l'import del modulo
# non trovi PRAMAIALOG_API_KEY quando viene eseguito da un'altra cartella (es. workspace root).
try:
    # cartella src
    _this_dir = os.path.abspath(os.path.dirname(__file__))
    # cartella agente (..)
    _agent_root = os.path.abspath(os.path.join(_this_dir, '..'))
    # root del repository (due livelli sopra agent_root)
    _repo_root = os.path.abspath(os.path.join(_agent_root, '..'))

    _agent_env = os.path.join(_agent_root, '.env')
    _repo_env = os.path.join(_repo_root, '.env')

    if os.path.exists(_agent_env):
        load_dotenv(_agent_env)
        # user local logger after it's configured; for now use logging.info via root logger
        logging.getLogger().info(f"[logger] load_dotenv: loaded {_agent_env}")
    elif os.path.exists(_repo_env):
        load_dotenv(_repo_env)
        logging.getLogger().info(f"[logger] load_dotenv: loaded {_repo_env}")
    else:
        # fallback generico
        load_dotenv()
except Exception:
    # se qualcosa va storto nella risoluzione dei path, usa il fallback semplice
    load_dotenv()

# Configurazione logging locale
logging.basicConfig(
    level=logging.DEBUG,  # Livello DEBUG per vedere più dettagli
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# AGGIUNGI IL LIVELLO CUSTOM LIFECYCLE al logging di Python
LIFECYCLE_LEVEL_NUM = 25  # Tra INFO (20) e WARNING (30)
logging.addLevelName(LIFECYCLE_LEVEL_NUM, "LIFECYCLE")

def lifecycle_log(self, message, *args, **kwargs):
    """Metodo per loggare a livello LIFECYCLE."""
    if self.isEnabledFor(LIFECYCLE_LEVEL_NUM):
        self._log(LIFECYCLE_LEVEL_NUM, message, args, **kwargs)

# Aggiungi il metodo al logger
logging.Logger.lifecycle_log = lifecycle_log

# Crea un logger per l'applicazione
_local_logger = logging.getLogger("document-monitor-agent")
_local_logger.setLevel(logging.DEBUG)  # Assicura che il logger locale accetti messaggi DEBUG

# Variabili globali per il LogService
LOGSERVICE_AVAILABLE = False
PRAMAIALOGGER = None
LOGSERVICE_HOST = None  # Variabile globale per l'host
DEFAULT_HOST = "localhost"  # Host predefinito per il fallback
DEFAULT_PROTOCOL = "http://"  # Protocollo predefinito
DEFAULT_PORT = "8081"  # Porta predefinita

# Carica il modulo pramaialog
try:
    _local_logger.info("Inizializzazione connessione LogService...")

    # Prova a importare il package pramaialog se installato
    if importlib.util.find_spec("pramaialog"):
        _local_logger.info("Modulo pramaialog trovato nel path")
        from pramaialog import PramaIALogger, LogLevel, LogProject
    else:
        # Fallback: prova a caricare pramaialog.py dal repository (quando non è installato)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        possible_path = os.path.join(repo_root, 'PramaIA-LogService', 'clients', 'python', 'pramaialog.py')
        if os.path.exists(possible_path):
            _local_logger.info(f"pramaialog non installato: provo a caricare da {possible_path}")
            spec = importlib.util.spec_from_file_location('pramaialog', possible_path)
            pr_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pr_module)
            PramaIALogger = getattr(pr_module, 'PramaIALogger')
            LogLevel = getattr(pr_module, 'LogLevel')
            LogProject = getattr(pr_module, 'LogProject')
        else:
            _local_logger.warning('Modulo pramaialog non trovato nel path né nella cartella clients/python del repo')
            raise ImportError('pramaialog non disponibile')

    # Ottieni configurazione dalle variabili d'ambiente
    api_key = os.getenv("PRAMAIALOG_API_KEY")
    host = os.getenv("PRAMAIALOG_HOST")
    port = os.getenv("PRAMAIALOG_PORT", DEFAULT_PORT)  # Porta predefinita se non specificata
    protocol = os.getenv("PRAMAIALOG_PROTOCOL", DEFAULT_PROTOCOL)  # Protocollo predefinito
    enabled = os.getenv("PRAMAIALOG_ENABLED", "true").lower() == "true"

    # Costruisci l'URL completo, assicurandosi che non ci siano URL hardcoded
    if host:
        if not host.startswith(("http://", "https://")):
            host = f"{protocol}{host}"  # Aggiungi il protocollo se non presente
        if ":" not in host.split("/")[-1]:  # Se non c'è già una porta nell'URL
            host = f"{host}:{port}"  # Aggiungi la porta
    else:
        # Fallback se host non è specificato
        host = f"{protocol}{DEFAULT_HOST}:{port}"

    # Imposta la variabile globale
    LOGSERVICE_HOST = host

    _local_logger.info(f"Configurazione LogService: host={host}, api_key={'***' if api_key else 'MISSING'}, enabled={enabled}, port={port}")

    if api_key and enabled:
        try:
            # Inizializza il client LogService
            PRAMAIALOGGER = PramaIALogger(
                api_key=api_key,
                project=LogProject.AGENTS,
                module="document-folder-monitor-agent",
                host=host
            )

            LOGSERVICE_AVAILABLE = True
            _local_logger.info(f"✅ PramaIA LogService inizializzato con successo - host: {host}")

            # Prova a inviare un log di test
            try:
                PRAMAIALOGGER.info(
                    "Document Monitor Agent avviato - LogService connesso",
                    details={
                        "timestamp": time.time(),
                        "host": host,
                        "initialization": "startup"
                    }
                )
                _local_logger.info("✅ Invio log di test riuscito!")
            except Exception as test_error:
                _local_logger.error(f"❌ Errore invio log di test: {str(test_error)}")
        except Exception as client_error:
            _local_logger.error(f"❌ Errore inizializzazione LogService: {str(client_error)}", exc_info=True)
    else:
        if not api_key:
            _local_logger.warning("❌ API key per LogService non trovata - usa PRAMAIALOG_API_KEY nel file .env")
        if not enabled:
            _local_logger.info("LogService disabilitato da configurazione (PRAMAIALOG_ENABLED=false)")
except Exception as import_error:
    _local_logger.error(f"❌ Errore importazione/inizializzazione LogService: {str(import_error)}", exc_info=True)

def debug(message: str, details: Optional[Dict[str, Any]] = None, 
          context: Optional[Dict[str, Any]] = None):
    """Log di livello DEBUG"""
    # Logging locale (sempre attivo)
    local_message = message
    if details:
        local_message = f"{message} - Details: {details}"
    _local_logger.debug(local_message)
    
    # Invia al LogService se disponibile
    if LOGSERVICE_AVAILABLE and PRAMAIALOGGER:
        try:
            PRAMAIALOGGER.debug(message, details=details, context=context)
        except Exception as e:
            _local_logger.error(f"❌ Errore invio log DEBUG a LogService: {str(e)}")

def info(message: str, details: Optional[Dict[str, Any]] = None, 
         context: Optional[Dict[str, Any]] = None):
    """Log di livello INFO"""
    # Logging locale (sempre attivo)
    local_message = message
    if details:
        local_message = f"{message} - Details: {details}"
    _local_logger.info(local_message)
    
    # Invia al LogService se disponibile
    if LOGSERVICE_AVAILABLE and PRAMAIALOGGER:
        try:
            _local_logger.debug(f"Invio log INFO a LogService: {message}")
            result = PRAMAIALOGGER.info(message, details=details, context=context)
            _local_logger.debug(f"Log INFO inviato con successo: {result}")
        except Exception as e:
            _local_logger.error(f"❌ Errore invio log INFO a LogService: {str(e)}")

def warning(message: str, details: Optional[Dict[str, Any]] = None, 
           context: Optional[Dict[str, Any]] = None):
    """Log di livello WARNING"""
    # Logging locale (sempre attivo)
    local_message = message
    if details:
        local_message = f"{message} - Details: {details}"
    _local_logger.warning(local_message)
    
    # Invia al LogService se disponibile
    if LOGSERVICE_AVAILABLE and PRAMAIALOGGER:
        try:
            PRAMAIALOGGER.warning(message, details=details, context=context)
        except Exception as e:
            _local_logger.error(f"❌ Errore invio log WARNING a LogService: {str(e)}")

def error(message: str, details: Optional[Dict[str, Any]] = None, 
         context: Optional[Dict[str, Any]] = None):
    """Log di livello ERROR"""
    # Logging locale (sempre attivo)
    local_message = message
    if details:
        local_message = f"{message} - Details: {details}"
    _local_logger.error(local_message)
    
    # Invia al LogService se disponibile
    if LOGSERVICE_AVAILABLE and PRAMAIALOGGER:
        try:
            PRAMAIALOGGER.error(message, details=details, context=context)
        except Exception as e:
            _local_logger.error(f"❌ Errore invio log ERROR a LogService: {str(e)}")

def critical(message: str, details: Optional[Dict[str, Any]] = None, 
            context: Optional[Dict[str, Any]] = None):
    """Log di livello CRITICAL"""
    # Logging locale (sempre attivo)
    local_message = message
    if details:
        local_message = f"{message} - Details: {details}"
    _local_logger.critical(local_message)
    
    # Invia al LogService se disponibile
    if LOGSERVICE_AVAILABLE and PRAMAIALOGGER:
        try:
            PRAMAIALOGGER.critical(message, details=details, context=context)
        except Exception as e:
            _local_logger.error(f"❌ Errore invio log CRITICAL a LogService: {str(e)}")

def lifecycle(message: str, details: Optional[Dict[str, Any]] = None, 
             context: Optional[Dict[str, Any]] = None):
    """
    Log specifico per tracciare eventi del ciclo di vita dei documenti.
    
    Questo livello di log è pensato specificamente per tenere traccia degli eventi 
    che riguardano il ciclo di vita dei documenti, come creazione, modifica, cancellazione, 
    upload al backend, rilevamento duplicati, ecc.
    
    Args:
        message: Il messaggio del log
        details: Dizionario con dettagli aggiuntivi
        context: Contesto dell'evento
    """
    # Sistema di deduplicazione per lifecycle
    global _recent_modification_events
    
    # Crea una chiave univoca per questo evento basata sul messaggio e sui dettagli principali
    event_key = message
    
    # Aggiungi identificatori chiave dai dettagli, se presenti
    if details:
        if 'document_id' in details:
            event_key += f":{details['document_id']}"
        if 'file_path' in details:
            event_key += f":{details['file_path']}"
        if 'file_name' in details:
            event_key += f":{details['file_name']}"
        if 'lifecycle_event' in details:
            event_key += f":{details['lifecycle_event']}"
    
    event_hash = hashlib.md5(event_key.encode()).hexdigest()
    
    # Verifica se questo evento è già stato registrato di recente
    current_time = time.time()
    if event_hash in _recent_modification_events:
        last_time = _recent_modification_events[event_hash]
        # Se l'evento è stato registrato negli ultimi 2 secondi, lo ignoriamo
        if current_time - last_time < 2.0:
            _local_logger.debug(f"Ignorato evento duplicato lifecycle: {event_key} (entro 2 secondi)")
            return None
    
    # Aggiorna il timestamp dell'ultimo evento
    _recent_modification_events[event_hash] = current_time
    
    # Pulisci il dizionario rimuovendo eventi più vecchi di 10 secondi
    _recent_modification_events = {
        k: v for k, v in _recent_modification_events.items() 
        if current_time - v < 10.0
    }
    
    # Non modifichiamo il messaggio originale per l'invio ai client esterni
    original_message = message
    
    # Aggiungi automaticamente un marker al messaggio PER IL LOG LOCALE
    marked_message = f"🔄 [LIFECYCLE] {message}"
    
    # Crea un messaggio locale con un formato che evidenzia che si tratta di un log del ciclo di vita
    local_message = marked_message
    if details:
        local_message = f"{marked_message} - Details: {details}"
    
    # Log locale - usa il livello LIFECYCLE custom
    local_message = f"🔄 {message}"
    if details:
        local_message = f"{local_message} - Details: {details}"
    _local_logger.log(LIFECYCLE_LEVEL_NUM, local_message)
    
    # Invia al LogService usando il metodo lifecycle() dedicato
    if LOGSERVICE_AVAILABLE and PRAMAIALOGGER:
        try:
            # Prepara i dettagli - copia per non modificare l'originale
            lifecycle_details = {}
            if details:
                lifecycle_details.update(details)
            
            # Se non c'è già un lifecycle_event, aggiungiamolo
            if "lifecycle_event" not in lifecycle_details:
                import re
                event_match = re.search(r'\b([A-Z_]+)\b', message)
                lifecycle_details["lifecycle_event"] = event_match.group(1) if event_match else "GENERIC_EVENT"
            
            # Usa il metodo lifecycle() nativo del client che gestisce tutto correttamente
            PRAMAIALOGGER.lifecycle(original_message, details=lifecycle_details, context=context)
            
        except Exception as e:
            _local_logger.error(f"❌ Errore invio log LIFECYCLE a LogService: {str(e)}")
            
    # Return None per compatibilità con le chiamate esistenti
    return None
            
    # Return None per compatibilità con le chiamate esistenti
    return None

# Funzioni specializzate per tracciare eventi del ciclo di vita dei documenti
def document_detected(document_id: str, path: str, details: Optional[Dict[str, Any]] = None, 
                   context: Optional[Dict[str, Any]] = None):
    """Traccia il rilevamento di un nuovo documento."""
    complete_details = {
        "document_id": document_id,
        "file_path": path,
        "lifecycle_event": "document_detected"
    }
    if details:
        complete_details.update(details)
    
    return lifecycle(
        f"Documento rilevato: {document_id}, percorso: {path}",
        details=complete_details,
        context=context
    )

def document_modified(document_id: str, path: str, modification_type: str, details: Optional[Dict[str, Any]] = None, 
                   context: Optional[Dict[str, Any]] = None):
    """Traccia una modifica a un documento (creato, aggiornato, eliminato, rinominato)."""
    # Utilizziamo il dizionario globale per tenere traccia degli eventi recenti
    global _recent_modification_events
    
    # Crea una chiave univoca per questo evento
    event_key = f"{document_id}:{path}:{modification_type}"
    event_hash = hashlib.md5(event_key.encode()).hexdigest()
    
    # Verifica se questo evento è già stato registrato di recente
    current_time = time.time()
    if event_hash in _recent_modification_events:
        last_time = _recent_modification_events[event_hash]
        # Se l'evento è stato registrato negli ultimi 2 secondi, lo ignoriamo
        if current_time - last_time < 2.0:
            _local_logger.debug(f"Ignorato evento duplicato document_modified: {event_key} (entro 2 secondi)")
            return None
    
    # Aggiorna il timestamp dell'ultimo evento
    _recent_modification_events[event_hash] = current_time
    
    # Pulisci il dizionario rimuovendo eventi più vecchi di 10 secondi
    _recent_modification_events = {
        k: v for k, v in _recent_modification_events.items() 
        if current_time - v < 10.0
    }
    
    # Procedi con il logging dell'evento
    complete_details = {
        "document_id": document_id,
        "file_path": path,
        "modification_type": modification_type,
        "lifecycle_event": "document_modified"
    }
    if details:
        complete_details.update(details)
    
    return lifecycle(
        f"Documento modificato ({modification_type}): {document_id}, percorso: {path}",
        details=complete_details,
        context=context
    )

def document_transmitted(document_id: str, target_system: str, status: str, details: Optional[Dict[str, Any]] = None, 
                      context: Optional[Dict[str, Any]] = None):
    """Traccia la trasmissione di un documento a un altro sistema."""
    complete_details = {
        "document_id": document_id,
        "target_system": target_system,
        "status": status,
        "lifecycle_event": "document_transmitted"
    }
    if details:
        complete_details.update(details)
    
    return lifecycle(
        f"Documento trasmesso a {target_system}: {document_id}, stato: {status}",
        details=complete_details,
        context=context
    )

def document_processed(document_id: str, processor_id: str, status: str, details: Optional[Dict[str, Any]] = None, 
                     context: Optional[Dict[str, Any]] = None):
    """Traccia l'elaborazione di un documento da parte di un processore."""
    complete_details = {
        "document_id": document_id,
        "processor_id": processor_id,
        "status": status,
        "lifecycle_event": "document_processed"
    }
    if details:
        complete_details.update(details)
    
    return lifecycle(
        f"Documento elaborato da {processor_id}: {document_id}, stato: {status}",
        details=complete_details,
        context=context
    )

def document_stored(document_id: str, storage_system: str, status: str, details: Optional[Dict[str, Any]] = None, 
                  context: Optional[Dict[str, Any]] = None):
    """Traccia l'archiviazione di un documento in un sistema di storage."""
    complete_details = {
        "document_id": document_id,
        "storage_system": storage_system,
        "status": status,
        "lifecycle_event": "document_stored"
    }
    if details:
        complete_details.update(details)
    
    return lifecycle(
        f"Documento archiviato in {storage_system}: {document_id}, stato: {status}",
        details=complete_details,
        context=context
    )

def flush():
    """Forza l'invio di tutti i log in buffer"""
    if LOGSERVICE_AVAILABLE and PRAMAIALOGGER:
        try:
            _local_logger.info("Forzatura flush dei log in buffer...")
            PRAMAIALOGGER.flush()
            _local_logger.info("Flush dei log completato")
        except Exception as e:
            _local_logger.error(f"❌ Errore durante flush dei log: {str(e)}")

def close():
    """Chiude la connessione con il LogService"""
    if LOGSERVICE_AVAILABLE and PRAMAIALOGGER:
        try:
            _local_logger.info("Chiusura connessione LogService...")
            PRAMAIALOGGER.close()
            _local_logger.info("Connessione LogService chiusa")
        except Exception as e:
            _local_logger.error(f"❌ Errore durante chiusura logger: {str(e)}")

# Messaggio di inizializzazione
if LOGSERVICE_AVAILABLE and PRAMAIALOGGER:
    _local_logger.info("✅ LogService integrazione attiva")
    info("Document Monitor Agent logger inizializzato con integrazione LogService", 
         details={"host": LOGSERVICE_HOST})
else:
    _local_logger.info("❌ Logger Document Monitor Agent inizializzato SOLO in modalità locale")
    _local_logger.warning("LogService non disponibile - utilizzando solo logging locale")
    _local_logger.info("Per integrare con LogService, imposta PRAMAIALOG_API_KEY nelle variabili d'ambiente")
