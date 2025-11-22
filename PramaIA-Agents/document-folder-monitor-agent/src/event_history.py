import sqlite3
from datetime import datetime
import json
from .logger import error as _logger_error, info as _logger_info


def track_file_history(db_path, lock, file_name, event_type, status=None):
    """
    Aggiunge un nuovo stato alla storia temporale di un file.
    Restituisce la sequence del nuovo record oppure 0 se fallisce.
    """
    try:
        with lock, sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            # Assicurati che la tabella esista
            c.execute(''' 
            CREATE TABLE IF NOT EXISTS file_history
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             file_name TEXT,
             event_type TEXT,
             status TEXT,
             timestamp TEXT,
             sequence INTEGER)
            ''')
            # Ottieni l'ultima sequenza per questo file
            c.execute(''' 
                SELECT MAX(sequence) FROM file_history WHERE file_name = ?
            ''', (file_name,))
            result = c.fetchone()
            sequence = (result[0] or 0) + 1

            # Aggiungi il nuovo stato alla storia
            c.execute(''' 
                INSERT INTO file_history (file_name, event_type, status, timestamp, sequence)
                VALUES (?, ?, ?, ?, ?)
            ''', (file_name, event_type, status or event_type, datetime.utcnow().isoformat(), sequence))

            conn.commit()
            return sequence
    except Exception as e:
        try:
            _logger_error(f"Errore durante il tracciamento della storia del file {file_name}: {e}")
        except Exception:
            print(f"[ERROR] Errore durante il tracciamento della storia del file {file_name}: {e}")
        return 0


def get_file_history(db_path, lock, file_name):
    """
    Restituisce la storia completa di un file, inclusi tutti gli eventi e stati.
    """
    try:
        with lock, sqlite3.connect(db_path) as conn:
            c = conn.cursor()

            # Prima cerchiamo nella tabella file_history
            c.execute('''
                SELECT id, event_type, status, timestamp, sequence 
                FROM file_history 
                WHERE file_name = ?
                ORDER BY sequence ASC
            ''', (file_name,))

            history_rows = c.fetchall()

            # Poi cerchiamo anche nella tabella events per completezza
            # metadata potrebbe non esistere in tutte le versioni del DB
            try:
                c.execute('''
                    SELECT id, event_type, status, timestamp, error_message, metadata
                    FROM events
                    WHERE file_name = ?
                    ORDER BY timestamp ASC
                ''', (file_name,))
                event_rows = c.fetchall()
            except Exception:
                # fallback a schema più semplice
                c.execute('''
                    SELECT id, event_type, status, timestamp, error_message
                    FROM events
                    WHERE file_name = ?
                    ORDER BY timestamp ASC
                ''', (file_name,))
                event_rows = [(*r, None) for r in c.fetchall()]

            # Combina i risultati in una timeline cronologica
            timeline = []

            for row in history_rows:
                timeline.append({
                    "id": f"hist_{row[0]}",
                    "event_type": row[1],
                    "status": row[2],
                    "timestamp": row[3],
                    "sequence": row[4],
                    "source": "history"
                })

            for row in event_rows:
                event = {
                    "id": f"evt_{row[0]}",
                    "event_type": row[1],
                    "status": row[2],
                    "timestamp": row[3],
                    "source": "events"
                }

                if row[4]:  # error_message
                    try:
                        event["details"] = json.loads(row[4])
                    except Exception:
                        event["details"] = row[4]

                if row[5]:  # metadata
                    try:
                        event["metadata"] = json.loads(row[5])
                    except Exception:
                        pass

                timeline.append(event)

            # Ordina la timeline per timestamp
            timeline.sort(key=lambda x: x["timestamp"]) if timeline else None

            return timeline
    except Exception as e:
        try:
            _logger_error(f"Errore durante il recupero della storia del file {file_name}: {e}")
        except Exception:
            print(f"[ERROR] Errore durante il recupero della storia del file {file_name}: {e}")
        return []
