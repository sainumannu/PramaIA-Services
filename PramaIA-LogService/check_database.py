"""
Script per verificare il contenuto del database di log.
"""

import sqlite3
import os

def check_database():
    """Verifica il contenuto del database di log."""
    db_path = os.path.join("logs", "log_database.db")
    
    if not os.path.exists(db_path):
        print(f"Il database {db_path} non esiste.")
        return
    
    try:
        # Connessione al database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verifica se la tabella logs esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
        if not cursor.fetchone():
            print("La tabella 'logs' non esiste nel database.")
            conn.close()
            return
        
        # Conta il numero totale di log
        cursor.execute("SELECT COUNT(*) as count FROM logs")
        total_logs = cursor.fetchone()["count"]
        print(f"Numero totale di log nel database: {total_logs}")
        
        if total_logs > 0:
            # Ottieni gli ultimi 5 log
            cursor.execute("""
                SELECT id, timestamp, project, level, module, message, details
                FROM logs
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            
            print("\nUltimi 5 log:")
            print("-" * 80)
            
            for row in cursor.fetchall():
                print(f"ID: {row['id']}")
                print(f"Timestamp: {row['timestamp']}")
                print(f"Progetto: {row['project']}")
                print(f"Livello: {row['level']}")
                print(f"Modulo: {row['module']}")
                print(f"Messaggio: {row['message']}")
                print(f"Dettagli: {row['details']}")
                print("-" * 80)
        
        # Verifica se ci sono log nelle ultime 24 ore
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        cursor.execute("SELECT COUNT(*) as count FROM logs WHERE timestamp > ?", (yesterday,))
        recent_logs = cursor.fetchone()["count"]
        print(f"\nLog nelle ultime 24 ore: {recent_logs}")
        
        # Verifica se ci sono log negli ultimi 15 minuti
        fifteen_min_ago = (datetime.now() - timedelta(minutes=15)).isoformat()
        
        cursor.execute("SELECT COUNT(*) as count FROM logs WHERE timestamp > ?", (fifteen_min_ago,))
        very_recent_logs = cursor.fetchone()["count"]
        print(f"Log negli ultimi 15 minuti: {very_recent_logs}")
        
        conn.close()
        
    except Exception as e:
        print(f"Errore durante la verifica del database: {str(e)}")

if __name__ == "__main__":
    print("=== Verifica del database di log ===\n")
    check_database()
