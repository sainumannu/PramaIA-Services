"""
Modulo per il tracciamento degli hash dei file.
Fornisce funzionalità per rilevare modifiche nei file.
"""

import os
import hashlib
import time
import sqlite3
import sys
from typing import Dict, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

from .logger import info, warning, error, debug

# Carica le variabili d'ambiente
load_dotenv()

class FileInfo:
    """Informazioni su un file per la riconciliazione"""
    def __init__(self, path: str, size: int, last_modified: float, hash_value: str = ""):
        self.path = path
        self.size = size
        self.last_modified = last_modified
        self.hash_value = hash_value
        self.vectorstore_id = ""  # ID nel vectorstore, se presente
        
    @property
    def relative_path(self) -> str:
        """Ottiene il path relativo dal nome file"""
        return os.path.basename(self.path)
    
    def __eq__(self, other):
        if not isinstance(other, FileInfo):
            return False
        # Due file sono considerati uguali se hanno stesso path (includendo la posizione) e hash
        return self.path == other.path and self.hash_value == other.hash_value
    
    def __hash__(self):
        return hash((self.path, self.hash_value))
    
    def __repr__(self):
        from datetime import datetime
        return f"FileInfo(path={self.path}, size={self.size}, modified={datetime.fromtimestamp(self.last_modified)})"


class FolderState:
    """Rappresenta lo stato di una cartella con tutti i suoi file"""
    def __init__(self, folder_path: str):
        from datetime import datetime
        self.folder_path = folder_path
        self.files: Dict[str, FileInfo] = {}  # path -> FileInfo
        self.last_scan = datetime.now()
        
    def add_file(self, file_info: FileInfo):
        """Aggiunge un file allo stato della cartella"""
        self.files[file_info.path] = file_info
        
    def remove_file(self, file_path: str):
        """Rimuove un file dallo stato della cartella"""
        if file_path in self.files:
            del self.files[file_path]
            
    def get_file_paths(self) -> set:
        """Ottiene l'insieme dei path di tutti i file"""
        return set(self.files.keys())
    
    def __repr__(self):
        return f"FolderState({self.folder_path}, files={len(self.files)}, last_scan={self.last_scan})"


class FileHashTracker:
    """
    Traccia gli hash dei file per rilevare cambiamenti.
    Utilizza un database SQLite per la persistenza.
    """
    def __init__(self, db_path: str = ""):
        # Usa il percorso dalla variabile d'ambiente se non specificato
        if not db_path:
            db_path = os.getenv("FILE_HASHES_DB", "data/file_hashes.db")
            
        # Assicurati che la directory esista
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                debug(f"Creata directory per il database degli hash: {db_dir}")
            except Exception as e:
                warning(f"Impossibile creare la directory per il database degli hash: {e}")
                
        # Usa percorso assoluto per evitare problemi con la directory corrente
        if not os.path.isabs(db_path):
            # Se il percorso è relativo, lo riferisco alla directory principale dell'agent
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            db_path = os.path.join(base_dir, db_path)
            debug(f"Percorso database hash convertito ad assoluto: {db_path}")
            
        self.db_path = db_path
        debug(f"Inizializzazione FileHashTracker con database: {db_path}")
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        
    def create_tables(self):
        """Crea le tabelle necessarie se non esistono"""
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_hashes (
            file_path TEXT PRIMARY KEY,
            hash_value TEXT NOT NULL,
            size INTEGER NOT NULL,
            last_modified REAL NOT NULL,
            last_check REAL NOT NULL,
            vectorstore_id TEXT NULL
        )
        ''')
        self.conn.commit()
        
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calcola un hash efficiente per un file.
        Utilizza una combinazione di percorso, size, mtime e hash parziale per efficienza.
        Includendo il percorso nell'hash, garantiamo che copie identiche in posizioni diverse
        abbiano hash diversi.
        """
        try:
            stat = os.stat(file_path)
            
            # Includi il percorso nell'hash per garantire che file identici
            # in posizioni diverse abbiano hash diversi
            path_component = os.path.dirname(file_path)
            
            # Per file molto piccoli, calcola hash completo
            if stat.st_size < 100 * 1024:  # < 100KB
                with open(file_path, 'rb') as f:
                    full_hash = hashlib.md5(f.read()).hexdigest()
                return f"{path_component}:{stat.st_size}:{stat.st_mtime}:{full_hash}"
            
            # Per file più grandi, hash primi KB + ultimi KB
            with open(file_path, 'rb') as f:
                # Primi 4KB
                first_chunk = f.read(4096)
                
                # Ultimi 4KB
                f.seek(max(0, stat.st_size - 4096))
                last_chunk = f.read(4096)
                
                # Combina per hash rappresentativo ma efficiente
                combined_hash = hashlib.md5(first_chunk + last_chunk).hexdigest()
                return f"{path_component}:{stat.st_size}:{stat.st_mtime}:{combined_hash}"
                
        except (IOError, OSError) as e:
            error(f"Errore calcolo hash per {file_path}: {e}", details={"file_path": file_path, "error": str(e)})
            # Fallback hash basato solo su size e mtime
            try:
                stat = os.stat(file_path)
                return f"{stat.st_size}:{stat.st_mtime}:error"
            except:
                return f"0:0:error-{time.time()}"
    
    def get_stored_hash(self, file_path: str) -> Optional[FileInfo]:
        """Ottiene l'hash memorizzato per un file, se presente"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT hash_value, size, last_modified, vectorstore_id FROM file_hashes WHERE file_path = ?", 
            (file_path,)
        )
        result = cursor.fetchone()
        
        if result:
            hash_value, size, last_modified, vectorstore_id = result
            file_info = FileInfo(file_path, size, last_modified, hash_value)
            file_info.vectorstore_id = vectorstore_id
            return file_info
        return None
        
    def update_file_hash(self, file_info: FileInfo):
        """Aggiorna l'hash di un file nel database"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO file_hashes (file_path, hash_value, size, last_modified, last_check, vectorstore_id) VALUES (?, ?, ?, ?, ?, ?)",
            (file_info.path, file_info.hash_value, file_info.size, file_info.last_modified, time.time(), file_info.vectorstore_id)
        )
        self.conn.commit()
        
    def remove_file_hash(self, file_path: str):
        """Rimuove l'hash di un file dal database"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM file_hashes WHERE file_path = ?", (file_path,))
        self.conn.commit()
        
    def get_all_tracked_files(self, folder_path: str = "") -> Dict[str, FileInfo]:
        """Ottiene tutti i file tracciati nel database, opzionalmente filtrati per cartella"""
        cursor = self.conn.cursor()
        
        if folder_path:
            # Filtra per cartella (usando LIKE per supportare subcartelle)
            folder_pattern = f"{folder_path}%"
            cursor.execute(
                "SELECT file_path, hash_value, size, last_modified, vectorstore_id FROM file_hashes WHERE file_path LIKE ?",
                (folder_pattern,)
            )
        else:
            cursor.execute("SELECT file_path, hash_value, size, last_modified, vectorstore_id FROM file_hashes")
            
        results = cursor.fetchall()
        
        tracked_files = {}
        for file_path, hash_value, size, last_modified, vectorstore_id in results:
            file_info = FileInfo(file_path, size, last_modified, hash_value)
            file_info.vectorstore_id = vectorstore_id
            tracked_files[file_path] = file_info
            
        return tracked_files

    def close(self):
        """Chiude la connessione al database"""
        if self.conn:
            self.conn.close()
            
    @staticmethod
    def clean_database():
        """Pulisce il database degli hash eliminando tutti i record"""
        try:
            db_path = os.getenv("FILE_HASHES_DB", "data/file_hashes.db")
            
            # Se il percorso è relativo, lo riferisco alla directory principale dell'agent
            if not os.path.isabs(db_path):
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                db_path = os.path.join(base_dir, db_path)
                
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Verifica se esiste la tabella
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_hashes'")
                if cursor.fetchone():
                    # Conta record prima
                    cursor.execute("SELECT COUNT(*) FROM file_hashes")
                    count_before = cursor.fetchone()[0]
                    
                    # Elimina tutti i record
                    cursor.execute("DELETE FROM file_hashes")
                    conn.commit()
                    
                    # Conta record dopo
                    cursor.execute("SELECT COUNT(*) FROM file_hashes")
                    count_after = cursor.fetchone()[0]
                    
                    info(f"Database hash pulito: rimossi {count_before - count_after} record", 
                         details={"db_path": db_path, "records_removed": count_before - count_after})
                    
                conn.close()
                return True
            else:
                warning(f"Database hash non trovato: {db_path}")
                return False
        except Exception as e:
            error(f"Errore durante la pulizia del database degli hash: {e}", details={"error": str(e)})
            return False
