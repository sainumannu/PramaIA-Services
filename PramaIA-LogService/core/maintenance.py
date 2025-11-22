"""
Modulo per la manutenzione programmata del LogService.
Gestisce la compressione dei log vecchi e la pulizia dei log e degli archivi.
"""

import threading
import time
import logging
from datetime import datetime, timedelta

from core.log_manager import LogManager
from core.config import get_settings

logger = logging.getLogger("PramaIA-LogService.Maintenance")

class MaintenanceScheduler:
    """
    Scheduler per eseguire operazioni di manutenzione a intervalli regolari.
    """
    
    def __init__(self, interval_hours=24):
        """
        Inizializza lo scheduler.
        
        Args:
            interval_hours: Intervallo in ore tra le esecuzioni
        """
        self.interval_hours = interval_hours
        self.log_manager = LogManager()
        self.running = False
        self.thread = None
        self.last_run = None
    
    def start(self):
        """
        Avvia lo scheduler in un thread separato.
        """
        if self.running:
            logger.warning("Lo scheduler di manutenzione è già in esecuzione")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"Scheduler di manutenzione avviato. Prossima esecuzione tra {self.interval_hours} ore")
    
    def stop(self):
        """
        Ferma lo scheduler.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            logger.info("Scheduler di manutenzione fermato")
    
    def _run(self):
        """
        Esegue lo scheduler.
        """
        # Esegui la manutenzione all'avvio
        self._perform_maintenance()
        
        while self.running:
            # Calcola il tempo di attesa fino alla prossima esecuzione
            if self.last_run:
                next_run = self.last_run + timedelta(hours=self.interval_hours)
                now = datetime.now()
                if next_run > now:
                    # Calcola i secondi da attendere
                    seconds_to_wait = (next_run - now).total_seconds()
                    # Attendi, controllando periodicamente se lo scheduler è stato fermato
                    for _ in range(int(seconds_to_wait / 10)):
                        if not self.running:
                            break
                        time.sleep(10)
                    # Attendi i secondi rimanenti
                    if self.running:
                        time.sleep(seconds_to_wait % 10)
            
            if self.running:
                self._perform_maintenance()
    
    def _perform_maintenance(self):
        """
        Esegue le operazioni di manutenzione.
        """
        try:
            logger.info("Avvio delle operazioni di manutenzione")
            
            # Esegui la manutenzione
            self.log_manager.run_maintenance()
            
            self.last_run = datetime.now()
            logger.info(f"Manutenzione completata. Prossima esecuzione: {self.last_run + timedelta(hours=self.interval_hours)}")
        except Exception as e:
            logger.error(f"Errore durante la manutenzione: {str(e)}", exc_info=True)

# Singleton dello scheduler
_scheduler = None

def get_maintenance_scheduler():
    """
    Ottiene l'istanza singleton dello scheduler di manutenzione.
    
    Returns:
        MaintenanceScheduler
    """
    global _scheduler
    if _scheduler is None:
        # Configurazione dello scheduler
        settings = get_settings()
        # Intervallo di esecuzione predefinito: ogni 24 ore
        _scheduler = MaintenanceScheduler(interval_hours=24)
    
    return _scheduler
