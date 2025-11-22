"""
Modulo di estensione per aggiungere la pulizia del database degli hash all'agente di monitoraggio.
Da installare nella directory src dell'agente.
"""

import os
import threading
import time
from pathlib import Path
from .logger import info, warning, error, debug

class HashDbCleaner:
    """
    Classe per la pulizia del database degli hash dell'agente di monitoraggio.
    """
    def __init__(self, cleanup_interval_hours=24):
        """
        Inizializza il cleaner con un intervallo di pulizia specificato.
        
        Args:
            cleanup_interval_hours: Intervallo in ore tra una pulizia e l'altra
        """
        self.cleanup_interval_seconds = cleanup_interval_hours * 3600
        self.running = False
        self.thread = None
    
    def start(self):
        """Avvia il thread di pulizia periodica"""
        if self.thread is not None and self.thread.is_alive():
            debug("Il cleaner degli hash è già in esecuzione")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.thread.start()
        info("🧹 Cleaner del database hash avviato")
        
    def stop(self):
        """Ferma il thread di pulizia periodica"""
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        info("🛑 Cleaner del database hash fermato")
    
    def _cleanup_loop(self):
        """Loop principale di pulizia periodica"""
        # Prima pulizia all'avvio
        self.cleanup_hash_database()
        
        # Poi ogni tot ore
        while self.running:
            time.sleep(self.cleanup_interval_seconds)
            if not self.running:
                break
            self.cleanup_hash_database()
    
    def cleanup_hash_database(self):
        """
        Pulisce il database file_hashes.db rimuovendo i record per file che non esistono più nel filesystem
        """
        from .file_hash_tracker import FileHashTracker
        
        info("[MANUTENZIONE] Avvio pulizia database file_hashes...")
        
        try:
            # Inizializza il tracker degli hash
            tracker = FileHashTracker()
            
            # Ottiene tutti i file tracciati
            all_tracked_files = tracker.get_all_tracked_files()
            
            # Conta i file che non esistono più
            files_to_remove = []
            for file_path in all_tracked_files:
                if not os.path.exists(file_path):
                    files_to_remove.append(file_path)
            
            # Rimuove i file che non esistono più
            removed_count = 0
            for file_path in files_to_remove:
                tracker.remove_file_hash(file_path)
                removed_count += 1
            
            info(f"[MANUTENZIONE] Pulizia database completata: rimossi {removed_count} hash di file non più esistenti")
            
            # Chiude correttamente la connessione al database
            tracker.close()
            
            return removed_count
        except Exception as e:
            error(f"[ERROR] Errore durante la pulizia del database file_hashes: {str(e)}")
            return 0
    
    def remove_file_hash(self, file_path):
        """
        Rimuove un hash specifico dal database
        
        Args:
            file_path: Il percorso del file il cui hash deve essere rimosso
        """
        try:
            from .file_hash_tracker import FileHashTracker
            
            tracker = FileHashTracker()
            tracker.remove_file_hash(file_path)
            tracker.close()
            
            debug(f"Hash rimosso dal database per il file {file_path}")
            return True
        except Exception as e:
            error(f"[ERROR] Errore durante la rimozione dell'hash per {file_path}: {str(e)}")
            return False

# Crea un'istanza globale del cleaner
hash_db_cleaner = HashDbCleaner()