"""
Implementazione del Layer 3 della strategia multi-layer: Connection Recovery Sync.

Questo modulo gestisce la sincronizzazione immediata dopo il ripristino della connessione
tra l'agent e il server. Lavora in sinergia con il sistema di heartbeat per rilevare
quando la connessione viene ripristinata dopo un'interruzione.
"""

import logging
import time
import threading
import asyncio
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime, timedelta

# Configurazione logger
logger = logging.getLogger("recovery-sync")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class ConnectionState:
    """Traccia lo stato della connessione con il server"""
    def __init__(self):
        self.connected = False
        self.last_connected = None
        self.last_disconnected = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.reconnection_callbacks = []
        
    def set_connected(self, connected: bool):
        """Aggiorna lo stato della connessione"""
        now = datetime.now()
        
        # Rileva cambio di stato
        if connected and not self.connected:
            # Transizione: disconnesso -> connesso
            self.consecutive_failures = 0
            self.consecutive_successes += 1
            self.last_connected = now
            
            # Trigger callbacks su riconnessione (solo dopo almeno 2 successi consecutivi)
            if self.consecutive_successes >= 2:
                self._trigger_reconnection()
                
        elif not connected and self.connected:
            # Transizione: connesso -> disconnesso
            self.consecutive_successes = 0
            self.consecutive_failures += 1
            self.last_disconnected = now
        
        # Aggiorna stato attuale
        self.connected = connected
        
        if connected:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0
    
    def _trigger_reconnection(self):
        """Attiva i callback di riconnessione"""
        if not self.reconnection_callbacks:
            return
            
        logger.info(f"Riconnessione rilevata. Esecuzione di {len(self.reconnection_callbacks)} callback")
        
        # Dettagli riconnessione
        if self.last_disconnected:
            disconnection_duration = datetime.now() - self.last_disconnected
            logger.info(f"Durata disconnessione: {disconnection_duration}")
        
        # Esegui callback
        for callback in self.reconnection_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Errore nell'esecuzione del callback di riconnessione: {e}")
    
    def add_reconnection_callback(self, callback: Callable[[], None]):
        """Aggiunge un callback da eseguire al ripristino della connessione"""
        self.reconnection_callbacks.append(callback)
        
    def remove_reconnection_callback(self, callback: Callable[[], None]):
        """Rimuove un callback di riconnessione"""
        if callback in self.reconnection_callbacks:
            self.reconnection_callbacks.remove(callback)
            
    def is_stably_connected(self) -> bool:
        """Verifica se la connessione è stabile (almeno 3 successi consecutivi)"""
        return self.connected and self.consecutive_successes >= 3
        
    def is_newly_reconnected(self) -> bool:
        """Verifica se si tratta di una nuova riconnessione"""
        return (self.connected and 
                self.last_disconnected is not None and 
                self.last_connected is not None and 
                self.last_connected > self.last_disconnected)
    
    def get_disconnection_duration(self) -> Optional[timedelta]:
        """Ottieni la durata dell'ultima disconnessione"""
        if self.last_disconnected and self.last_connected and self.last_connected > self.last_disconnected:
            return self.last_connected - self.last_disconnected
        return None

# Istanza globale per tracking della connessione
connection_state = ConnectionState()

class RecoverySync:
    """
    Gestisce la sincronizzazione al ripristino della connessione.
    Implementa il Layer 3 della strategia multi-layer.
    """
    def __init__(self, backend_url: Optional[str] = None, reconciliation_service: Any = None):
        """
        Inizializza il servizio di recovery sync.
        
        Args:
            backend_url: URL del backend PramaIA
            reconciliation_service: Riferimento al servizio di riconciliazione
        """
        # Backend connection
        import os
        self.backend_url = backend_url or f"http://{os.getenv('BACKEND_HOST', 'localhost')}:{os.getenv('BACKEND_PORT', '8000')}"
        
        # Reference to reconciliation service
        self.reconciliation_service = reconciliation_service
        
        # Stato
        self.enabled = False
        self.auto_reconcile = True
        self.monitored_folders = []
        
    def enable(self):
        """Abilita il recovery sync"""
        if self.enabled:
            return
            
        self.enabled = True
        
        # Registra callback per riconnessione
        connection_state.add_reconnection_callback(self._on_reconnection)
        
        logger.info("Recovery sync abilitato")
        
    def disable(self):
        """Disabilita il recovery sync"""
        if not self.enabled:
            return
            
        self.enabled = False
        
        # Rimuovi callback
        connection_state.remove_reconnection_callback(self._on_reconnection)
        
        logger.info("Recovery sync disabilitato")
        
    def _on_reconnection(self):
        """
        Callback eseguito quando viene rilevata una riconnessione.
        Avvia sincronizzazione se necessario.
        """
        if not self.enabled or not self.auto_reconcile:
            return
            
        # Durata disconnessione
        disconnection_duration = connection_state.get_disconnection_duration()
        
        if disconnection_duration:
            minutes = disconnection_duration.total_seconds() / 60
            logger.info(f"Riconnessione rilevata dopo {minutes:.1f} minuti di disconnessione")
            
            # Avvia riconciliazione solo se disconnessione significativa (>1 min)
            if minutes >= 1:
                self._trigger_reconciliation()
            else:
                logger.info(f"Disconnessione breve ({minutes:.1f} min), riconciliazione non necessaria")
        else:
            logger.info("Riconnessione rilevata, avvio riconciliazione...")
            self._trigger_reconciliation()
    
    async def _get_monitored_folders(self) -> List[str]:
        """Ottiene la lista delle cartelle monitorate"""
        # Ottieni da monitor
        try:
            from .control_api import monitor
            if hasattr(monitor, "get_folders"):
                folders = monitor.get_folders()
                if folders:
                    return folders
        except (ImportError, AttributeError):
            pass
        
        # Usa lista predefinita
        return self.monitored_folders
    
    def _trigger_reconciliation(self):
        """Avvia la riconciliazione per tutte le cartelle monitorate"""
        if not self.reconciliation_service:
            logger.error("Impossibile avviare riconciliazione: reconciliation_service non disponibile")
            return
            
        # Crea task asincrono
        async def _reconcile_all_folders():
            folders = await self._get_monitored_folders()
            
            if not folders:
                logger.warning("Nessuna cartella da riconciliare")
                return
                
            logger.info(f"Avvio riconciliazione recovery per {len(folders)} cartelle")
            
            for folder in folders:
                try:
                    logger.info(f"Riconciliazione recovery per: {folder}")
                    if self.reconciliation_service:
                        result = await self.reconciliation_service.reconcile_folder(folder)
                        
                        if result['success']:
                            stats = result.get('stats', {})
                            logger.info(f"Riconciliazione recovery completata per {folder}. "
                                       f"Aggiunti: {stats.get('files_added', 0)}, "
                                       f"Aggiornati: {stats.get('files_updated', 0)}, "
                                       f"Eliminati: {stats.get('files_deleted', 0)}")
                        else:
                            logger.error(f"Riconciliazione recovery fallita per {folder}: {result.get('error')}")
                    else:
                        logger.error("Impossibile eseguire la riconciliazione: reconciliation_service non disponibile")
                        
                except Exception as e:
                    logger.error(f"Errore riconciliazione recovery per {folder}: {e}")
        
        # Esegui task asincrono
        loop = asyncio.get_event_loop()
        task = loop.create_task(_reconcile_all_folders())

# Istanza globale
recovery_sync = RecoverySync()

# Funzione per inizializzare con reconciliation_service
def initialize_recovery_sync(reconciliation_service):
    """Inizializza recovery sync con reconciliation_service"""
    recovery_sync.reconciliation_service = reconciliation_service
    recovery_sync.enable()
    return recovery_sync

# Funzione per aggiornare lo stato della connessione dal registration loop
def update_connection_state(connected: bool):
    """
    Aggiorna lo stato della connessione.
    Da chiamare da registration_loop quando cambia lo stato della connessione.
    """
    connection_state.set_connected(connected)
