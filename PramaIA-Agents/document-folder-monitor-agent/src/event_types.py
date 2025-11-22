import json
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, Any, Optional, Tuple

from .logger import debug as _safe_log_debug, info as _safe_log_info, warning as _safe_log_warning, error as _safe_log_error
def handle_renamed_event(db_path: str, lock, event_type: str, file_name: str, 
                         folder: str, metadata: Dict[str, Any]) -> int:
    """
    Gestisce l'aggiunta di un evento di rinomina file.
    Implementa la logica specializzata per gestire rinomina file e 
    pulizia degli eventi deleted corrispondenti.
    
    Returns:
        int: ID dell'evento creato
    """
    old_name = metadata.get('old_name')
    new_name = metadata.get('new_name')
    document_id = metadata.get('document_id')
    
    if not (old_name and new_name):
        _safe_log_warning(f"Evento rinomina senza nome vecchio/nuovo: {metadata}")
        return 0
        
    with lock, sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        
        # Evento di rinomina: salva nomi vecchi/nuovi in error_message (per retrocompatibilità)
        details = f"Rinominato da '{old_name}' a '{new_name}'"
        if metadata and isinstance(metadata, dict) and 'details' in metadata:
            details = metadata['details']
        
        rename_info = json.dumps({
            'old_name': old_name,
            'new_name': new_name,
            'details': details
        })
        _safe_log_debug(f"Registrazione evento di rinomina per file: da {old_name} a {new_name}")
        c.execute('''
            INSERT INTO events (event_type, file_name, folder, timestamp, sent, status, document_id, error_message)
            VALUES (?, ?, ?, ?, 0, 'renamed', ?, ?)
        ''', (event_type, file_name, folder, datetime.utcnow().isoformat(), document_id, rename_info))
        event_id = c.lastrowid
        # Cerca se c'è un evento "removed" recente per il vecchio nome del file
        # Se lo troviamo, lo cancelliamo perché abbiamo già registrato l'operazione come rename
        cutoff_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        c.execute('''
            DELETE FROM events 
            WHERE file_name = ? AND event_type = 'deleted' AND timestamp > ? 
            AND status NOT IN ('completed', 'failed')
        ''', (old_name, cutoff_time))
        deleted_count = c.rowcount
        if deleted_count > 0:
            _safe_log_debug(f"Rimossi {deleted_count} eventi 'deleted' ridondanti per il file rinominato: {old_name}")
        
    return event_id if event_id is not None else 0


def handle_moved_event(db_path: str, lock, event_type: str, file_name: str,
                       folder: str, metadata: Dict[str, Any]) -> int:
    """
    Gestisce l'aggiunta di un evento di spostamento file.
    Implementa la logica specializzata per registrare lo spostamento di file.
    
    Returns:
        int: ID dell'evento creato
    """
    moved_from = metadata.get('moved_from')
    moved_to = metadata.get('moved_to')
    document_id = metadata.get('document_id')
    
    if not (moved_from and moved_to):
        _safe_log_warning(f"Evento spostamento senza origine/destinazione: {metadata}")
        return 0
        
    with lock, sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        
        # Evento di spostamento: salva percorso origine/destinazione in error_message
        moved_info = json.dumps({
            'from': moved_from,
            'to': moved_to
        })
        _safe_log_debug(f"Registrazione evento di spostamento per file {file_name}: da {moved_from} a {moved_to}")
        c.execute('''
            INSERT INTO events (event_type, file_name, folder, timestamp, sent, status, document_id, error_message)
            VALUES (?, ?, ?, ?, 0, 'moved', ?, ?)
        ''', (event_type, file_name, folder, datetime.utcnow().isoformat(), document_id, moved_info))
        event_id = c.lastrowid

    return event_id if event_id is not None else 0
