"""
Event Logger Processor per PDK.
Registra gli eventi nel sistema PDF Monitor utilizzando il LogService centralizzato.
"""

import sys
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Importa il logger standardizzato
try:
    # Prima tenta di importare il modulo locale
    from . import logger
except ImportError:
    try:
        # Aggiungi la cartella common alla path
        plugin_common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../common"))
        if os.path.exists(plugin_common_path):
            sys.path.append(plugin_common_path)
            
        # Importa il modulo logger.py
        import logger
    except ImportError:
        # Fallback al logger standard
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.error("Impossibile importare il modulo di logging standardizzato")

# Path predefinito del database (non più utilizzato, solo per retrocompatibilità)
DEFAULT_DB_PATH = "document_monitor_events.db"

async def process(inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registra un evento nel LogService centralizzato.
    """
    # Log ingresso nodo
    event_type = str(inputs.get("event_type", ""))
    file_name = str(inputs.get("file_name", ""))
    entry_msg = f"[EventLogger] INGRESSO nodo: event_type={event_type}, file_name={file_name}"
    logger.info(entry_msg)
    try:
        status = str(inputs.get("status", ""))
        document_id = inputs.get("document_id")
        if document_id is not None:
            document_id = str(document_id)
        metadata = inputs.get("metadata", {})
        event_data = inputs.get("event_data", {})
        event_source = str(inputs.get("event_source", "pdk_workflow"))
        user_id = inputs.get("user_id")
        if user_id is not None:
            user_id = str(user_id)
        # Validazione degli input obbligatori
        _validate_inputs(event_type, file_name, status, document_id, metadata)
        # Generazione event_id e timestamp
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Preparazione dei dettagli dell'evento
        event_details = {
            "event_type": event_type,
            "file_name": file_name,
            "status": status,
            "event_id": event_id,
            "timestamp": timestamp
        }
        
        # Aggiungi campi opzionali se presenti
        if document_id:
            event_details["document_id"] = document_id
        if metadata:
            event_details["metadata"] = metadata
        if event_data:
            event_details["event_data"] = event_data
        if event_source:
            event_details["event_source"] = event_source
            
        # Preparazione del contesto
        event_context = {}
        if user_id:
            event_context["user_id"] = user_id
        
        # Invia l'evento come log lifecycle al LogService
        # Il tipo di evento determina il messaggio del log
        log_message = f"Evento {event_type} per il file '{file_name}'"
        if document_id:
            log_message += f" (documento ID: {document_id})"
        
        # Utilizza il metodo lifecycle del logger per registrare l'evento, con fallback su info
        try:
            if hasattr(logger, 'lifecycle'):
                logger.lifecycle(log_message, details=event_details, context=event_context)
            else:
                event_details["log_type"] = "lifecycle"
                logger.info(f"[LIFECYCLE] {log_message}", event_details)
        except Exception as e:
            # Fallback al logger standard
            logger.error(f"Errore durante l'invio del log lifecycle: {str(e)}")
            logger.info(f"[LIFECYCLE] {log_message}")
            
        exit_msg = f"[EventLogger] USCITA nodo (successo): event_type={event_type}, event_id={event_id}"
        logger.info(exit_msg)
        return {
            "success": True,
            "event_id": event_id,
            "timestamp": timestamp
        }
    except Exception as e:
        exit_msg = f"[EventLogger] USCITA nodo (errore): {str(e)}"
        logger.error(exit_msg)
        return {
            "success": False,
            "event_id": "",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def _validate_inputs(event_type: str, file_name: str, status: str, 
                     document_id: Optional[str], metadata: Any) -> None:
    """
    Valida i parametri di input.
    
    Args:
        event_type: Tipo di evento
        file_name: Nome del file
        status: Stato dell'evento
        document_id: ID del documento (opzionale)
        metadata: Metadati associati (opzionale)
        
    Raises:
        ValueError: Se i parametri obbligatori non sono validi
    """
    valid_event_types = [
        "file_processed", "file_detected", "metadata_updated", 
        "error", "workflow_executed", "custom"
    ]
    
    valid_statuses = ["success", "error", "warning", "info"]
    
    if not event_type:
        raise ValueError("Il tipo di evento è obbligatorio")
    
    if event_type not in valid_event_types:
        raise ValueError(f"Tipo di evento non valido. Valori ammessi: {', '.join(valid_event_types)}")
    
    if not file_name:
        raise ValueError("Il nome del file è obbligatorio")
    
    if not status:
        raise ValueError("Lo stato dell'evento è obbligatorio")
    
    if status not in valid_statuses:
        raise ValueError(f"Stato non valido. Valori ammessi: {', '.join(valid_statuses)}")
    
    if metadata and not isinstance(metadata, dict):
        raise ValueError("I metadati devono essere un dizionario")

# Nota: Funzione mantenuta per compatibilità ma reimplementata per utilizzare il LogService
def _log_event_to_db(db_path: str, event_id: str, timestamp: str, 
                     event_type: str, file_name: str, status: str,
                     document_id: Optional[str], metadata: Any, event_data: Any,
                     event_source: str, user_id: Optional[str]) -> None:
    """
    Registra un evento utilizzando il LogService anziché un database SQLite.
    Questa funzione è mantenuta per compatibilità con il codice esistente.
    
    Args:
        db_path: Percorso del database (ignorato, mantenuto per compatibilità)
        event_id: ID univoco dell'evento
        timestamp: Timestamp di registrazione
        event_type: Tipo di evento
        file_name: Nome del file
        status: Stato dell'evento
        document_id: ID del documento (opzionale)
        metadata: Metadati associati (opzionale)
        event_data: Dati aggiuntivi (opzionale)
        event_source: Sorgente dell'evento
        user_id: ID utente (opzionale)
    """
    try:
        # Preparazione dei dettagli dell'evento
        event_details = {
            "event_type": event_type,
            "file_name": file_name,
            "status": status,
            "event_id": event_id,
            "timestamp": timestamp
        }
        
        # Aggiungi campi opzionali se presenti
        if document_id:
            event_details["document_id"] = document_id
        if metadata:
            event_details["metadata"] = metadata
        if event_data:
            event_details["event_data"] = event_data
        if event_source:
            event_details["event_source"] = event_source
            
        # Preparazione del contesto
        event_context = {}
        if user_id:
            event_context["user_id"] = user_id
        
        # Invia l'evento come log lifecycle al LogService
        log_message = f"Evento {event_type} per il file '{file_name}'"
        if document_id:
            log_message += f" (documento ID: {document_id})"
        
        # Utilizza il metodo info con marker lifecycle per retrocompatibilità
        # in caso il metodo lifecycle non sia disponibile
        try:
            if hasattr(logger, 'lifecycle'):
                logger.lifecycle(log_message, details=event_details, context=event_context)
            else:
                event_details["log_type"] = "lifecycle"
                logger.info(f"[LIFECYCLE] {log_message}", event_details)
        except Exception as e:
            # Fallback al logger standard
            logger.error(f"Errore durante l'invio del log lifecycle: {str(e)}")
            logger.info(f"[LIFECYCLE] {log_message}")
        
    except Exception as e:
        logger.error(f"Errore durante la registrazione dell'evento: {str(e)}")
        raise

# Nota: Funzione mantenuta per compatibilità ma reimplementata per utilizzare il LogService
def _get_events(db_path: str, filters: Optional[Dict[str, Any]] = None, 
               limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Recupera eventi tramite il LogService.
    Questa funzione è mantenuta per compatibilità, ma potrebbe non fornire
    le stesse funzionalità complete dell'implementazione originale.
    
    Args:
        db_path: Percorso del database (ignorato, mantenuto per compatibilità)
        filters: Filtri da applicare (chiave/valore)
        limit: Numero massimo di risultati
        offset: Offset per la paginazione
        
    Returns:
        Lista di eventi come dizionari (vuota in questa implementazione)
    """
    logger.warning("La funzione _get_events è stata reimplementata per utilizzare il LogService. "
                  "Per accedere agli eventi, utilizza l'interfaccia web del LogService.")
    
    # Nota: Il recupero dei log dal LogService richiederebbe l'implementazione di un client
    # che faccia richieste API al LogService. Questa funzionalità è disponibile 
    # attraverso l'interfaccia web del LogService.
    
    return []

# Nota: Funzione mantenuta per compatibilità ma reimplementata per utilizzare il LogService
def _clear_events(db_path: str, older_than: Optional[datetime] = None) -> int:
    """
    Non supportato nell'implementazione LogService.
    La pulizia dei log è gestita automaticamente dal LogService.
    
    Args:
        db_path: Percorso del database (ignorato)
        older_than: Data limite (ignorato)
        
    Returns:
        Sempre 0, poiché non elimina nulla direttamente
    """
    logger.warning("La funzione _clear_events è stata reimplementata per utilizzare il LogService. "
                  "La pulizia dei log viene gestita automaticamente dal LogService.")
    
    return 0
