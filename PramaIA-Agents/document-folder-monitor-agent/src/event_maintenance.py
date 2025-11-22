import json
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, Any, List, Set, Optional, Tuple

from .logger import debug as _safe_log_debug, info as _safe_log_info, warning as _safe_log_warning, error as _safe_log_error


def clean_duplicate_events(db_path: str, lock) -> int:
    """
    Elimina eventi duplicati mantenendo solo l'evento più appropriato per ogni file.
    Utilizza la versione legacy del metodo clean_duplicate_events che elimina fisicamente 
    i duplicati invece di marcarli come storici.
    
    Returns:
        int: Numero di eventi duplicati rimossi
    """
    _safe_log_info("Pulizia avanzata degli eventi duplicati...")
    try:
        # Utilizziamo direttamente la versione legacy
        return _legacy_clean_duplicate_events(db_path, lock)
    except Exception as e:
        _safe_log_error(f"Errore durante la pulizia degli eventi: {e}")
        return 0


def _legacy_clean_duplicate_events(db_path: str, lock) -> int:
    """
    Versione legacy del metodo clean_duplicate_events che elimina fisicamente i duplicati
    invece di marcarli come storici. Usato come fallback se la nuova versione fallisce.
    """
    _safe_log_info("Usando il metodo legacy di pulizia degli eventi duplicati...")
    count = 0
    _safe_log_debug(f"[event_maintenance] Tentativo acquisizione lock per _legacy_clean_duplicate_events")
    with lock:
        _safe_log_debug(f"[event_maintenance] Lock acquisito per _legacy_clean_duplicate_events, apertura connessione SQLite")
        try:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                # Gestione eventi di rinomina con status diversi
                c.execute("""
                    WITH RenamedFiles AS (
                        SELECT file_name
                        FROM events
                        WHERE event_type = 'renamed'
                        GROUP BY file_name
                        HAVING COUNT(*) > 1
                    )
                    SELECT e.id, e.file_name, e.status
                    FROM events e
                    JOIN RenamedFiles rf ON e.file_name = rf.file_name
                    WHERE e.event_type = 'renamed'
                    ORDER BY e.file_name, e.status
                """)
                duplicate_renamed = c.fetchall()
                files_processed: Set[str] = set()
                # Per ogni file con eventi "renamed" duplicati
                for event in duplicate_renamed:
                    event_id, file_name, status = event
                    if file_name in files_processed:
                        continue
                    c.execute("""
                        SELECT id FROM events
                        WHERE file_name = ? AND event_type = 'renamed' AND status = 'completed'
                        ORDER BY timestamp DESC LIMIT 1
                    """, (file_name,))
                    completed_event = c.fetchone()
                    if completed_event:
                        # Mantieni solo l'evento completato
                        completed_id = completed_event[0]
                        c.execute("""
                            DELETE FROM events
                            WHERE file_name = ? AND event_type = 'renamed' AND id != ?
                        """, (file_name, completed_id))
                        count += c.rowcount
                    else:
                        # Mantieni solo il più recente
                        c.execute("""
                            WITH RankedEvents AS (
                                SELECT 
                                    id,
                                    ROW_NUMBER() OVER (ORDER BY timestamp DESC) as rn
                                FROM events
                                WHERE file_name = ? AND event_type = 'renamed'
                            )
                            DELETE FROM events
                            WHERE id IN (
                                SELECT id FROM RankedEvents WHERE rn > 1
                            ) AND file_name = ? AND event_type = 'renamed'
                        """, (file_name, file_name))
                        count += c.rowcount
                    files_processed.add(file_name)
                conn.commit()
                _safe_log_debug(f"[event_maintenance] Connessione SQLite chiusa dopo _legacy_clean_duplicate_events")
        except Exception as e:
            _safe_log_error(f"[event_maintenance] Errore in _legacy_clean_duplicate_events: {e}")
    return count


def auto_update_stalled_events(db_path: str, lock, max_age_hours: int = 2) -> int:
    """
    Cerca eventi che sono in stato 'pending' o 'aggiunto' da troppo tempo e li segna come falliti.
    Questo è utile per evitare eventi "zombie" che rimangono bloccati in stato di attesa.
    
    Args:
        db_path: Percorso al database SQLite
        lock: Lock per l'accesso concorrente al database
        max_age_hours: Numero di ore dopo le quali un evento in attesa viene considerato bloccato
    
    Returns:
        int: Numero di eventi aggiornati
    """
    try:
        _safe_log_info(f"Verifica eventi bloccati (più vecchi di {max_age_hours} ore)...")
        now = datetime.utcnow()
        cutoff_time = (now - timedelta(hours=max_age_hours)).isoformat()
        _safe_log_debug(f"[event_maintenance] Tentativo acquisizione lock per auto_update_stalled_events")
        with lock:
            _safe_log_debug(f"[event_maintenance] Lock acquisito per auto_update_stalled_events, apertura connessione SQLite")
            try:
                with sqlite3.connect(db_path) as conn:
                    c = conn.cursor()
                    # Cerca eventi bloccati in stato 'pending' o 'aggiunto'
                    c.execute('''
                        SELECT id, file_name, status, timestamp 
                        FROM events 
                        WHERE (status = 'pending' OR status = 'aggiunto' OR status = 'In attesa') 
                        AND timestamp < ?
                    ''', (cutoff_time,))
                    stalled_events = c.fetchall()
                    updated_count = 0
                    for event in stalled_events:
                        event_id, file_name, status, timestamp = event
                        try:
                            time_diff = (now - datetime.fromisoformat(timestamp)).total_seconds() / 3600
                            _safe_log_info(f"Evento {event_id} ({file_name}) bloccato in stato '{status}' da {time_diff:.1f} ore")
                            # Aggiorna lo stato a 'failed' con un messaggio di errore
                            c.execute('''
                                UPDATE events 
                                SET status = 'failed', error_message = ? 
                                WHERE id = ?
                            ''', (f"Evento scaduto: nessun aggiornamento dopo {time_diff:.1f} ore", event_id))
                            updated_count += 1
                        except Exception as e:
                            _safe_log_error(f"Errore durante l'aggiornamento dell'evento {event_id}: {e}")
                    conn.commit()
                    _safe_log_debug(f"[event_maintenance] Connessione SQLite chiusa dopo auto_update_stalled_events")
                    _safe_log_info(f"{updated_count} eventi bloccati sono stati aggiornati a 'failed'")
                    return updated_count
            except Exception as e:
                _safe_log_error(f"[event_maintenance] Errore in auto_update_stalled_events: {e}")
                return 0
    except Exception as e:
        _safe_log_error(f"auto_update_stalled_events fallito: {e}")
        return 0
