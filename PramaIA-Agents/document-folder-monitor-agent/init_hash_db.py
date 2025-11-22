import sqlite3
import os

def initialize_hash_db():
    """Inizializza il database degli hash nel percorso corretto"""
    
    # Assicuriamoci che esista la directory data
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Percorso del database come specificato nel file .env
    db_path = os.path.join(data_dir, "file_hashes.db")
    
    print(f"Inizializzazione del database degli hash in: {os.path.abspath(db_path)}")
    
    try:
        # Connessione al database (lo crea se non esiste)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Creazione della tabella se non esiste
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_hashes (
            file_path TEXT PRIMARY KEY,
            hash TEXT,
            timestamp INTEGER
        )
        ''')
        
        conn.commit()
        print(f"✅ Database inizializzato correttamente in: {os.path.abspath(db_path)}")
        
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Errore durante l'inizializzazione del database: {e}")
        return False

if __name__ == "__main__":
    initialize_hash_db()