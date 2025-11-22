import json
import sqlite3
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .logger import debug as _safe_log_debug, info as _safe_log_info, warning as _safe_log_warning, error as _safe_log_error

def get_unsent_events(db_path: str, lock, limit: int = 100) -> List[Dict[str, Any]]:
    _safe_log_debug(f"[event_queries] Tentativo acquisizione lock per get_unsent_events")
    with lock:
        _safe_log_debug(f"[event_queries] Lock acquisito per get_unsent_events, apertura connessione SQLite")
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT id, event_type, file_name, folder, timestamp, status, document_id, error_message 
                    FROM events WHERE sent = 0 LIMIT ?
                ''', (limit,))
                rows = c.fetchall()
                _safe_log_debug(f"[event_queries] Connessione SQLite chiusa dopo get_unsent_events")
                return [
                    {
                        "id": row[0],
                        "event_type": row[1],
                        "file_name": row[2],
                        "folder": row[3],
                        "timestamp": row[4],
                        "status": row[5],
                        "document_id": row[6],
                        "error_message": row[7]
                    }
                    for row in rows
                ]
        except Exception as e:
            _safe_log_error(f"[event_queries] Errore in get_unsent_events: {e}")
            return []

def get_recent_events(db_path: str, lock, limit: int = 100, include_history: bool = False) -> List[Dict[str, Any]]:
    _safe_log_debug(f"[event_queries] Tentativo acquisizione lock per get_recent_events")
    with lock:
        _safe_log_debug(f"[event_queries] Lock acquisito per get_recent_events, apertura connessione SQLite")
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                try:
                    c.execute("PRAGMA table_info(events)")
                    columns = c.fetchall()
                    column_names = [col[1] for col in columns]
                    if 'is_current' not in column_names:
                        try:
                            c.execute("ALTER TABLE events ADD COLUMN is_current INTEGER DEFAULT 1")
                            conn.commit()
                            _safe_log_info("Aggiunta colonna is_current alla tabella events")
                        except Exception as e:
                            _safe_log_error(f"Errore aggiunta colonna is_current: {e}")
                    query = '''
                        SELECT id, event_type, file_name, folder, timestamp, status, document_id, error_message, 
                               COALESCE(metadata, '{}') as metadata
                        FROM events 
                    '''
                    if 'is_current' in column_names and not include_history:
                        query += "WHERE (is_current = 1 OR is_current IS NULL) AND status != 'history' "
                    query += "ORDER BY timestamp DESC LIMIT ?"
                    c.execute(query, (limit,))
                    rows = c.fetchall()
                    events = []
                    for row in rows:
                        event = {
                            "id": row[0],
                            "event_type": row[1],
                            "file_name": row[2],
                            "folder": row[3],
                            "timestamp": row[4],
                            "status": row[5],
                            "document_id": row[6],
                            "error_message": row[7]
                        }
                        try:
                            metadata = json.loads(row[8]) if row[8] else {}
                            if isinstance(metadata, dict):
                                event["metadata"] = metadata
                        except Exception:
                            pass
                        events.append(event)
                    _safe_log_debug(f"[event_queries] Connessione SQLite chiusa dopo get_recent_events")
                    return events
                except Exception as e:
                    _safe_log_error(f"get_recent_events: {e}")
                    c.execute('''
                        SELECT id, event_type, file_name, folder, timestamp, status, document_id, error_message
                        FROM events ORDER BY timestamp DESC LIMIT ?
                    ''', (limit,))
                    rows = c.fetchall()
                    _safe_log_debug(f"[event_queries] Connessione SQLite chiusa dopo fallback get_recent_events")
                    return [
                        {
                            "id": row[0],
                            "event_type": row[1],
                            "file_name": row[2],
                            "folder": row[3],
                            "timestamp": row[4],
                            "status": row[5],
                            "document_id": row[6],
                            "error_message": row[7]
                        }
                        for row in rows
                    ]
        except Exception as e:
            _safe_log_error(f"[event_queries] Errore in get_recent_events: {e}")
            return []

def mark_events_as_sent(db_path: str, lock, event_ids: List[int]) -> int:
    if not event_ids:
        return 0
    _safe_log_debug(f"[event_queries] Tentativo acquisizione lock per mark_events_as_sent")
    with lock:
        _safe_log_debug(f"[event_queries] Lock acquisito per mark_events_as_sent, apertura connessione SQLite")
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                placeholders = ','.join(['?' for _ in event_ids])
                c.execute(f'UPDATE events SET sent = 1 WHERE id IN ({placeholders})', event_ids)
                conn.commit()
                _safe_log_debug(f"[event_queries] Connessione SQLite chiusa dopo mark_events_as_sent")
                return c.rowcount
        except Exception as e:
            _safe_log_error(f"[event_queries] Errore in mark_events_as_sent: {e}")
            return 0

def mark_event_sent(db_path: str, lock, event_id: int) -> bool:
    _safe_log_debug(f"[event_queries] Tentativo acquisizione lock per mark_event_sent")
    with lock:
        _safe_log_debug(f"[event_queries] Lock acquisito per mark_event_sent, apertura connessione SQLite")
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute('UPDATE events SET sent = 1 WHERE id = ?', (event_id,))
                conn.commit()
                _safe_log_debug(f"[event_queries] Connessione SQLite chiusa dopo mark_event_sent")
                return c.rowcount > 0
        except Exception as e:
            _safe_log_error(f"[event_queries] Errore in mark_event_sent: {e}")
            return False

def get_event_status(db_path: str, lock, event_id: int) -> Optional[str]:
    _safe_log_debug(f"[event_queries] Tentativo acquisizione lock per get_event_status")
    with lock:
        _safe_log_debug(f"[event_queries] Lock acquisito per get_event_status, apertura connessione SQLite")
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute('SELECT status FROM events WHERE id = ?', (event_id,))
                row = c.fetchone()
                _safe_log_debug(f"[event_queries] Connessione SQLite chiusa dopo get_event_status")
                return row[0] if row else None
        except Exception as e:
            _safe_log_error(f"[event_queries] Errore in get_event_status: {e}")
            return None

def find_event_by_filename(db_path: str, lock, file_name: str) -> Optional[int]:
    _safe_log_debug(f"[event_queries] Tentativo acquisizione lock per find_event_by_filename ({file_name})")
    with lock:
        _safe_log_debug(f"[event_queries] Lock acquisito per find_event_by_filename ({file_name}), apertura connessione SQLite")
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT id FROM events WHERE file_name = ? AND status = 'pending' 
                    ORDER BY timestamp DESC LIMIT 1
                ''', (file_name,))
                row = c.fetchone()
                if not row:
                    c.execute('''
                        SELECT id FROM events WHERE file_name = ? 
                        ORDER BY timestamp DESC LIMIT 1
                    ''', (file_name,))
                    row = c.fetchone()
                _safe_log_debug(f"[event_queries] Connessione SQLite chiusa dopo find_event_by_filename ({file_name})")
                return row[0] if row else None
        except Exception as e:
            _safe_log_error(f"[event_queries] Errore in find_event_by_filename ({file_name}): {e}")
            return None

def update_event_status(db_path: str, lock, event_id: int, status: str, 
                        document_id: Optional[str] = None, 
                        error_message: Optional[str] = None) -> bool:
    _safe_log_debug(f"Aggiornamento stato evento {event_id} a '{status}', document_id: {document_id}")
    _safe_log_debug(f"[event_queries] Tentativo acquisizione lock per update_event_status")
    with lock:
        _safe_log_debug(f"[event_queries] Lock acquisito per update_event_status, apertura connessione SQLite")
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                # Prima verifichiamo lo stato attuale
                c.execute('SELECT status, document_id FROM events WHERE id = ?', (event_id,))
                row = c.fetchone()
                if not row:
                    _safe_log_error(f"Evento {event_id} non trovato nel database!")
                    return False
                current_status, current_doc_id = row
                _safe_log_debug(f"Stato attuale evento {event_id}: '{current_status}', document_id attuale: {current_doc_id}")
                # Evita il declassamento degli stati critici
                if current_status == 'duplicate' and status == 'completed':
                    _safe_log_warning(f"Tentativo di declassare l'evento {event_id} da 'duplicate' a 'completed'. Operazione non consentita.")
                    return False
                # Costruiamo l'update in base ai parametri forniti
                update_fields = ['status = ?']
                params = [status]
                if document_id is not None:
                    update_fields.append('document_id = ?')
                    params.append(document_id)
                if error_message is not None:
                    update_fields.append('error_message = ?')
                    params.append(error_message)
                # Completiamo i parametri con l'id dell'evento
                params.append(event_id)
                query = f'UPDATE events SET {", ".join(update_fields)} WHERE id = ?'
                _safe_log_debug(f"Query SQL: {query} con parametri {params}")
                c.execute(query, params)
                conn.commit()
                affected = c.rowcount > 0
                _safe_log_debug(f"Aggiornamento stato evento {event_id} completato: {affected}")
                _safe_log_debug(f"[event_queries] Connessione SQLite chiusa dopo update_event_status")
                return affected
        except Exception as e:
            _safe_log_error(f"[event_queries] Errore in update_event_status: {e}")
            return False

def update_event_document_id(db_path: str, lock, event_id: int, document_id: str) -> bool:
    if not document_id:
        _safe_log_warning(f"Tentativo di aggiornare document_id con valore vuoto per evento {event_id}")
        return False
    _safe_log_debug(f"Aggiornamento document_id per evento {event_id}: {document_id}")
    _safe_log_debug(f"[event_queries] Tentativo acquisizione lock per update_event_document_id")
    with lock:
        _safe_log_debug(f"[event_queries] Lock acquisito per update_event_document_id, apertura connessione SQLite")
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute('UPDATE events SET document_id = ? WHERE id = ?', (document_id, event_id))
                conn.commit()
                affected = c.rowcount > 0
                if affected:
                    _safe_log_debug(f"Document ID aggiornato con successo per evento {event_id}")
                else:
                    _safe_log_error(f"Fallito aggiornamento document_id per evento {event_id} (evento non trovato)")
                _safe_log_debug(f"[event_queries] Connessione SQLite chiusa dopo update_event_document_id")
                return affected
        except Exception as e:
            _safe_log_error(f"[event_queries] Errore in update_event_document_id: {e}")
            return False