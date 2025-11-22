"""
Document Monitor Event Source for PramaIA PDK
Monitors a folder for d                api_key=os.environ.get("PRAMAIALOG_API_KEY", "document_monitor_api_key"),
                project=LogProject.TOOLS,
                module="document_monitor_event_source",ment file changes and emits events
"""

import asyncio
import json
import os
import sys
import time
import hashlib
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from typing import Dict, Any, Optional

# Preferisci un wrapper `logger` locale (se presente). Altrimenti, usa il client
# `PramaIALogger` quando disponibile. Se non esiste nessuno dei due, usiamo il
# fallback basato su stdout/stderr.
logger = None
logging_enabled = False
try:
    # Prova ad importare un modulo `logger` locale (package-level o in PYTHONPATH)
    try:
        # primo tentativo: import relativo se il modulo è bundlato col package
        from . import logger as _local_logger_mod  # type: ignore
    except Exception:
        try:
            import logger as _local_logger_mod  # type: ignore
        except Exception:
            _local_logger_mod = None

    if _local_logger_mod:
        # Crea un adattatore minimale che espone le stesse API usate nel file
        class _Adapter:
            def info(self, msg, details=None, context=None):
                try:
                    _local_logger_mod.info(msg, details=details, context=context)
                except Exception:
                    print("[INFO]", msg)

            def debug(self, msg, details=None, context=None):
                try:
                    _local_logger_mod.debug(msg, details=details, context=context)
                except Exception:
                    print("[DEBUG]", msg)

            def warning(self, msg, details=None, context=None):
                try:
                    _local_logger_mod.warning(msg, details=details, context=context)
                except Exception:
                    print("[WARNING]", msg)

            def error(self, msg, details=None, context=None):
                try:
                    _local_logger_mod.error(msg, details=details, context=context)
                except Exception:
                    print("[ERROR]", msg)

            def flush(self):
                try:
                    getattr(_local_logger_mod, 'flush', lambda: None)()
                except Exception:
                    pass

        logger = _Adapter()
        logging_enabled = True
    else:
        # Fallback: prova a caricare il client pramaialog
        try:
            from pramaialog import PramaIALogger, LogLevel, LogProject
            # Configurazione logger centralizzato
            logger = PramaIALogger(
                api_key=os.environ.get("PRAMAIALOG_API_KEY", "document_monitor_api_key"),
                project=LogProject.PDK,
                module="document_monitor_event_source",
                host=os.environ.get("PRAMAIALOG_HOST", "http://localhost:8081")
            )
            logging_enabled = True
        except ImportError:
            # Nessun client disponibile: fallback su stdout/stderr
            logging_enabled = False
            logging.getLogger(__name__).warning("[Document Monitor] PramaIALogger non disponibile, utilizzo logger locale come fallback")
except Exception:
    logging_enabled = False

class DocumentEventHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, event_source):
        self.event_source = event_source
        self.debounce_cache = {}
        
    def on_created(self, event):
        if not event.is_directory:
            self._handle_file_event('created', event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file_event('modified', event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._handle_file_event('deleted', event.src_path)
    
    def _handle_file_event(self, event_type: str, file_path: str):
        """Handle file system event with debouncing"""
        try:
            # Check if file should be processed
            if not self.event_source._should_process_file(file_path):
                return
            
            # Debouncing: ignore rapid successive events for the same file
            debounce_time = self.event_source.config.get('debounce_time', 2)
            current_time = time.time()
            cache_key = f"{file_path}:{event_type}"
            
            if cache_key in self.debounce_cache:
                if current_time - self.debounce_cache[cache_key] < debounce_time:
                    return
            
            self.debounce_cache[cache_key] = current_time
            
            # Schedule event processing
            asyncio.create_task(self.event_source._process_file_event(event_type, file_path))
            
        except Exception as e:
            if logging_enabled:
                logger.error(
                    "Errore durante la gestione dell'evento file",
                    details={
                        "event_type": event_type,
                        "file_path": file_path,
                        "error": str(e)
                    }
                )
            else:
                print(f"Error handling file event: {e}", file=sys.stderr)

class EventSource:
    """Document Monitor Event Source for PDK"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[DocumentEventHandler] = None
        self.running = False
        self.events_emitted = 0
        self.last_activity = None
        
    async def initialize(self, config: Dict[str, Any]):
        """Initialize the event source with configuration"""
        self.config = config
        
        # Validate required configuration
        if not config.get('monitor_path'):
            raise ValueError("monitor_path is required in configuration")
        
        monitor_path = Path(config['monitor_path'])
        if not monitor_path.exists():
            raise ValueError(f"Monitor path does not exist: {monitor_path}")
        
        if not monitor_path.is_dir():
            raise ValueError(f"Monitor path is not a directory: {monitor_path}")
        
        if logging_enabled:
            logger.info(
                "Document Monitor inizializzato",
                details={"config": config}
            )
        else:
            print(f"[Document Monitor] Initialized with config: {config}")
        
    async def start(self):
        """Start monitoring the folder"""
        if self.running:
            if logging_enabled:
                logger.info("Document Monitor già in esecuzione")
            else:
                print("[Document Monitor] Already running")
            return
        
        try:
            monitor_path = self.config['monitor_path']
            recursive = self.config.get('recursive', True)
            
            if logging_enabled:
                logger.info(
                    "Avvio monitoraggio cartella",
                    details={
                        "monitor_path": monitor_path,
                        "recursive": recursive
                    }
                )
            else:
                print(f"[Document Monitor] Starting monitoring of: {monitor_path}")
                print(f"[Document Monitor] Recursive: {recursive}")
            
            # Create event handler and observer
            self.event_handler = DocumentEventHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                self.event_handler, 
                monitor_path, 
                recursive=recursive
            )
            
            # Start observer
            self.observer.start()
            self.running = True
            
            if logging_enabled:
                logger.info("Document Monitor avviato con successo")
            else:
                print("[Document Monitor] Started successfully")
            
            # Emit initial scan events for existing files
            await self._initial_scan()
            
        except Exception as e:
            if logging_enabled:
                logger.error(
                    "Errore durante l'avvio del monitoraggio",
                    details={
                        "error": str(e),
                        "monitor_path": self.config.get('monitor_path')
                    }
                )
            else:
                print(f"[Document Monitor] Error starting: {e}", file=sys.stderr)
            await self.stop()
            raise
    
    async def stop(self):
        """Stop monitoring"""
        if not self.running:
            return
        
        if logging_enabled:
            logger.info("Arresto Document Monitor in corso")
        else:
            print("[Document Monitor] Stopping...")
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        self.event_handler = None
        self.running = False
        
        if logging_enabled:
            logger.info("Document Monitor arrestato")
            # Assicuriamoci che tutti i log vengano inviati
            logger.flush()
        else:
            print("[Document Monitor] Stopped")
    
    async def _initial_scan(self):
        """Perform initial scan of existing files"""
        try:
            monitor_path = Path(self.config['monitor_path'])
            file_extensions = self.config.get('file_extensions', ['.pdf', '.doc', '.docx', '.odt', '.txt', '.xls', '.xlsx', '.ods'])
            recursive = self.config.get('recursive', True)
            
            if logging_enabled:
                logger.info(
                    "Avvio scansione iniziale",
                    details={
                        "monitor_path": str(monitor_path),
                        "recursive": recursive,
                        "file_extensions": file_extensions
                    }
                )
            else:
                print(f"[Document Monitor] Performing initial scan of {monitor_path}")
            
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in monitor_path.glob(pattern):
                if file_path.is_file() and self._should_process_file(str(file_path)):
                    await self._process_file_event('existing', str(file_path))
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(0.1)
        
        except Exception as e:
            if logging_enabled:
                logger.error(
                    "Errore durante la scansione iniziale",
                    details={
                        "error": str(e),
                        "monitor_path": str(self.config.get('monitor_path', ''))
                    }
                )
            else:
                print(f"[Document Monitor] Error in initial scan: {e}", file=sys.stderr)
    
    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed based on configuration"""
        try:
            path = Path(file_path)
            
            # Check file extension
            file_extensions = self.config.get('file_extensions', ['.pdf', '.doc', '.docx', '.odt', '.txt', '.xls', '.xlsx', '.ods'])
            if not any(path.suffix.lower() == ext.lower() for ext in file_extensions):
                return False
            
            # Check hidden files
            if self.config.get('ignore_hidden', True) and path.name.startswith('.'):
                return False
            
            # Check file size (only for existing files)
            if path.exists():
                max_size_mb = self.config.get('max_file_size', 100)
                if max_size_mb > 0:
                    file_size_mb = path.stat().st_size / (1024 * 1024)
                    if file_size_mb > max_size_mb:
                        if logging_enabled:
                            logger.warning(
                                "File ignorato: dimensione eccessiva",
                                details={
                                    "file_path": file_path,
                                    "file_size_mb": f"{file_size_mb:.1f}",
                                    "max_size_mb": max_size_mb
                                }
                            )
                        else:
                            print(f"[Document Monitor] Skipping large file ({file_size_mb:.1f}MB): {file_path}")
                        return False
            
            return True
            
        except Exception as e:
            if logging_enabled:
                logger.error(
                    "Errore durante il controllo del file",
                    details={
                        "file_path": file_path,
                        "error": str(e)
                    }
                )
            else:
                print(f"[Document Monitor] Error checking file {file_path}: {e}", file=sys.stderr)
            return False
    
    async def _process_file_event(self, event_type: str, file_path: str):
        """Process a file event and emit appropriate event"""
        try:
            path = Path(file_path)
            
            # Generate document ID
            document_id = self._generate_document_id(file_path)
            
            # Prepare base event data
            base_event_data = {
                'file_path': str(path.absolute()),
                'file_name': path.name,
                'document_id': document_id
            }
            
            if logging_enabled:
                logger.debug(
                    f"Elaborazione evento {event_type} per file",
                    details={
                        "event_type": event_type,
                        "file_path": file_path,
                        "document_id": document_id
                    }
                )
            
            # Emit appropriate event based on type
            if event_type in ['created', 'existing']:
                if path.exists():
                    event_data = {
                        **base_event_data,
                        'file_size': path.stat().st_size,
                        'detected_at': datetime.now().isoformat()
                    }
                    await self._emit_event('document_file_added', event_data)
                    
                    # Also emit any_change event for created files
                    if event_type == 'created':
                        any_change_data = {
                            **base_event_data,
                            'change_type': 'created',
                            'detected_at': datetime.now().isoformat(),
                            'file_size': path.stat().st_size
                        }
                        await self._emit_event('any_change', any_change_data)
                
            elif event_type == 'modified':
                if path.exists():
                    event_data = {
                        **base_event_data,
                        'file_size': path.stat().st_size,
                        'modified_at': datetime.now().isoformat()
                    }
                    await self._emit_event('document_file_modified', event_data)
                    
                    # Also emit any_change event
                    any_change_data = {
                        **base_event_data,
                        'change_type': 'modified',
                        'detected_at': datetime.now().isoformat(),
                        'file_size': path.stat().st_size
                    }
                    await self._emit_event('any_change', any_change_data)
                
            elif event_type == 'deleted':
                event_data = {
                    **base_event_data,
                    'deleted_at': datetime.now().isoformat()
                }
                await self._emit_event('document_file_deleted', event_data)
                
                # Also emit any_change event
                any_change_data = {
                    **base_event_data,
                    'change_type': 'deleted',
                    'detected_at': datetime.now().isoformat(),
                    'file_size': None  # File no longer exists
                }
                await self._emit_event('any_change', any_change_data)
        
        except Exception as e:
            if logging_enabled:
                logger.error(
                    "Errore durante l'elaborazione dell'evento file",
                    details={
                        "event_type": event_type,
                        "file_path": file_path,
                        "error": str(e)
                    }
                )
            else:
                print(f"[Document Monitor] Error processing file event: {e}", file=sys.stderr)
    
    def _generate_document_id(self, file_path: str) -> str:
        """Generate a unique document ID for the file"""
        # Use file path hash + timestamp for uniqueness
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        return f"document_{timestamp}_{path_hash}"
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event (output as JSON for PDK server to capture)"""
        try:
            event = {
                'eventType': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'sourceId': 'document-monitor-event-source'
            }
            
            # Output event as JSON (PDK server will capture this)
            print(json.dumps(event))
            sys.stdout.flush()
            
            # Update internal stats
            self.events_emitted += 1
            self.last_activity = datetime.now()
            
            # Log anche su LogService
            if logging_enabled:
                logger.info(
                    f"Evento {event_type} emesso",
                    details={
                        "event_type": event_type,
                        "file_name": data.get('file_name', ''),
                        "document_id": data.get('document_id', ''),
                        "change_type": data.get('change_type', '')
                    },
                    context={
                        "event_id": data.get('document_id', '')
                    }
                )
            
        except Exception as e:
            if logging_enabled:
                logger.error(
                    "Errore durante l'emissione dell'evento",
                    details={
                        "event_type": event_type,
                        "error": str(e)
                    }
                )
            else:
                print(f"[Document Monitor] Error emitting event: {e}", file=sys.stderr)

# Main execution
async def main():
    """Main execution function"""
    try:
        # Get configuration from command line or environment
        # In PDK context, configuration is passed via stdin or environment
        config = {
            'monitor_path': os.environ.get('MONITOR_PATH', '/tmp/document_monitor'),
            'recursive': os.environ.get('RECURSIVE', 'true').lower() == 'true',
            'file_extensions': ['.pdf', '.doc', '.docx', '.odt', '.txt', '.xls', '.xlsx', '.ods'],
            'ignore_hidden': True,
            'debounce_time': int(os.environ.get('DEBOUNCE_TIME', '2')),
            'max_file_size': int(os.environ.get('MAX_FILE_SIZE', '100'))
        }
        
        # Log startup
        if logging_enabled:
            logger.info(
                "Document Monitor avvio dell'event source",
                details={"config": config}
            )
        else:
            print("[Document Monitor] Starting event source")
        
        # Create and initialize event source
        event_source = EventSource()
        await event_source.initialize(config)
        
        # Start monitoring
        await event_source.start()
        
        if logging_enabled:
            logger.info(
                "Document Monitor event source in esecuzione",
                details={"monitor_path": config['monitor_path']}
            )
        else:
            print(f"[Document Monitor] Event source running. Monitoring: {config['monitor_path']}")
        
        # Keep running
        try:
            while event_source.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            if logging_enabled:
                logger.info("Document Monitor ricevuto segnale di interruzione")
            else:
                print("[Document Monitor] Received interrupt signal")
        finally:
            await event_source.stop()
            
    except Exception as e:
        if logging_enabled:
            logger.critical(
                "Errore fatale nel Document Monitor",
                details={"error": str(e)}
            )
            await logger.flush()  # Assicurati che i log vengano inviati prima di uscire
        else:
            print(f"[Document Monitor] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
