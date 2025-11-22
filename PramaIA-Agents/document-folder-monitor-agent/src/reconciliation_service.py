"""
Servizio di riconciliazione per garantire la sincronizzazione
tra il filesystem locale e il vectorstore remoto.

Questo modulo implementa il Layer 2 della strategia multi-layer:
- Scan periodico del filesystem
- Confronto con lo stato del vectorstore
- Sincronizzazione delle differenze
"""
import os
import time
import asyncio
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any
from .unified_file_handler import UnifiedFileHandler

# Importiamo le classi dal nuovo file separato
from .file_hash_tracker import FileInfo, FolderState, FileHashTracker

# Importa il logger personalizzato
from .logger import info, warning, error, debug

class ReconciliationService:
    """
    Servizio che gestisce la riconciliazione tra filesystem e vectorstore.
    """
    def __init__(self, backend_url: str = "", sync_interval: int = 3600):
        """
        Inizializza il servizio di riconciliazione.
        
        Args:
            backend_url: URL del backend PramaIA
            sync_interval: Intervallo in secondi tra sincronizzazioni periodiche (default: 1 ora)
        """
        # Backend connection: usa la logica CORRETTA per il backend
        import os
        import requests
        if backend_url:
            self.backend_url = backend_url
        else:
            backend_base = os.getenv("BACKEND_URL")
            if not backend_base:
                backend_host = os.getenv("BACKEND_HOST", "localhost")
                backend_port = os.getenv("BACKEND_PORT", "8000")
                backend_base = f"http://{backend_host}:{backend_port}"
            self.backend_url = backend_base
        
        # Components
        self.hash_tracker = FileHashTracker()
        self.sync_interval = sync_interval
        self.running = False
        self.last_sync = {}  # folder_path -> datetime
        self.sync_task = None
        
    async def start(self):
        """Avvia il servizio di riconciliazione periodica"""
        if self.running:
            warning("Reconciliation service already running", details={"service": "reconciliation"})
            return
            
        self.running = True
        info(f"Starting reconciliation service with interval {self.sync_interval}s", details={"interval": self.sync_interval, "service": "reconciliation"})
        
        # Avvia task asincrono per sync periodico
        self.sync_task = asyncio.create_task(self._periodic_sync())
        
    async def stop(self):
        """Ferma il servizio di riconciliazione"""
        if not self.running:
            return
            
        self.running = False
        info("Stopping reconciliation service", details={"service": "reconciliation"})
        
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
        
    async def _periodic_sync(self):
        """Task asincrono per sync periodico di tutte le cartelle monitorate"""
        while self.running:
            try:
                # Ottieni lista cartelle attivamente monitorate
                monitored_folders = await self._get_monitored_folders()
                
                if not monitored_folders:
                    info("Nessuna cartella monitorata attivamente trovata, sincronizzazione saltata", details={"service": "reconciliation"})
                else:
                    # Log delle cartelle che saranno sincronizzate
                    info(f"Sincronizzazione periodica per {len(monitored_folders)} cartelle attivamente monitorate", details={"folder_count": len(monitored_folders), "service": "reconciliation"})
                    
                    # Sync ogni cartella
                    for folder in monitored_folders:
                        try:
                            info(f"Avvio sincronizzazione periodica per cartella: {folder}", details={"folder": folder, "service": "reconciliation"})
                            await self.reconcile_folder(folder)
                        except Exception as e:
                            error(f"Errore sincronizzazione cartella {folder}: {e}", details={"folder": folder, "error": str(e), "service": "reconciliation"})
                
                # Aggiorna timestamp ultimo sync
                self.last_sync["periodic"] = datetime.now()
                
            except Exception as e:
                error(f"Errore nella sincronizzazione periodica: {e}", details={"error": str(e), "service": "reconciliation"})
                
            # Attendi prossimo intervallo
            await asyncio.sleep(self.sync_interval)
    
    async def _get_monitored_folders(self) -> List[str]:
        """Ottiene la lista delle cartelle attivamente monitorate"""
        # Importa dinamicamente per evitare import circolari
        try:
            from .control_api import monitor
            # Usa get_active_folders() per ottenere solo le cartelle attivamente monitorate
            if hasattr(monitor, "get_active_folders"):
                active_folders = monitor.get_active_folders()
                if active_folders:
                    info(f"Found {len(active_folders)} actively monitored folders", details={"folder_count": len(active_folders), "service": "reconciliation"})
                    return active_folders
                else:
                    info("No actively monitored folders found", details={"service": "reconciliation"})
                    
            # Fallback a get_folders() solo se necessario
            elif hasattr(monitor, "get_folders"):
                warning("Using get_folders() fallback - may include inactive folders", details={"service": "reconciliation"})
                return monitor.get_folders()
        except (ImportError, AttributeError) as e:
            error(f"Error accessing monitor: {e}", details={"error": str(e), "service": "reconciliation"})
            pass
        
        # Fallback: leggi da config
        try:
            import json
            with open("monitor_config.json", "r") as f:
                config = json.load(f)
                return config.get("folders", [])
        except:
            pass
            
        return []
    
    async def scan_filesystem(self, folder_path: str) -> FolderState:
        """
        Scansiona il filesystem per ottenere lo stato attuale.
        
        Args:
            folder_path: Percorso della cartella da scansionare
            
        Returns:
            FolderState con tutti i file trovati
        """
        info(f"Scanning filesystem for folder: {folder_path}", details={"folder": folder_path, "service": "reconciliation"})
        
        folder_state = FolderState(folder_path)
        
        try:
            for root, _, files in os.walk(folder_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    
                    try:
                        # Ottieni informazioni file
                        stat = os.stat(file_path)
                        
                        # Calcola hash solo se necessario
                        hash_value = self.hash_tracker.calculate_file_hash(file_path)
                        
                        # Crea FileInfo
                        file_info = FileInfo(
                            path=file_path,
                            size=stat.st_size,
                            last_modified=stat.st_mtime,
                            hash_value=hash_value
                        )
                        
                        # Aggiungi allo stato
                        folder_state.add_file(file_info)
                        
                    except (IOError, OSError) as e:
                        warning(f"Error processing file {file_path}: {e}", details={"file_path": file_path, "error": str(e), "service": "reconciliation"})
            
            info(f"Filesystem scan completed. Found {len(folder_state.files)} files", details={"folder": folder_path, "file_count": len(folder_state.files), "service": "reconciliation"})
            
        except Exception as e:
            error(f"Error scanning filesystem {folder_path}: {e}", details={"folder": folder_path, "error": str(e), "service": "reconciliation"})
            
        return folder_state
    
    async def get_vectorstore_state(self, folder_path: str) -> FolderState:
        """
        Ottiene lo stato attuale del vectorstore per una cartella.
        Utilizza l'API del backend per ottenere lo stato.
        
        Args:
            folder_path: Percorso della cartella
            
        Returns:
            FolderState con tutti i file nel vectorstore
        """
        info(f"Getting vectorstore state for folder: {folder_path}", details={"folder": folder_path, "service": "reconciliation"})
        
        folder_state = FolderState(folder_path)
        
        try:
            # Costruisci URL per API
            import requests
            
            # Normalizza path per API
            norm_path = folder_path.replace("\\", "/")
            encoded_path = urllib.parse.quote(norm_path)
            
            url = f"{self.backend_url.rstrip('/')}/api/folders/state?path={encoded_path}"
            
            # Fai richiesta API
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Processa risposta
                files = data.get("files", {})
                for file_path, file_data in files.items():
                    file_info = FileInfo(
                        path=file_path,
                        size=file_data.get("size", 0),
                        last_modified=file_data.get("last_modified", 0),
                        hash_value=file_data.get("hash", "")
                    )
                    file_info.vectorstore_id = file_data.get("id")
                    
                    folder_state.add_file(file_info)
                    
                info(f"Vectorstore state retrieved. Found {len(folder_state.files)} files", details={"folder": folder_path, "file_count": len(folder_state.files), "service": "reconciliation"})
                
            else:
                error(f"Error getting vectorstore state: {response.status_code} - {response.text}", details={"folder": folder_path, "status_code": response.status_code, "response": response.text, "service": "reconciliation"})
                
        except Exception as e:
            error(f"Error getting vectorstore state for {folder_path}: {e}", details={"folder": folder_path, "error": str(e), "service": "reconciliation"})
            
        return folder_state
    
    async def calculate_diff(self, fs_state: FolderState, vs_state: FolderState) -> Dict[str, Any]:
        """
        Calcola le differenze tra filesystem e vectorstore.
        
        Args:
            fs_state: Stato del filesystem
            vs_state: Stato del vectorstore
            
        Returns:
            Dict con le differenze
        """
        info("Calculating differences between filesystem and vectorstore", details={"folder": fs_state.folder_path, "service": "reconciliation"})
        
        fs_paths = fs_state.get_file_paths()
        vs_paths = vs_state.get_file_paths()
        
        # File presenti nel filesystem ma non nel vectorstore
        missing_in_vs = fs_paths - vs_paths
        
        # File presenti nel vectorstore ma non nel filesystem
        missing_in_fs = vs_paths - fs_paths
        
        # File presenti in entrambi ma con contenuto diverso
        content_changed = []
        
        # File con metadati cambiati
        metadata_changed = []
        
        # Controlla file presenti in entrambi
        for path in fs_paths & vs_paths:
            fs_file = fs_state.files[path]
            vs_file = vs_state.files[path]
            
            # Controlla hash per rilevare cambiamenti contenuto
            if fs_file.hash_value != vs_file.hash_value:
                content_changed.append(path)
                
            # Controlla size e last_modified
            elif fs_file.size != vs_file.size or abs(fs_file.last_modified - vs_file.last_modified) > 1:
                metadata_changed.append(path)
        
        diff = {
            'missing_in_vs': list(missing_in_vs),
            'missing_in_fs': list(missing_in_fs),
            'content_changed': content_changed,
            'metadata_changed': metadata_changed
        }
        
        # Log riassuntivo
        info(f"Diff summary: {len(missing_in_vs)} new files, {len(missing_in_fs)} deleted files, "
                    f"{len(content_changed)} modified files, {len(metadata_changed)} metadata changes", 
                    details={
                        "folder": fs_state.folder_path,
                        "new_files": len(missing_in_vs),
                        "deleted_files": len(missing_in_fs),
                        "modified_files": len(content_changed),
                        "metadata_changes": len(metadata_changed),
                        "service": "reconciliation"
                    })
        
        return diff
    
    async def reconcile_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Esegue la riconciliazione di una cartella.
        
        Args:
            folder_path: Percorso della cartella da riconciliare
            
        Returns:
            Dict con risultati della riconciliazione
        """
        info(f"Starting reconciliation for folder: {folder_path}", details={"folder": folder_path, "service": "reconciliation"})
        
        start_time = time.time()
        result = {
            'success': False,
            'folder': folder_path,
            'timestamp': datetime.now().isoformat(),
            'actions': [],
            'stats': {}
        }
        
        try:
            # 1. Scan filesystem
            fs_state = await self.scan_filesystem(folder_path)
            
            # 2. Get vectorstore state
            vs_state = await self.get_vectorstore_state(folder_path)
            
            # 3. Calculate diff
            diff = await self.calculate_diff(fs_state, vs_state)
            
            # 4. Apply changes
            actions = await self.apply_sync_actions(folder_path, diff, fs_state)
            
            # 5. Update result
            result['success'] = True
            result['actions'] = actions
            result['stats'] = {
                'files_added': len(diff['missing_in_vs']),
                'files_deleted': len(diff['missing_in_fs']),
                'files_updated': len(diff['content_changed']),
                'metadata_updated': len(diff['metadata_changed']),
                'total_changes': len(diff['missing_in_vs']) + len(diff['missing_in_fs']) + 
                                 len(diff['content_changed']) + len(diff['metadata_changed']),
                'duration_seconds': round(time.time() - start_time, 2)
            }
            
            # 6. Update last sync timestamp
            self.last_sync[folder_path] = datetime.now()
            
            info(f"Reconciliation completed successfully for {folder_path}. "
                f"Duration: {result['stats']['duration_seconds']}s. "
                f"Changes: {result['stats']['total_changes']}", 
                details={
                    "folder": folder_path,
                    "duration": result['stats']['duration_seconds'],
                    "changes": result['stats']['total_changes'],
                    "service": "reconciliation"
                })
            
        except Exception as e:
            error(f"Error during reconciliation of {folder_path}: {e}", details={"folder": folder_path, "error": str(e), "service": "reconciliation"})
            result['error'] = str(e)
            
        return result
    
    async def apply_sync_actions(self, folder_path: str, diff: Dict[str, List[str]], 
                                fs_state: FolderState) -> List[Dict[str, Any]]:
        """
        Applica le azioni di sincronizzazione basate sulle differenze.
        
        Args:
            folder_path: Percorso della cartella
            diff: Differenze calcolate
            fs_state: Stato del filesystem
            
        Returns:
            Lista di azioni eseguite
        """
        actions = []
        
        # Verifica la disponibilità dell'handler
        handler_available = True
        
        # 1. Aggiungi file mancanti nel vectorstore
        for file_path in diff['missing_in_vs']:
            try:
                info(f"Adding missing file to vectorstore: {file_path}", details={"file_path": file_path, "service": "reconciliation"})
                
                if handler_available:
                    # Usa l'handler esistente per consistency
                    from .event_buffer import event_buffer
                    dummy_list = []
                    handler = UnifiedFileHandler(dummy_list, folder_path, event_buffer)
                    
                    # Simula evento created
                    file_info = fs_state.files[file_path]
                    filter_decision = {'action': 'process_full', 'should_upload': True, 
                                     'extract_metadata': True, 'should_process_content': True}
                    
                    # Invia al backend
                    handler._send_file_to_backend(file_path, 'reconciliation_add', filter_decision)
                    
                else:
                    # Chiamata API diretta
                    import requests
                    
                    BACKEND_URL = f"{self.backend_url.rstrip('/')}/api/document-monitor/upload/"
                    
                    with open(file_path, "rb") as f:
                        files = {"file": (os.path.basename(file_path), f)}
                        data = {
                            "action": "reconciliation_add",
                            "full_path": file_path,
                            "relative_path": os.path.relpath(file_path, folder_path),
                        }
                        
                        resp = requests.post(BACKEND_URL, files=files, data=data, timeout=30)
                        
                    if resp.status_code != 200:
                        raise Exception(f"API error: {resp.status_code} - {resp.text}")
                
                # Registra azione
                actions.append({
                    'action': 'add',
                    'file': file_path,
                    'success': True
                })
                
            except Exception as e:
                error(f"Error adding file {file_path}: {e}", details={"file_path": file_path, "error": str(e), "service": "reconciliation"})
                actions.append({
                    'action': 'add',
                    'file': file_path,
                    'success': False,
                    'error': str(e)
                })
        
        # 2. Rimuovi file mancanti nel filesystem
        for file_path in diff['missing_in_fs']:
            try:
                info(f"Removing file from vectorstore: {file_path}", details={"file_path": file_path, "service": "reconciliation"})
                
                if handler_available:
                    # Usa handler esistente
                    dummy_list = []
                    from .event_buffer import event_buffer
                    handler = UnifiedFileHandler(dummy_list, folder_path, event_buffer)
                    
                    # Simula evento deleted
                    handler._delete_file_from_backend(os.path.basename(file_path))
                    
                else:
                    # Chiamata API diretta
                    import requests
                    
                    DELETE_URL = f"{self.backend_url.rstrip('/')}/api/documents/{os.path.basename(file_path)}"
                    
                    resp = requests.delete(DELETE_URL, timeout=10)
                    
                    if resp.status_code not in [200, 204, 404]:
                        raise Exception(f"API error: {resp.status_code} - {resp.text}")
                
                # Registra azione
                actions.append({
                    'action': 'delete',
                    'file': file_path,
                    'success': True
                })
                
            except Exception as e:
                error(f"Error deleting file {file_path}: {e}", details={"file_path": file_path, "error": str(e), "service": "reconciliation"})
                actions.append({
                    'action': 'delete',
                    'file': file_path,
                    'success': False,
                    'error': str(e)
                })
        
        # 3. Aggiorna file con contenuto cambiato
        for file_path in diff['content_changed']:
            try:
                info(f"Updating modified file in vectorstore: {file_path}", details={"file_path": file_path, "service": "reconciliation"})
                
                # Tratta come add (rimuovi e aggiungi)
                # Rimuovi prima
                if handler_available:
                    dummy_list = []
                    from .event_buffer import event_buffer
                    handler = UnifiedFileHandler(dummy_list, folder_path, event_buffer)
                    
                    # Simula evento modified
                    file_info = fs_state.files[file_path]
                    filter_decision = {'action': 'process_full', 'should_upload': True, 
                                     'extract_metadata': True, 'should_process_content': True}
                    
                    # Rimuovi vecchio
                    handler._delete_file_from_backend(os.path.basename(file_path))
                    
                    # Aggiungi nuovo
                    handler._send_file_to_backend(file_path, 'reconciliation_update', filter_decision)
                    
                else:
                    # Chiamata API diretta
                    import requests
                    
                    # Rimuovi
                    DELETE_URL = f"{self.backend_url.rstrip('/')}/api/documents/{os.path.basename(file_path)}"
                    requests.delete(DELETE_URL, timeout=10)
                    
                    # Aggiungi nuovo
                    BACKEND_URL = f"{self.backend_url.rstrip('/')}/api/document-monitor/upload/"
                    
                    with open(file_path, "rb") as f:
                        files = {"file": (os.path.basename(file_path), f)}
                        data = {
                            "action": "reconciliation_update",
                            "full_path": file_path,
                            "relative_path": os.path.relpath(file_path, folder_path),
                        }
                        
                        resp = requests.post(BACKEND_URL, files=files, data=data, timeout=30)
                        
                    if resp.status_code != 200:
                        raise Exception(f"API error: {resp.status_code} - {resp.text}")
                
                # Registra azione
                actions.append({
                    'action': 'update',
                    'file': file_path,
                    'success': True
                })
                
            except Exception as e:
                error(f"Error updating file {file_path}: {e}", details={"file_path": file_path, "error": str(e), "service": "reconciliation"})
                actions.append({
                    'action': 'update',
                    'file': file_path,
                    'success': False,
                    'error': str(e)
                })
        
        # 4. Aggiorna metadati
        # Per ora, trattiamo metadati come file cambiati per semplicità
        for file_path in diff['metadata_changed']:
            try:
                info(f"Updating metadata in vectorstore: {file_path}", details={"file_path": file_path, "service": "reconciliation"})
                
                # Stessa logica di content_changed
                if handler_available:
                    dummy_list = []
                    from .event_buffer import event_buffer
                    handler = UnifiedFileHandler(dummy_list, folder_path, event_buffer)
                    
                    # Simula evento modified
                    file_info = fs_state.files[file_path]
                    filter_decision = {'action': 'process_full', 'should_upload': True, 
                                     'extract_metadata': True, 'should_process_content': True}
                    
                    # Update
                    handler._send_file_to_backend(file_path, 'reconciliation_metadata', filter_decision)
                    
                else:
                    # Chiamata API diretta
                    import requests
                    
                    BACKEND_URL = f"{self.backend_url.rstrip('/')}/api/document-monitor/upload/"
                    
                    with open(file_path, "rb") as f:
                        files = {"file": (os.path.basename(file_path), f)}
                        data = {
                            "action": "reconciliation_metadata",
                            "full_path": file_path,
                            "relative_path": os.path.relpath(file_path, folder_path),
                        }
                        
                        resp = requests.post(BACKEND_URL, files=files, data=data, timeout=30)
                        
                    if resp.status_code != 200:
                        raise Exception(f"API error: {resp.status_code} - {resp.text}")
                
                # Registra azione
                actions.append({
                    'action': 'metadata',
                    'file': file_path,
                    'success': True
                })
                
            except Exception as e:
                error(f"Error updating metadata for {file_path}: {e}", details={"file_path": file_path, "error": str(e), "service": "reconciliation"})
                actions.append({
                    'action': 'metadata',
                    'file': file_path,
                    'success': False,
                    'error': str(e)
                })
        
        # 5. Aggiorna hash locali per tutti i file processati
        for action in actions:
            if action['success'] and action['action'] in ['add', 'update', 'metadata']:
                file_path = action['file']
                if file_path in fs_state.files:
                    # Aggiorna hash nel tracker
                    self.hash_tracker.update_file_hash(fs_state.files[file_path])
        
        return actions

# Istanza globale
reconciliation_service = ReconciliationService()

async def start_reconciliation_service():
    """Avvia il servizio di riconciliazione"""
    await reconciliation_service.start()

async def trigger_reconciliation(folder_path: str):
    """Trigger manuale di riconciliazione per una cartella"""
    return await reconciliation_service.reconcile_folder(folder_path)
