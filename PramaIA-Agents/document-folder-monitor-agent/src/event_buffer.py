import sqlite3
import os
from datetime import datetime
from threading import Lock
from typing import Dict, Any, List, Optional, Union
from .logger import debug as _logger_debug, info as _logger_info, warning as _logger_warning, error as _logger_error
from . import event_history as _event_history

# Helper wrappers to reduce repeated try/except logging blocks scattered in the file.
def _safe_log_debug(msg):
    try:
        _logger_debug(msg)
    except Exception:
        try:
            _logger_debug(msg)
        except Exception:
            print(f"[DEBUG] {msg}")

def _safe_log_info(msg):
    try:
        _logger_info(msg)
    except Exception:
        try:
            _logger_info(msg)
        except Exception:
            print(f"[INFO] {msg}")

def _safe_log_warning(msg):
    try:
        _logger_warning(msg)
    except Exception:
        try:
            _logger_warning(msg)
        except Exception:
            print(f"[AVVISO] {msg}")

def _safe_log_error(msg):
    try:
        _logger_error(msg)
    except Exception:
        try:
            _logger_error(msg)
        except Exception:
            print(f"[ERROR] {msg}")

class EventBuffer:
    """
    Classe principale per la gestione del buffer degli eventi.
    
    Questa classe è stata refactored per separare le responsabilità:
    - event_types.py: Gestione dei tipi di eventi specializzati (rinomina, spostamento)
    - event_maintenance.py: Funzioni di manutenzione (pulizia duplicati, aggiornamento stalled)
    - event_queries.py: Operazioni di query e aggiornamento sul database
    - event_history.py: Funzioni di tracciamento storico
    
    Questa classe ora funge da API principale che delega le operazioni ai moduli appropriati.
    """
    def __init__(self, db_path="event_buffer.db"):
        self.db_path = db_path
        self.lock = Lock()
        _safe_log_debug(f"[EventBuffer] Inizializzazione con db_path={db_path}")
        self._init_db()
        
    def _init_db(self):
        """Inizializza il database se non esiste"""
        _safe_log_debug("[EventBuffer] Tentativo acquisizione lock per _init_db")
        with self.lock:
            _safe_log_debug("[EventBuffer] Lock acquisito per _init_db, apertura connessione SQLite")
            try:
                with sqlite3.connect(self.db_path) as conn:
                    c = conn.cursor()
                    c.execute('''
                        CREATE TABLE IF NOT EXISTS events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            event_type TEXT,
                            file_name TEXT,
                            folder TEXT,
                            timestamp TEXT,
                            sent INTEGER DEFAULT 0,
                            status TEXT DEFAULT 'pending',
                            document_id TEXT,
                            error_message TEXT
                        )
                    ''')
                    # Aggiunta colonna status se non esiste
                    try:
                        c.execute('ALTER TABLE events ADD COLUMN status TEXT DEFAULT "pending"')
                    except sqlite3.OperationalError:
                        pass  # Colonna già esistente
                    # Aggiunta colonna document_id se non esiste
                    try:
                        c.execute('ALTER TABLE events ADD COLUMN document_id TEXT')
                    except sqlite3.OperationalError:
                        pass  # Colonna già esistente
                    # Aggiunta colonna error_message se non esiste
                    try:
                        c.execute('ALTER TABLE events ADD COLUMN error_message TEXT')
                    except sqlite3.OperationalError:
                        pass  # Colonna già esistente
                    # Aggiunta colonna metadata se non esiste
                    try:
                        c.execute('ALTER TABLE events ADD COLUMN metadata TEXT DEFAULT "{}"')
                    except sqlite3.OperationalError:
                        pass  # Colonna già esistente
                    conn.commit()
                    _safe_log_debug("[EventBuffer] Connessione SQLite chiusa dopo _init_db")
            except Exception as e:
                _safe_log_error(f"[EventBuffer] Errore in _init_db: {e}")

    def add_event(self, event_type: str, file_name: str, folder: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Aggiunge un nuovo evento o aggiorna un evento esistente per lo stesso file.
        Delega la gestione di eventi specializzati (rinomina, spostamento) ai rispettivi handler.
        
        Args:
            event_type: Tipo di evento ('created', 'deleted', 'renamed', 'moved', 'path_changed')
            file_name: Nome del file
            folder: Cartella in cui si trova il file
            metadata: Metadati aggiuntivi per l'evento
        
        Returns:
            int: ID dell'evento creato o aggiornato
        """
        # Gestione di eventi specializzati
        if event_type == 'renamed' and metadata and isinstance(metadata, dict) and 'old_name' in metadata and 'new_name' in metadata:
            import event_types
            return event_types.handle_renamed_event(self.db_path, self.lock, event_type, file_name, folder, metadata)
            
        elif (event_type == 'moved' or event_type == 'path_changed') and metadata and isinstance(metadata, dict) and 'moved_from' in metadata and 'moved_to' in metadata:
            import event_types
            return event_types.handle_moved_event(self.db_path, self.lock, event_type, file_name, folder, metadata)
            
        # Gestione standard per altri eventi
        _safe_log_debug(f"[EventBuffer] Tentativo acquisizione lock per add_event ({event_type}, {file_name})")
        with self.lock:
            _safe_log_debug(f"[EventBuffer] Lock acquisito per add_event ({event_type}, {file_name}), apertura connessione SQLite")
            try:
                with sqlite3.connect(self.db_path) as conn:
                    c = conn.cursor()
                    # Ottieni metadati
                    document_id = None
                    if metadata and isinstance(metadata, dict):
                        document_id = metadata.get('document_id')
                    # Cerca l'evento più recente per questo file
                    c.execute(
                        'SELECT id, status, document_id, timestamp FROM events WHERE file_name = ? ORDER BY timestamp DESC LIMIT 1', 
                        (file_name,)
                    )
                    existing_event = c.fetchone()
                    # Se l'evento è in stato pending, aggiorna timestamp e altri campi
                    if existing_event and existing_event[1] == 'pending':
                        _safe_log_debug(f"Aggiornamento evento {existing_event[0]} in stato 'pending' per file {file_name}")
                        update_fields = ['timestamp = ?', 'event_type = ?', 'folder = ?']
                        params = [datetime.utcnow().isoformat(), event_type, folder]
                        if document_id and not existing_event[2]:  # Aggiungi document_id se non esiste già
                            update_fields.append('document_id = ?')
                            params.append(document_id)
                        update_query = f"UPDATE events SET {', '.join(update_fields)} WHERE id = ?"
                        params.append(existing_event[0])
                        c.execute(update_query, params)
                        event_id = existing_event[0]
                    # Evita di creare duplicati per lo stesso file nella stessa cartella entro un'ora
                    elif existing_event and existing_event[1] == 'completed':
                        # Controlla se è trascorsa meno di un'ora dall'ultimo evento
                        try:
                            last_timestamp = datetime.fromisoformat(existing_event[3])
                            now = datetime.utcnow()
                            time_diff = (now - last_timestamp).total_seconds() / 3600  # ore
                            if time_diff < 1:  # Se è passata meno di un'ora
                                _safe_log_debug(f"Evitata creazione duplicato per {file_name} (ultimo evento: {time_diff:.2f} ore fa)")
                                return existing_event[0]
                        except (ValueError, TypeError):
                            pass  # Se c'è un errore nel parsing del timestamp, procedi con la creazione
                        # Se arriviamo qui, significa che dobbiamo creare un nuovo evento
                        event_id = None
                    # Crea un nuovo evento
                    else:
                        _safe_log_debug(f"Creazione nuovo evento per file {file_name}")
                        # Imposta stato iniziale su 'aggiunto'
                        initial_status = 'aggiunto' if event_type == 'created' else 'pending'
                        if document_id:
                            c.execute('''
                                INSERT INTO events (event_type, file_name, folder, timestamp, sent, status, document_id)
                                VALUES (?, ?, ?, ?, 0, ?, ?)
                            ''', (event_type, file_name, folder, datetime.utcnow().isoformat(), initial_status, document_id))
                        else:
                            c.execute('''
                                INSERT INTO events (event_type, file_name, folder, timestamp, sent, status)
                                VALUES (?, ?, ?, ?, 0, ?)
                            ''', (event_type, file_name, folder, datetime.utcnow().isoformat(), initial_status))
                        event_id = c.lastrowid
                        _safe_log_debug(f"Nuovo evento {event_id} creato con stato '{initial_status}'")
                    conn.commit()
                    _safe_log_debug(f"[EventBuffer] Connessione SQLite chiusa dopo add_event ({event_type}, {file_name})")
                    return event_id if event_id is not None else 0
            except Exception as e:
                _safe_log_error(f"[EventBuffer] Errore in add_event ({event_type}, {file_name}): {e}")
                return 0

    def get_unsent_events(self, limit=100):
        """
        Recupera gli eventi non ancora inviati.
        Args:
            limit: Numero massimo di eventi da restituire
        Returns:
            List[Dict]: Lista di eventi non inviati
        """
        from . import event_queries
        return event_queries.get_unsent_events(self.db_path, self.lock, limit)
    
    def get_recent_events(self, limit=100, include_history=False):
        """
        Restituisce gli eventi più recenti, inclusi quelli già inviati.
        Args:
            limit: Numero massimo di eventi da restituire
            include_history: Se True, include anche gli eventi storici/archiviati
        Returns:
            List[Dict]: Lista di eventi recenti
        """
        from . import event_queries
        return event_queries.get_recent_events(self.db_path, self.lock, limit, include_history)
    
    def mark_events_as_sent(self, event_ids):
        """
        Segna più eventi come inviati
        Args:
            event_ids: Lista di ID degli eventi da segnare come inviati
        Returns:
            int: Numero di eventi aggiornati
        """
        from . import event_queries
        return event_queries.mark_events_as_sent(self.db_path, self.lock, event_ids)
    
    def mark_event_sent(self, event_id):
        """
        Segna un evento come inviato
        Args:
            event_id: ID dell'evento da segnare come inviato
        Returns:
            bool: True se l'operazione ha avuto successo, False altrimenti
        """
        from . import event_queries
        return event_queries.mark_event_sent(self.db_path, self.lock, event_id)
    
    def update_event_status(self, event_id, status, document_id=None, error_message=None):
        """
        Aggiorna lo stato di un evento specifico.
        Stati possibili: 'pending', 'processing', 'completed', 'duplicate', 'error', 'failed'
        Args:
            event_id: ID dell'evento da aggiornare
            status: Nuovo stato
            document_id: Opzionale, ID del documento associato all'evento
            error_message: Opzionale, messaggio di errore in caso di problemi
        Returns:
            bool: True se l'operazione ha avuto successo, False altrimenti
        """
        from . import event_queries
        return event_queries.update_event_status(self.db_path, self.lock, event_id, status, document_id, error_message)
    
    def update_event_document_id(self, event_id, document_id):
        """
        Aggiorna il document_id di un evento specifico.
        Args:
            event_id: ID dell'evento da aggiornare
            document_id: Nuovo ID del documento
        Returns:
            bool: True se l'operazione ha avuto successo, False altrimenti
        """
        from . import event_queries
        return event_queries.update_event_document_id(self.db_path, self.lock, event_id, document_id)
    
    def get_event_status(self, event_id):
        """
        Ottiene lo stato corrente di un evento.
        Args:
            event_id: ID dell'evento
        Returns:
            str: Stato dell'evento ('pending', 'processing', 'completed', 'duplicate', 'error', 'failed')
            o None se l'evento non esiste
        """
        from . import event_queries
        return event_queries.get_event_status(self.db_path, self.lock, event_id)

    def find_event_by_filename(self, file_name):
        """
        Cerca un evento per nome file. Restituisce prima gli eventi in stato 'pending',
        altrimenti l'evento più recente per il file.
        Args:
            file_name: Nome del file da cercare
        Returns:
            int: ID dell'evento trovato, o None se non trovato
        """
        from . import event_queries
        return event_queries.find_event_by_filename(self.db_path, self.lock, file_name)
    
    def track_file_history(self, file_name, event_type, status=None):
        """Delega l'operazione di tracciamento storie al modulo `event_history`."""
        try:
            return _event_history.track_file_history(self.db_path, self.lock, file_name, event_type, status)
        except Exception as e:
            _safe_log_error(f"track_file_history delegazione fallita: {e}")
            return 0
    
    def get_file_history(self, file_name):
        """
        Restituisce la storia completa di un file, inclusi tutti gli eventi e stati.
        Utile per debug e per visualizzare la timeline completa di un file.
        
        Args:
            file_name: Nome del file di cui recuperare la storia
            
        Returns:
            Lista di eventi in ordine cronologico
        """
        try:
            return _event_history.get_file_history(self.db_path, self.lock, file_name)
        except Exception as e:
            _safe_log_error(f"get_file_history delegazione fallita: {e}")
            return []
    
    def clean_duplicate_events(self) -> int:
        """
        Elimina eventi duplicati mantenendo solo l'evento più appropriato per ogni file.
        Regole di selezione:
        1. Se ci sono eventi completati con document_id, mantieni il più recente di questi
        2. Se non ci sono completati con document_id, ma ci sono eventi completati, mantieni il più recente
        3. Se ci sono solo eventi in attesa/errore, mantieni il più recente
        4. Gestione speciale per eventi di rinomina: trova e rimuove le coppie deleted/renamed
        """
        from . import event_maintenance
        return event_maintenance.clean_duplicate_events(self.db_path, self.lock)
   
    def auto_update_stalled_events(self, max_age_hours=2) -> int:
        """
        Cerca eventi che sono in stato 'pending' o 'aggiunto' da troppo tempo e li segna come falliti.
        Questo è utile per evitare eventi "zombie" che rimangono bloccati in stato di attesa.
        
        Args:
            max_age_hours: Numero di ore dopo le quali un evento in attesa viene considerato bloccato
        
        Returns:
            int: Numero di eventi aggiornati
        """
        from . import event_maintenance
        return event_maintenance.auto_update_stalled_events(self.db_path, self.lock, max_age_hours) # Crea un'istanza globale di EventBuffer che può essere importata da altri moduli
event_buffer = EventBuffer()
