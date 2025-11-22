import threading
import time
import json
from watchdog.observers import Observer
import os
from pathlib import Path
from .event_buffer import EventBuffer, event_buffer
from .unified_file_handler import UnifiedFileHandler
from .logger import info, warning, error, debug

class FolderMonitor:
    def __init__(self):
        self.folders = []  # lista di cartelle monitorate
        self.autostart_folders = []  # lista di cartelle con autostart abilitato
        self.document_list = []  # lista di documenti trovati
        self.observers = []
        self.running = False
        self.event_buffer = EventBuffer()
        self.CONFIG_FILE = "monitor_config.json"
        self._load_config()
        
    def remove_folder(self, folder):
        """
        Rimuove una cartella dal monitoraggio e dalla configurazione.
        """
        if folder in self.folders:
            self.folders.remove(folder)
            self._save_config()
            self._notify_server()
            info(f"Path rimossa dalla configurazione: {folder}", details={"folder": folder, "action": "remove_folder"})
            return True
        info(f"Path non trovata in configurazione: {folder}", details={"folder": folder, "action": "remove_folder"})
        return False
        
    def add_folder(self, folder):
        """
        Aggiunge una cartella da monitorare e la salva subito in configurazione, senza avviare la scansione.
        """
        if not os.path.isdir(folder):
            warning(f"Errore: La cartella '{folder}' non esiste.", details={"folder": folder, "action": "add_folder"})
            return False
        if folder not in self.folders:
            self.folders.append(folder)
            self._save_config()
            info(f"Path aggiunta e salvata in configurazione: {folder}", details={"folder": folder, "action": "add_folder"})
            self._notify_server()
            return True
        info(f"Path già presente in configurazione: {folder}", details={"folder": folder, "action": "add_folder"})
        return False

    def _load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.folders = data.get("folders", [])
                    # Carica le configurazioni di autostart, se presenti
                    self.autostart_folders = data.get("autostart_folders", [])
            except Exception as e:
                error(f"Errore caricamento config: {e}", details={"error": str(e), "config_file": self.CONFIG_FILE})
        else:
            self.folders = []
            self.autostart_folders = []

    def _save_config(self):
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "folders": self.folders,
                    "autostart_folders": self.autostart_folders
                }, f)
        except Exception as e:
            error(f"Errore salvataggio config: {e}", details={"error": str(e), "config_file": self.CONFIG_FILE})

    def start(self, folder):
        """
        Avvia il monitoraggio su una cartella specifica.
        Se il monitoraggio per questa cartella è già attivo, lo riavvia.
        """
        if not os.path.isdir(folder):
            warning(f"Errore: La cartella '{folder}' non esiste.", details={"folder": folder, "action": "start_monitoring"})
            return

        # Verifica se c'è già un observer attivo per questa cartella e rimuovilo
        existing_observers = []
        for i, observer in enumerate(self.observers):
            try:
                # Controlla se questo observer monitora già questa cartella
                if hasattr(observer, '_watches'):
                    for watch in observer._watches:
                        if watch.path == folder:
                            existing_observers.append(i)
                            break
            except (AttributeError, RuntimeError):
                # Observer in stato inconsistente, rimuovilo
                existing_observers.append(i)
        
        # Rimuovi observer esistenti per questa cartella (partendo dall'ultimo per non alterare gli indici)
        for i in reversed(existing_observers):
            old_observer = self.observers.pop(i)
            try:
                if hasattr(old_observer, 'is_alive') and old_observer.is_alive():
                    old_observer.stop()
                    old_observer.join(timeout=2)
            except (AttributeError, RuntimeError):
                pass  # Observer già in stato inconsistente
            info(f"Rimosso observer esistente per {folder}")

        # Aggiungi alla configurazione se non presente
        if folder not in self.folders:
            self.folders.append(folder)
            self._save_config()
            self._notify_server()

        info(f"Avvio monitoraggio su: {folder}", details={"folder": folder, "action": "start_monitoring"})

        # Scansione iniziale dei file PDF esistenti
        self._scan_existing_files(folder)

        # Avvio dell'observer - Fix robusto per Python 3.13
        event_handler = UnifiedFileHandler(self.document_list, folder, self.event_buffer)
        observer = Observer()
        observer.schedule(event_handler, folder, recursive=True)
        
        try:
            observer.start()
            info("Observer avviato correttamente.", details={"folder": folder, "observer_type": str(type(observer))})
        except (TypeError, AttributeError) as e:
            error_msg = str(e)
            warning(f"Errore nell'avvio standard dell'observer: {error_msg}. Tentativo workaround Python 3.13...", details={"folder": folder, "error": error_msg})
            
            # Workaround per problemi di compatibilità Python 3.13
            try:
                # Rimuovi schedule precedente
                observer.unschedule_all()
                
                # Reimpostazione manuale dell'observer
                import threading
                from watchdog.observers.api import DEFAULT_OBSERVER_TIMEOUT
                
                observer._watches = set()
                observer._emitter_for_watch = {}
                observer._emitters = set()
                observer._emitters_lock = threading.RLock()
                
                # Usa timeout di default, fallback a 1.0 se non disponibile
                try:
                    observer._timeout = DEFAULT_OBSERVER_TIMEOUT
                except (AttributeError, NameError):
                    observer._timeout = 1.0
                
                # Re-schedule e start manuale
                observer.schedule(event_handler, folder, recursive=True)
                
                # Avvio manuale più sicuro
                if hasattr(observer, '_emitters'):
                    for emitter in observer._emitters:
                        if hasattr(emitter, 'start') and not getattr(emitter, '_started', False):
                            try:
                                emitter.start()
                                emitter._started = True
                            except Exception as emitter_err:
                                warning(f"Emitter per {folder} non avviato: {emitter_err}")
                
                observer._started = True
                info(f"Observer avviato con workaround per {folder}")
                
            except Exception as workaround_err:
                error(f"Impossibile avviare observer anche con workaround: {workaround_err}")
                # Fallback: usa polling observer se disponibile
                try:
                    from watchdog.observers.polling import PollingObserver
                    observer = PollingObserver()
                    observer.schedule(event_handler, folder, recursive=True)
                    observer.start()
                    warning(f"Utilizzando PollingObserver per {folder}")
                except Exception as polling_err:
                    error(f"Impossibile avviare PollingObserver: {polling_err}")
                    raise RuntimeError(f"Impossibile avviare qualsiasi tipo di observer per {folder}")
        
        except Exception as e:
            error(f"Errore inatteso durante avvio observer: {e}")
            raise

        # Aggiungi l'observer alla lista
        self.observers.append(observer)
        self.running = True

        info("Monitoraggio avviato.", details={"folder": folder, "action": "monitoring_started"})
    
    def _scan_existing_files(self, folder):
        """Scansiona i file esistenti nella cartella e li aggiunge alla lista"""
        try:
            # Lista di estensioni di documenti supportati
            supported_extensions = ['.pdf', '.doc', '.docx', '.odt', '.txt', '.xls', '.xlsx', '.ods']
            document_files = []
            
            for file in os.listdir(folder):
                if any(file.lower().endswith(ext) for ext in supported_extensions):
                    document_files.append(file)
                    
            for doc_file in document_files:
                if doc_file not in self.document_list:
                    self.document_list.append(doc_file)
                    info(f"File esistente aggiunto all'indice: {doc_file}", details={
                        "file_name": doc_file,
                        "folder": folder,
                        "action": "add_existing_file"
                    })
            
            info(f"Scansione iniziale completata: {len(document_files)} file trovati", details={
                "folder": folder,
                "file_count": len(document_files),
                "action": "initial_scan"
            })
        except Exception as e:
            error(f"Errore durante la scansione iniziale: {e}", details={
                "folder": folder,
                "error": str(e),
                "action": "initial_scan_error"
            })

    def stop(self):
        """
        Ferma il monitoraggio su tutte le cartelle.
        """
        self.running = False
        for observer in self.observers:
            try:
                if hasattr(observer, 'is_alive') and observer.is_alive():
                    observer.stop()
                    observer.join(timeout=2)
            except (AttributeError, RuntimeError):
                pass  # Observer già in stato inconsistente
        
        # Svuota la lista degli observer
        self.observers = []
        
        info("Monitoraggio fermato.", details={"action": "monitoring_stopped"})
        
        # Notifica al server che il monitoraggio è stato fermato (percorsi aggiornati)
        self._notify_server()
    def _notify_server(self):
        # Import qui per evitare dipendenze circolari
        try:
            import requests
            import os
            
            # Configurazione centralizzata delle porte e URL
            BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
            PLUGIN_PORT = os.getenv("PLUGIN_DOCUMENT_MONITOR_PORT") or os.getenv("PLUGIN_PDF_MONITOR_PORT", "8001")

            # Risolvi l'URL del backend in modo esplicito:
            # 1) usa BACKEND_URL se fornito (consigliato)
            # 2) altrimenti usa BACKEND_BASE_URL
            # 3) fallback a http://localhost:BACKEND_PORT
            backend_base = os.getenv("BACKEND_URL") or os.getenv("BACKEND_BASE_URL")
            if not backend_base:
                backend_base = f"http://localhost:{BACKEND_PORT}"

            PLUGIN_BASE_URL = os.getenv("PLUGIN_DOCUMENT_MONITOR_BASE_URL") or os.getenv("PLUGIN_PDF_MONITOR_BASE_URL") or f"http://localhost:{PLUGIN_PORT}"

            SERVER_URL = f"{backend_base.rstrip('/')}/api/document-monitor/clients/register"
            CLIENT_ID = os.getenv("PLUGIN_CLIENT_ID") or "document-monitor-001"  # nuovo ID
            CLIENT_NAME = os.getenv("PLUGIN_CLIENT_NAME") or "Document Folder Monitor"
            CLIENT_ENDPOINT = PLUGIN_BASE_URL
            payload = {
                "id": CLIENT_ID,
                "name": CLIENT_NAME,
                "endpoint": CLIENT_ENDPOINT,
                "scanPaths": self.get_folders(),
                "online": True
            }
            resp = requests.post(SERVER_URL, json=payload, timeout=5)
            if resp.status_code == 200:
                info("Stato client aggiornato al server.", details={"action": "notify_server", "status_code": 200})
            else:
                warning(f"Errore aggiornamento stato client: {resp.status_code}", details={
                    "action": "notify_server", 
                    "status_code": resp.status_code, 
                    "response_text": resp.text
                })
        except Exception as e:
            error(f"Errore invio stato client: {e}", details={"action": "notify_server", "error": str(e)})

    def set_folder_autostart(self, folder, autostart=True):
        """
        Imposta o rimuove l'autostart per una cartella specifica.
        """
        if folder not in self.folders:
            warning(f"Errore: La cartella '{folder}' non è configurata.", details={"folder": folder, "action": "set_folder_autostart"})
            return False
        
        if autostart and folder not in self.autostart_folders:
            self.autostart_folders.append(folder)
            self._save_config()
            info(f"Autostart abilitato per: {folder}", details={"folder": folder, "action": "enable_autostart"})
            self._notify_server()
            return True
        elif not autostart and folder in self.autostart_folders:
            self.autostart_folders.remove(folder)
            self._save_config()
            info(f"Autostart disabilitato per: {folder}", details={"folder": folder, "action": "disable_autostart"})
            self._notify_server()
            return True
        
        info(f"Nessuna modifica all'autostart per: {folder}", details={"folder": folder, "action": "unchanged_autostart"})
        return False
    
    def is_folder_autostart(self, folder):
        """
        Verifica se una cartella ha l'autostart abilitato.
        """
        return folder in self.autostart_folders
    
    def get_autostart_folders(self):
        """
        Restituisce la lista delle cartelle con autostart abilitato.
        """
        return list(self.autostart_folders)
    
    def start_autostart_folders(self):
        """
        Avvia il monitoraggio di tutte le cartelle configurate con autostart.
        """
        info(f"Avvio monitoraggio cartelle autostart: {self.autostart_folders}", details={"folders": self.autostart_folders, "action": "start_autostart"})
        for folder in self.autostart_folders:
            if os.path.isdir(folder):
                self.start(folder)
            else:
                warning(f"Cartella autostart non trovata: {folder}", details={"folder": folder, "action": "missing_folder"})
        
        # Conta gli observer effettivamente vivi dopo l'avvio
        alive_count = 0
        for observer in self.observers:
            try:
                if hasattr(observer, 'is_alive') and observer.is_alive():
                    alive_count += 1
            except (AttributeError, RuntimeError):
                pass
        
        return alive_count

    def get_documents(self):
        return list(set(self.document_list))

    def is_running(self):
        """
        Verifica se il monitoraggio è attivo.
        Restituisce True se self.running è True, indipendentemente dallo stato degli observer.
        Questo permette una transizione di stato corretta quando start() è chiamato.
        """
        return self.running

    def get_folders(self):
        return list(self.folders)
        
    def get_active_folders(self):
        """
        Restituisce solo le cartelle attivamente monitorate.
        A differenza di get_folders() che restituisce tutte le cartelle configurate,
        questo metodo restituisce solo quelle attualmente monitorate.
        """
        active_folders = []
        for observer in self.observers:
            try:
                if hasattr(observer, '_started') and hasattr(observer, 'is_alive'):
                    try:
                        is_alive = observer.is_alive()
                    except (AttributeError, RuntimeError):
                        is_alive = False
                    
                    if is_alive:
                        # Ottieni la cartella monitorata da questo observer
                        if hasattr(observer, '_watches'):
                            try:
                                for watch in observer._watches:
                                    path = watch.path
                                    if path not in active_folders:
                                        active_folders.append(path)
                            except (AttributeError, TypeError):
                                # _watches non è iterabile o non esiste
                                continue
            except (AttributeError, RuntimeError):
                # Observer in stato inconsistente, ignora
                continue
        return active_folders
    
    def _get_observer_health(self):
        """
        Restituisce un rapporto sulla salute degli observer per debug.
        """
        health = {
            "total_observers": len(self.observers),
            "running_flag": self.running,
            "observers_status": []
        }
        
        for i, observer in enumerate(self.observers):
            status = {
                "index": i,
                "type": str(type(observer).__name__),
                "has_is_alive": hasattr(observer, 'is_alive'),
                "has_started": hasattr(observer, '_started'),
                "is_alive": False,
                "error": None
            }
            
            try:
                if hasattr(observer, 'is_alive'):
                    status["is_alive"] = observer.is_alive()
            except Exception as e:
                status["error"] = str(e)
            
            health["observers_status"].append(status)
        
        return health
        
    def refresh_monitoring(self):
        """
        Forza un refresh del monitoraggio, riavviando gli observer fermi
        e verificando che tutte le cartelle siano correttamente monitorate.
        Utile dopo lunghi periodi di inattività.
        """
        info("Avvio refresh del monitoraggio...", details={"action": "refresh_monitoring"})
        
        # Controlla observer fermi
        for i, observer in enumerate(self.observers):
            if not observer.is_alive():
                warning(f"Observer {i} non attivo, riavvio...", details={"action": "restart_observer"})
                try:
                    # Ottieni informazioni sull'observer prima di ricrearlo
                    watches = []
                    for watch in observer._watches:
                        watches.append({
                            "path": watch.path,
                            "recursive": watch.recursive
                        })
                    
                    # Crea un nuovo observer
                    new_observer = Observer()
                    for watch_info in watches:
                        path = watch_info["path"]
                        event_handler = UnifiedFileHandler(self.document_list, path, self.event_buffer)
                        new_observer.schedule(event_handler, path, recursive=watch_info["recursive"])
                    
                    # Avvia il nuovo observer e sostituisci il vecchio
                    new_observer.start()
                    self.observers[i] = new_observer
                    info(f"Observer {i} riavviato con successo", details={"action": "observer_restarted"})
                except Exception as e:
                    error(f"Errore durante riavvio observer {i}: {e}", details={"error": str(e), "action": "restart_error"})
        
        # Verifica cartelle attive
        active_folders = self.get_active_folders()
        for folder in self.folders:
            if folder not in active_folders and os.path.isdir(folder):
                warning(f"Cartella '{folder}' non monitorata, riavvio...", details={"folder": folder, "action": "restart_folder"})
                try:
                    self.start(folder)
                except Exception as e:
                    error(f"Errore durante riavvio monitoraggio per '{folder}': {e}", 
                         details={"folder": folder, "error": str(e), "action": "restart_folder_error"})
        
        # Aggiorna stato running
        self.running = any(observer.is_alive() for observer in self.observers)
        info(f"Refresh monitoraggio completato. Stato: {'attivo' if self.running else 'inattivo'}", 
             details={"running": self.running, "active_folders": len(active_folders), "action": "refresh_completed"})
        
        return self.running
