"""
Modulo di estensione per il logging avanzato dell'agente document-folder-monitor.
Questo modulo aggiunge funzionalità di logging dettagliato per tracciare
il ciclo di vita completo dei documenti, dalla rilevazione all'invio al backend.
"""

import os
import json
import time
from datetime import datetime
from .logger import info, warning, error, debug

class DetailedLogger:
    """
    Implementa un sistema di logging avanzato per l'agente di monitoraggio
    che traccia l'intero ciclo di vita dei documenti.
    """
    
    @staticmethod
    def log_file_detection(event_type, file_path, folder):
        """
        Registra la rilevazione di un evento sul filesystem
        
        Args:
            event_type: Il tipo di evento (create, modify, delete)
            file_path: Percorso completo del file
            folder: Cartella di monitoraggio
        """
        file_name = os.path.basename(file_path)
        
        # Raccogli statistiche sul file se esiste
        file_stats = {}
        if os.path.exists(file_path) and event_type != 'delete':
            try:
                stat = os.stat(file_path)
                file_stats = {
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "mtime_human": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            except Exception as e:
                file_stats = {"error": f"Impossibile ottenere statistiche: {str(e)}"}
        
        info(
            f"🔎 Rilevato evento {event_type.upper()} per '{file_name}'",
            details={
                "event": "FILE_DETECTION",
                "event_type": event_type,
                "file_name": file_name,
                "file_path": file_path,
                "folder": folder,
                "timestamp": datetime.now().isoformat(),
                "file_stats": file_stats
            }
        )
    
    @staticmethod
    def log_hash_calculation(file_path, hash_value, is_new=True):
        """
        Registra il calcolo dell'hash per un file
        
        Args:
            file_path: Percorso del file
            hash_value: Hash calcolato
            is_new: Se è un nuovo hash o uno esistente
        """
        file_name = os.path.basename(file_path)
        
        info(
            f"🔢 {'Calcolato' if is_new else 'Recuperato'} hash per '{file_name}'",
            details={
                "event": "HASH_CALCULATION",
                "file_name": file_name,
                "file_path": file_path,
                "hash_value": hash_value,
                "is_new_hash": is_new,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def log_hash_db_operation(operation, file_path, hash_value=None, success=True):
        """
        Registra operazioni sul database degli hash
        
        Args:
            operation: Tipo di operazione (add, update, remove, check)
            file_path: Percorso del file
            hash_value: Hash del file (opzionale)
            success: Se l'operazione è riuscita
        """
        file_name = os.path.basename(file_path)
        
        log_level = info if success else warning
        
        operation_name = {
            "add": "Aggiunto",
            "update": "Aggiornato",
            "remove": "Rimosso",
            "check": "Verificato"
        }.get(operation, operation)
        
        icon = "✅" if success else "⚠️"
        
        log_level(
            f"{icon} {operation_name} hash nel database per '{file_name}'",
            details={
                "event": "HASH_DB_OPERATION",
                "operation": operation,
                "file_name": file_name,
                "file_path": file_path,
                "hash_value": hash_value,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def log_backend_request(operation, file_path, request_data=None):
        """
        Registra una richiesta verso il backend
        
        Args:
            operation: Tipo di operazione (upload, delete)
            file_path: Percorso del file
            request_data: Dati della richiesta (opzionale)
        """
        file_name = os.path.basename(file_path)
        
        info(
            f"📤 Invio richiesta {operation.upper()} al backend per '{file_name}'",
            details={
                "event": "BACKEND_REQUEST",
                "operation": operation,
                "file_name": file_name,
                "file_path": file_path,
                "request_data": request_data,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def log_backend_response(operation, file_path, status_code, response_data, success=True):
        """
        Registra la risposta dal backend
        
        Args:
            operation: Tipo di operazione (upload, delete)
            file_path: Percorso del file
            status_code: Codice di stato HTTP
            response_data: Dati della risposta
            success: Se l'operazione è riuscita
        """
        file_name = os.path.basename(file_path)
        
        log_level = info if success else warning
        icon = "✅" if success else "⚠️"
        
        log_level(
            f"{icon} Risposta {operation.upper()} dal backend per '{file_name}': {status_code}",
            details={
                "event": "BACKEND_RESPONSE",
                "operation": operation,
                "file_name": file_name,
                "file_path": file_path,
                "status_code": status_code,
                "response_data": response_data,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def log_filter_decision(file_path, filter_name, decision):
        """
        Registra una decisione di filtro
        
        Args:
            file_path: Percorso del file
            filter_name: Nome del filtro
            decision: Decisione presa dal filtro
        """
        file_name = os.path.basename(file_path)
        
        info(
            f"🔍 Filtro '{filter_name}' ha deciso '{decision['action']}' per '{file_name}'",
            details={
                "event": "FILTER_DECISION",
                "file_name": file_name,
                "file_path": file_path,
                "filter_name": filter_name,
                "decision": decision,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def log_error(context, file_path, error_message, error_details=None):
        """
        Registra un errore durante l'elaborazione
        
        Args:
            context: Contesto dell'errore
            file_path: Percorso del file
            error_message: Messaggio di errore
            error_details: Dettagli aggiuntivi sull'errore
        """
        file_name = os.path.basename(file_path) if file_path else "N/A"
        
        error(
            f"❌ Errore in {context} per '{file_name}': {error_message}",
            details={
                "event": "ERROR",
                "context": context,
                "file_name": file_name,
                "file_path": file_path,
                "error_message": error_message,
                "error_details": error_details,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def log_document_lifecycle(file_path, stage, status, details=None):
        """
        Registra uno stadio del ciclo di vita di un documento
        
        Args:
            file_path: Percorso del file
            stage: Fase del ciclo di vita
            status: Stato del documento in questa fase
            details: Dettagli aggiuntivi
        """
        file_name = os.path.basename(file_path)
        
        info(
            f"📄 Documento '{file_name}' - {stage}: {status}",
            details={
                "event": "DOCUMENT_LIFECYCLE",
                "file_name": file_name,
                "file_path": file_path,
                "stage": stage,
                "status": status,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )

# Crea un'istanza globale per l'utilizzo in tutto il codice
detailed_logger = DetailedLogger()