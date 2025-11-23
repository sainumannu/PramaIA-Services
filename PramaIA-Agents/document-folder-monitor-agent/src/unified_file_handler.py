"""
UnifiedFileHandler - Handler di eventi del filesystem unificato
Combina le funzionalità di smart_file_handler.py e file_handler.py
in un'unica implementazione configurabile.
"""
import threading
import time
import json
import inspect
import os
import hashlib
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sqlite3
import requests
from .event_buffer import EventBuffer, event_buffer
from .filter_client import agent_filter_client
from .logger import info, warning, error, debug, lifecycle, document_detected, document_modified, document_transmitted, document_processed, document_stored


class UnifiedFileHandler(FileSystemEventHandler):
    """
    Handler unificato che combina tutte le funzionalità degli handler precedenti.
    Configurabile tramite opzioni per adattarsi a diversi scenari d'uso.
    """
    def __init__(self, document_list, folder, event_buffer, options=None):
        """
        Inizializza un nuovo handler unificato.
        
        Args:
            document_list: Lista dove salvare i documenti rilevati (può essere pdf_list o document_list)
            folder: Cartella da monitorare
            event_buffer: Buffer degli eventi
            options: Dizionario con opzioni di configurazione
        """
        self.document_list = document_list
        self.folder = folder
        self.event_buffer = event_buffer
        self.filter_client = agent_filter_client
        
        # Opzioni di configurazione con valori predefiniti
        self.options = {
            "use_smart_filters": True,          # Usa filtri intelligenti
            "track_document_lifecycle": True,   # Traccia il ciclo di vita dei documenti
            "support_document_rename": True,    # Supporta rinomina documenti
            "check_file_hashes": True,          # Verifica hash dei file
            "log_detailed_events": True,        # Log dettagliati
            "prevent_duplicate_logs": True,     # Previene log duplicati
            "process_all_file_types": False     # Se False, processa solo PDF e documenti
        }
        
        # Aggiorna con le opzioni fornite
        if options:
            self.options.update(options)
            
    def _get_relative_path(self, full_path):
        """Ottiene il percorso relativo dalla root monitorata"""
        try:
            return os.path.relpath(full_path, self.folder)
        except:
            return full_path
            
    def _get_file_size(self, file_path):
        """Ottiene la dimensione del file in bytes"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
            
    def _extract_file_metadata(self, file_path):
        """Estrae metadati del file per il nuovo formato richiesto dal server"""
        try:
            stat = os.stat(file_path)
            metadata = {
                # CORE - sempre disponibili (obbligatori)
                "filename_original": os.path.basename(file_path),
                "file_size_original": stat.st_size,
                "date_created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "date_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }

            # Campi opzionali - aggiunti solo se disponibili
            # Se è un PDF, prova ad estrarre metadati embedded
            if file_path.lower().endswith('.pdf'):
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    pdf_metadata = doc.metadata
                    doc.close()
                    
                    if pdf_metadata:
                        # Aggiungi solo metadati PDF non vuoti
                        if pdf_metadata.get('author'):
                            metadata["author"] = pdf_metadata.get('author')
                        if pdf_metadata.get('title'):
                            metadata["title"] = pdf_metadata.get('title')
                        if pdf_metadata.get('subject'):
                            metadata["subject"] = pdf_metadata.get('subject')
                        if pdf_metadata.get('keywords'):
                            keywords = [k.strip() for k in pdf_metadata.get('keywords').split(',') if k.strip()]
                            if keywords:
                                metadata["keywords"] = keywords
                        if pdf_metadata.get('creator'):
                            metadata["creator"] = pdf_metadata.get('creator')
                        if pdf_metadata.get('producer'):
                            metadata["producer"] = pdf_metadata.get('producer')
                        if pdf_metadata.get('creationDate'):
                            metadata["creation_date"] = pdf_metadata.get('creationDate')
                except ImportError:
                    pass  # PyMuPDF non disponibile
                except Exception:
                    pass  # Errore nell'estrazione metadati PDF

            return metadata
            
        except Exception as e:
            # Ritorna metadati minimi obbligatori in caso di errore
            return {
                "filename_original": os.path.basename(file_path),
                "file_size_original": 0,
                "date_created": datetime.now().isoformat(),
                "date_modified": datetime.now().isoformat()
            }

    def on_created(self, event):
        """Gestisce creazione di file e cartelle con filtri intelligenti"""
        if event.is_directory:
            info(f"📁 Nuova cartella creata: {event.src_path}")
            self._handle_directory_change(event.src_path, "created")
            return

        file_path = str(event.src_path)
        file_name = os.path.basename(file_path)
        relative_path = self._get_relative_path(file_path)
        file_size = self._get_file_size(file_path)
        
        # Se la dimensione è 0, attendi e riprova fino a 5 volte (max 2.5s)
        retry_count = 0
        while file_size == 0 and retry_count < 5:
            time.sleep(0.5)
            file_size = self._get_file_size(file_path)
            retry_count += 1

        # Evita log duplicati: se esiste già un evento per questo file (pending o completed), non loggare/inviare
        if self.options["prevent_duplicate_logs"]:
            existing_event_id = self.event_buffer.find_event_by_filename(file_name)
            if existing_event_id:
                # Puoi loggare solo una volta per debug, oppure saltare del tutto
                debug(f"Evento già presente per file {file_name}, ignoro nuovo evento di creazione.")
                return

        # Log dettagliato dell'evento di creazione file
        info(
            f"📄 Nuovo file rilevato: {relative_path} ({file_size} bytes)",
            details={
                "file_name": file_name,
                "file_path": file_path,
                "relative_path": relative_path,
                "file_size": file_size,
                "event_type": "created"
            }
        )
        
        # Tracciamento del ciclo di vita del documento
        if self.options["track_document_lifecycle"]:
            document_detected(
                document_id=file_name,  # Usa il nome file come ID temporaneo fino a quando non otteniamo l'ID dal backend
                path=file_path,
                details={
                    "file_size": file_size,
                    "relative_path": relative_path,
                    "detection_type": "file_creation"
                }
            )
            
        # Calcolo hash se abilitato
        if self.options["check_file_hashes"]:
            try:
                from .file_hash_tracker import FileHashTracker
                tracker = FileHashTracker()
                stored_hash = tracker.get_stored_hash(file_path)
                
                if not stored_hash:
                    hash_value = tracker.calculate_file_hash(file_path)
                    info(
                        f"🔢 Calcolato nuovo hash per '{file_name}'",
                        details={
                            "operation": "hash_calculation",
                            "file_name": file_name,
                            "file_path": file_path,
                            "hash_value": hash_value,
                            "is_new_hash": True
                        }
                    )
                    
                    # Aggiungi l'hash al database e registra l'operazione
                    file_stat = os.stat(file_path)
                    from .file_hash_tracker import FileInfo
                    file_info = FileInfo(file_path, file_stat.st_size, file_stat.st_mtime, hash_value)
                    tracker.update_file_hash(file_info)
                    info(
                        f"✅ Aggiunto hash nel database per '{file_name}'",
                        details={
                            "operation": "hash_db_operation",
                            "action": "add",
                            "file_name": file_name,
                            "file_path": file_path,
                            "hash_value": hash_value
                        }
                    )
                else:
                    info(
                        f"🔢 Recuperato hash esistente per '{file_name}'",
                        details={
                            "operation": "hash_calculation",
                            "file_name": file_name,
                            "file_path": file_path,
                            "hash_value": stored_hash.hash_value,
                            "is_new_hash": False
                        }
                    )
                
                tracker.close()
            except Exception as e:
                error(
                    f"❌ Errore nel calcolo hash per '{file_name}': {str(e)}",
                    details={
                        "operation": "hash_calculation",
                        "file_name": file_name,
                        "file_path": file_path,
                        "error": str(e)
                    }
                )
                
        # Interroga il sistema di filtri per decidere come gestire il file
        filter_decision = self.filter_client.should_process_file(file_path, file_size)
        
        if self.options["log_detailed_events"]:
            info(
                f"🔍 Decisione filtri: {filter_decision['action']} - {filter_decision['reason']}",
                details={
                    "file_name": file_name,
                    "filter_decision": filter_decision
                }
            )
        
        # Gestisci in base alla decisione dei filtri
        if filter_decision['action'] == 'skip':
            info(
                f"⏭️ File '{file_name}' ignorato per filtri", 
                details={
                    "file_name": file_name,
                    "reason": filter_decision['reason'],
                    "filter_name": filter_decision.get('filter_name', 'unknown')
                }
            )
            return
            
        # Aggiungi alla lista di documenti se è un tipo supportato
        supported_extensions = ['.pdf', '.doc', '.docx', '.odt', '.txt', '.xls', '.xlsx', '.ods']
        if self.options["process_all_file_types"] or any(file_path.lower().endswith(ext) for ext in supported_extensions):
            self.document_list.append(file_name)
            
        # Invia al backend solo se i filtri lo consentono
        if filter_decision['should_upload']:
            self._send_file_to_backend(file_path, 'created', filter_decision)
        else:
            info(
                f"📋 File '{file_name}' non inviato al backend per filtri",
                details={
                    "file_name": file_name,
                    "reason": filter_decision.get('reason', 'Filtro attivo'),
                    "filter_name": filter_decision.get('filter_name', 'unknown')
                }
            )

    def on_deleted(self, event):
        """Gestisce cancellazione di file e cartelle"""
        if event.is_directory:
            info(f"🗑️ Cartella cancellata: {event.src_path}")
            self._handle_directory_deletion(event.src_path)
            return
            
        file_name = os.path.basename(event.src_path)
        relative_path = self._get_relative_path(event.src_path)
        
        # Log standard per l'evento di cancellazione
        info(
            f"🗑️ File cancellato: {relative_path}",
            details={
                "file_name": file_name,
                "relative_path": relative_path,
                "event_type": "deleted"
            }
        )
        
        # Tracciamento del ciclo di vita del documento cancellato
        if self.options["track_document_lifecycle"]:
            lifecycle(
                f"File cancellato: {file_name}",
                details={
                    "lifecycle_event": "FILE_DELETED",
                    "log_type": "lifecycle",
                    "file_name": file_name,
                    "file_path": event.src_path,
                    "relative_path": relative_path
                }
            )
            
            document_modified(
                document_id=str(file_name),
                path=str(event.src_path),
                modification_type="deleted",
                details={
                    "relative_path": relative_path
                }
            )
        
        # Per le cancellazioni, sempre informare il backend
        self._delete_file_from_backend(file_name)

    def on_modified(self, event):
        """Gestisce modifica di file con filtri"""
        if event.is_directory:
            return
            
        file_path = str(event.src_path)
        file_name = os.path.basename(file_path)
        relative_path = self._get_relative_path(file_path)
        file_size = self._get_file_size(file_path)
        
        info(
            f"✏️ File modificato: {relative_path}",
            details={
                "file_name": file_name,
                "file_path": file_path,
                "relative_path": relative_path,
                "file_size": file_size,
                "event_type": "modified"
            }
        )
        
        # Tracciamento del ciclo di vita del documento modificato
        if self.options["track_document_lifecycle"]:
            document_modified(
                document_id=file_name,
                path=file_path,
                modification_type="updated",
                details={
                    "file_size": file_size,
                    "relative_path": relative_path
                }
            )
        
        # Valuta con filtri
        filter_decision = self.filter_client.should_process_file(file_path, file_size)
        
        if filter_decision['should_upload']:
            # Log di processo usando solo lifecycle se è abilitato
            if self.options["track_document_lifecycle"]:
                lifecycle(
                    f"Re-invio file modificato: {file_name}",
                    details={
                        "lifecycle_event": "REUPLOAD_DECISION",
                        "log_type": "lifecycle",
                        "file_name": file_name,
                        "file_path": file_path,
                        "decision": "reupload",
                        "filter_decision": filter_decision
                    }
                )
            
            self._send_file_to_backend(file_path, 'modified', filter_decision)
        else:
            if self.options["track_document_lifecycle"]:
                lifecycle(
                    f"File modificato non re-inviato per filtri: {file_name}",
                    details={
                        "lifecycle_event": "REUPLOAD_SKIPPED",
                        "log_type": "lifecycle",
                        "file_name": file_name,
                        "file_path": file_path,
                        "decision": "skip",
                        "reason": filter_decision.get('reason', 'Filtro attivo'),
                        "filter_name": filter_decision.get('filter_name', 'unknown')
                    }
                )
            else:
                info(
                    f"📋 File modificato '{file_name}' non re-inviato per filtri",
                    details={
                        "file_name": file_name,
                        "reason": filter_decision.get('reason', 'Filtro attivo'),
                        "filter_name": filter_decision.get('filter_name', 'unknown')
                    }
                )

    def on_moved(self, event):
        """Gestisce spostamento/rinomina di file e cartelle"""
        old_name = os.path.basename(event.src_path)
        new_name = os.path.basename(event.dest_path)
        
        # Determina se è una rinomina o uno spostamento
        old_dir = os.path.dirname(event.src_path)
        new_dir = os.path.dirname(event.dest_path)
        is_rename = old_dir == new_dir
        
        event_type = "renamed" if is_rename else "moved"
        
        info(
            f"📦 {'Rinomina' if is_rename else 'Spostamento'}: {old_name} → {new_name}",
            details={
                "old_name": old_name,
                "new_name": new_name,
                "old_path": event.src_path,
                "new_path": event.dest_path,
                "event_type": event_type,
                "is_rename": is_rename
            }
        )
        
        # Tracciamento del ciclo di vita del documento rinominato o spostato
        if self.options["track_document_lifecycle"]:
            document_modified(
                document_id=str(new_name),  # Convertiamo in stringa per sicurezza
                path=str(event.dest_path),
                modification_type=event_type,  # "renamed" o "moved"
                details={
                    "old_name": old_name,
                    "old_path": str(event.src_path),
                    "is_rename": is_rename
                }
            )
        
        if event.is_directory:
            self._handle_directory_move(event.src_path, event.dest_path)
        else:
            if is_rename and self.options["support_document_rename"]:
                # Se è una rinomina, crea un evento specifico di rinomina invece di delete+create
                self._handle_file_rename(old_name, new_name, event.dest_path)
            else:
                # Per i file spostati: cancella vecchio e aggiungi nuovo
                self._delete_file_from_backend(old_name)
                
                # Valuta nuovo file con filtri
                dest_path = str(event.dest_path)
                file_size = self._get_file_size(dest_path)
                filter_decision = self.filter_client.should_process_file(dest_path, file_size)
                
                if filter_decision['should_upload']:
                    self._send_file_to_backend(dest_path, 'moved', filter_decision)
                    
    def _handle_file_rename(self, old_name, new_name, new_path):
        """Gestisce la rinomina di un file creando un evento di tipo 'renamed'"""
        try:
            # Crea metadati dettagliati per l'evento di rinomina
            metadata = {
                'old_name': old_name,
                'new_name': new_name,
                'details': f"Rinominato da '{old_name}' a '{new_name}'"
            }
            
            # Aggiungi evento di tipo 'renamed'
            folder = os.path.dirname(new_path)
            event_id = self.event_buffer.add_event('renamed', new_name, folder, metadata)
            
            info(
                f"📝 Rinomina registrata: {old_name} → {new_name}",
                details={
                    "old_name": old_name,
                    "new_name": new_name,
                    "event_id": event_id,
                    "event_type": "renamed"
                }
            )
            
            # Notifica al backend della rinomina
            self._notify_backend_rename(old_name, new_name, new_path, event_id)
            
        except Exception as e:
            error(
                f"❌ Errore durante registrazione rinomina {old_name} → {new_name}: {e}",
                details={"old_name": old_name, "new_name": new_name, "error": str(e)}
            )
            
    def _notify_backend_rename(self, old_name, new_name, new_path, event_id):
        """Notifica al backend che un file è stato rinominato"""
        try:
            import os
            
            # Risolvi l'URL del backend seguendo questa priorità:
            # 1) BACKEND_URL
            # 2) PRAMAIALOG_HOST (+ PRAMAIALOG_PORT se presente)
            # 3) BACKEND_BASE_URL
            # 4) BACKEND_HOST + BACKEND_PORT (fallback)
            BACKEND_BASE_URL = os.getenv("BACKEND_URL")
            if not BACKEND_BASE_URL:
                pra_host = os.getenv("PRAMAIALOG_HOST")
                pra_port = os.getenv("PRAMAIALOG_PORT")
                if pra_host:
                    # Aggiungi protocollo se mancante
                    if not pra_host.startswith(("http://", "https://")):
                        pra_host = f"http://{pra_host}"
                    # Aggiungi porta se fornita e non già presente
                    if pra_port and not pra_host.rstrip('/').split(':')[-1].isdigit():
                        pra_host = f"{pra_host.rstrip('/') }:{pra_port}"
                    BACKEND_BASE_URL = pra_host
                else:
                    BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
                    BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
                    BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL") or f"http://{BACKEND_HOST}:{BACKEND_PORT}"
            
            # Costruisci il percorso per l'API di rinomina
            RENAME_URL = f"{BACKEND_BASE_URL}/api/document-monitor/rename"
            
            # Crea il payload con tutte le informazioni necessarie
            data = {
                "old_name": old_name,
                "new_name": new_name,
                "file_path": new_path,
                "event_id": event_id
            }
            
            # Invia la richiesta al backend
            resp = requests.post(RENAME_URL, json=data, timeout=10)

            if resp.status_code in [200, 201, 204]:
                info(
                    f"✅ Rinomina registrata con successo: {old_name} → {new_name}",
                    details={
                        "old_name": old_name,
                        "new_name": new_name,
                        "status_code": resp.status_code,
                        "event_id": event_id
                    }
                )
                # Aggiorna lo stato dell'evento a 'completed'
                self.event_buffer.update_event_status(event_id, 'completed')
                
                # Pulizia immediata degli eventi duplicati dopo ogni rinomina riuscita
                # per evitare che l'utente veda due righe per lo stesso evento
                if self.options["prevent_duplicate_logs"]:
                    try:
                        duplicates_cleaned = self.event_buffer.clean_duplicate_events()
                        if duplicates_cleaned > 0:
                            info(f"🧹 Pulizia automatica: rimossi {duplicates_cleaned} eventi duplicati dopo rinomina")
                    except Exception as clean_error:
                        warning(f"⚠️ Errore durante la pulizia automatica dopo rinomina: {clean_error}")
            else:
                warning(
                    f"⚠️ Errore nella registrazione della rinomina {old_name} → {new_name}: {resp.status_code}",
                    details={
                        "old_name": old_name,
                        "new_name": new_name,
                        "status_code": resp.status_code,
                        "response_text": resp.text,
                        "event_id": event_id
                    }
                )
                # Aggiorna lo stato dell'evento a 'failed'
                self.event_buffer.update_event_status(event_id, 'failed', error_message=f"Errore: {resp.status_code} {resp.text}")
        except Exception as e:
            error(
                f"❌ Errore durante notifica rinomina {old_name} → {new_name}: {e}",
                details={"old_name": old_name, "new_name": new_name, "error": str(e)}
            )
            # Aggiorna lo stato dell'evento a 'failed'
            self.event_buffer.update_event_status(event_id, 'failed', error_message=f"Errore: {str(e)}")

    def _send_file_to_backend(self, file_path, action, filter_decision):
        """Invia file al backend con informazioni sui filtri"""
        try:
            file_name = os.path.basename(file_path)
            
            # Log inizio del ciclo di vita di questo documento
            if self.options["track_document_lifecycle"]:
                lifecycle(
                    f"Inizio elaborazione documento '{file_name}'",
                    details={
                        "lifecycle_event": "START_PROCESSING",
                        "log_type": "lifecycle",
                        "file_name": file_name,
                        "file_path": file_path,
                        "status": "iniziato",
                        "action": action,
                        "filter_action": filter_decision['action']
                    }
                )
            
            # Cerca l'evento esistente o crea un nuovo evento
            event_id = self.event_buffer.find_event_by_filename(file_name)
            
            # Se non esiste un evento, ne creiamo uno adesso
            if not event_id:
                event_data = {
                    'full_path': file_path,
                    'relative_path': self._get_relative_path(file_path),
                    'filter_action': filter_decision['action'],
                    'extract_metadata': filter_decision['extract_metadata']
                }
                event_id = self.event_buffer.add_event(action, file_name, self.folder, event_data)
                
                if self.options["track_document_lifecycle"]:
                    lifecycle(
                        f"Creato evento per '{file_name}'",
                        details={
                            "lifecycle_event": "EVENT_CREATED",
                            "file_name": file_name,
                            "file_path": file_path,
                            "status": "creato",
                            "event_id": event_id,
                            "event_data": str(event_data)
                        }
                    )
            
            # Aggiorna lo stato dell'evento a 'processing'
            self.event_buffer.update_event_status(event_id, 'processing')
            
            if self.options["track_document_lifecycle"]:
                lifecycle(
                    f"Evento aggiornato a 'processing' per '{file_name}'",
                    details={
                        "lifecycle_event": "EVENT_STATUS",
                        "file_name": file_name,
                        "file_path": file_path,
                        "status": "processing",
                        "event_id": event_id
                    }
                )
            
            # Risolvi BACKEND URL preferendo BACKEND_URL -> PRAMAIALOG_HOST(+PORT) -> BACKEND_BASE_URL -> fallback
            backend_base = os.getenv("BACKEND_URL")
            if not backend_base:
                backend_base = os.getenv("BACKEND_BASE_URL")
                if not backend_base:
                    backend_host = os.getenv("BACKEND_HOST", "localhost")
                    backend_port = os.getenv("BACKEND_PORT", "8000")
                    backend_base = f"http://{backend_host}:{backend_port}"

            UPLOAD_URL = f"{backend_base.rstrip('/')}/api/document-monitor/upload/"
            
            # Log delle informazioni sull'hash prima dell'invio
            if self.options["check_file_hashes"]:
                try:
                    from .file_hash_tracker import FileHashTracker
                    tracker = FileHashTracker()
                    stored_hash = tracker.get_stored_hash(file_path)
                    
                    if stored_hash:
                        lifecycle(
                            f"Hash trovato nel database per '{file_name}'",
                            details={
                                "lifecycle_event": "HASH_CHECK",
                                "file_name": file_name,
                                "file_path": file_path,
                                "status": "trovato",
                                "hash_value": stored_hash.hash_value
                            }
                        )
                    else:
                        lifecycle(
                            f"Hash non trovato nel database per '{file_name}'",
                            details={
                                "lifecycle_event": "HASH_CHECK",
                                "file_name": file_name,
                                "file_path": file_path,
                                "status": "non trovato"
                            }
                        )
                    
                    tracker.close()
                except Exception as e:
                    error(
                        f"❌ Errore verifica hash prima dell'upload per '{file_name}': {str(e)}",
                        details={
                            "operation": "hash_check_before_upload",
                            "file_name": file_name,
                            "file_path": file_path,
                            "error": str(e)
                        }
                    )
            
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f)}
                
                # Estrai metadati originali del file
                file_metadata = _extract_file_metadata(file_path)
                
                # Aggiungi informazioni sui filtri ai custom_fields
                file_metadata["custom_fields"].update({
                    "filter_action": filter_decision['action'],
                    "filter_name": filter_decision.get('filter_name', 'unknown'),
                    "extract_metadata_fields": filter_decision['extract_metadata'],
                    "should_process_content": filter_decision['should_process_content'],
                    "agent_action": action
                })
                
                # Costruisci payload nel formato UploadFileMetadata richiesto dal server
                client_id = os.getenv("PLUGIN_CLIENT_ID", "document-monitor-001")
                upload_metadata = {
                    "client_id": client_id,
                    "original_path": file_path,
                    "source": "agent",
                    "metadata": file_metadata
                }
                
                # Converti in JSON per form-data
                data = {
                    "metadata": json.dumps(upload_metadata)
                }
                
                # Log della richiesta prima dell'invio
                if self.options["log_detailed_events"]:
                    info(
                        f"📤 Invio richiesta al backend per '{file_name}' con metadati",
                        details={
                            "operation": "backend_request",
                            "request_type": "upload_with_metadata",
                            "file_name": file_name,
                            "file_path": file_path,
                            "client_id": client_id,
                            "has_metadata": len(file_metadata) > 0,
                            "metadata_fields": list(file_metadata.keys()),
                            "filter_action": filter_decision['action']
                        }
                    )
                
                # Invia la richiesta al backend
                resp = requests.post(UPLOAD_URL, files=files, data=data, timeout=30)
            
            # Prepara per analizzare la risposta
            try:
                response_data = resp.json() if resp.text else {}
            except:
                response_data = {"text": resp.text}
                
            # Log della risposta dal backend
            success = (resp.status_code == 200)
            log_level = info if success else error
            
            if self.options["log_detailed_events"]:
                log_level(
                    f"{'✅' if success else '❌'} Risposta dal backend ({resp.status_code}) per '{file_name}'",
                    details={
                        "operation": "backend_response",
                        "request_type": "upload",
                        "file_name": file_name,
                        "file_path": file_path,
                        "status_code": resp.status_code,
                        "response_data": str(response_data),
                        "success": success
                    }
                )
                
            if resp.status_code == 200:
                info(
                    f"✅ File '{file_name}' inviato al backend con metadati ({action})",
                    details={
                        "file_name": file_name,
                        "action": action,
                        "filter_name": filter_decision.get('filter_name', 'unknown'),
                        "status_code": resp.status_code,
                        "has_original_metadata": bool(file_metadata.get('author') or file_metadata.get('title')),
                        "file_size_original": file_metadata.get('file_size_original', 0)
                    }
                )
                
                # Tracciamento del ciclo di vita: documento trasmesso al backend
                if self.options["track_document_lifecycle"]:
                    document_transmitted(
                        document_id=file_name,
                        target_system="backend",
                        status="success",
                        details={
                            "action": action,
                            "response_code": resp.status_code,
                            "file_path": file_path,
                            "metadata_included": True,
                            "original_file_size": file_metadata.get('file_size_original', 0),
                            "client_id": client_id
                        }
                    )
                
                # Aggiorna lo stato dell'evento a 'completed'
                self.event_buffer.update_event_status(event_id, 'completed')
                
                if self.options["track_document_lifecycle"]:
                    lifecycle(
                        f"Evento completato per '{file_name}'",
                        details={
                            "lifecycle_event": "EVENT_STATUS",
                            "file_name": file_name,
                            "file_path": file_path,
                            "status": "completed",
                            "event_id": event_id
                        }
                    )
                    
                # Estrai document_id dalla risposta
                try:
                    result = resp.json()
                    document_id = None
                    status = result.get('status', 'success')
                    
                    # Log completo della risposta per debug
                    if self.options["log_detailed_events"]:
                        info(f"Risposta completa dal backend:", details={"response": result})
                    
                    # Verifica se la risposta indica che il file è un duplicato
                    is_duplicate = False
                    
                    # Controlla il campo status
                    if 'status' in result and result['status'] == 'duplicate':
                        is_duplicate = True
                        info(f"File '{file_name}' identificato come duplicato dal campo 'status'", 
                            details={"file_name": file_name, "response_status": result['status']})
                    
                    # Controlla anche il campo is_duplicate per compatibilità
                    elif 'is_duplicate' in result and result['is_duplicate'] is True:
                        is_duplicate = True
                        info(f"File '{file_name}' identificato come duplicato dal campo 'is_duplicate'", 
                            details={"file_name": file_name, "is_duplicate": result['is_duplicate']})
                    
                    # Se il file è un duplicato e abilitiamo il lifecycle
                    if is_duplicate and self.options["track_document_lifecycle"]:
                        lifecycle(
                            f"Rilevato file duplicato: '{file_name}'",
                            details={
                                "lifecycle_event": "DUPLICATE_CHECK",
                                "file_name": file_name,
                                "file_path": file_path,
                                "status": "duplicato",
                                "response": str(result)
                            }
                        )
                        
                        # Recupera l'ID del documento originale se disponibile
                        if 'document_id' in result:
                            document_id = result['document_id']
                            info(f"Documento duplicato: usando document_id del file originale: {document_id}", 
                                details={"file_name": file_name, "document_id": document_id})
                            
                            # Aggiorna lo stato e il document_id dell'evento
                            success = self.event_buffer.update_event_status(event_id, 'duplicate', document_id=document_id)
                            info(f"Aggiornamento stato: evento {event_id} impostato a 'duplicate' con document_id. Successo: {success}", 
                                details={"event_id": event_id, "status": "duplicate", "document_id": document_id})
                        else:
                            # Se non abbiamo document_id, aggiorna solo lo stato
                            success = self.event_buffer.update_event_status(event_id, 'duplicate')
                            info(f"Aggiornamento stato: evento {event_id} impostato a 'duplicate' senza document_id. Successo: {success}", 
                                details={"event_id": event_id, "status": "duplicate"})
                            
                        # Termina qui l'elaborazione per i duplicati
                        return
                    
                    # Cerca il document_id in tutte le posizioni possibili
                    if 'document_id' in result:
                        document_id = result['document_id']
                    elif 'result' in result and isinstance(result['result'], dict) and 'document_id' in result['result']:
                        document_id = result['result']['document_id']
                    elif 'workflow_result' in result and isinstance(result['workflow_result'], dict):
                        if 'document_id' in result['workflow_result']:
                            document_id = result['workflow_result']['document_id']
                        elif 'result' in result['workflow_result'] and isinstance(result['workflow_result']['result'], dict):
                            if 'document_id' in result['workflow_result']['result']:
                                document_id = result['workflow_result']['result']['document_id']
                            elif 'id' in result['workflow_result']['result']:
                                document_id = result['workflow_result']['result']['id']
                    
                    info(f"Document ID estratto: {document_id}", details={"file_name": file_name, "document_id": document_id})
                    
                    if self.options["track_document_lifecycle"]:
                        lifecycle(
                            f"{'Estratto' if document_id else 'Non trovato'} Document ID per '{file_name}'",
                            details={
                                "lifecycle_event": "DOCUMENT_ID",
                                "file_name": file_name,
                                "file_path": file_path,
                                "status": "estratto" if document_id else "non trovato",
                                "document_id": document_id
                            }
                        )
                    
                    if document_id:
                        self.event_buffer.update_event_document_id(event_id, document_id)
                        info(f"Document ID salvato nell'evento {event_id}: {document_id}")
                        
                        # Tracciamento del ciclo di vita: documento archiviato nel sistema
                        if self.options["track_document_lifecycle"]:
                            document_stored(
                                document_id=document_id,
                                storage_system="vectorstore",
                                status="success",
                                details={
                                    "file_name": file_name,
                                    "event_id": event_id,
                                    "original_file_path": file_path
                                }
                            )
                            
                            # Tracciamento del ciclo di vita: documento processato
                            document_processed(
                                document_id=document_id,
                                processor_id="backend_workflow",
                                status="completed",
                                details={
                                    "file_name": file_name,
                                    "event_id": event_id,
                                    "workflow_result": "success"
                                }
                            )
                    else:
                        warning(f"⚠️ Nessun document_id trovato nella risposta per '{file_name}'", 
                                details={"file_name": file_name})
                except Exception as e:
                    warning(
                        f"⚠️ Errore durante l'estrazione del document_id per '{file_name}'",
                        details={"file_name": file_name, "error": str(e)}
                    )
                    error(
                        f"❌ Errore estrazione document_id per '{file_name}': {str(e)}",
                        details={
                            "operation": "document_id_extraction",
                            "file_name": file_name,
                            "file_path": file_path,
                            "error": str(e),
                            "response": str(response_data)
                        }
                    )
                    
            else:
                error(
                    f"❌ Errore invio file '{file_name}': {resp.status_code}",
                    details={
                        "file_name": file_name,
                        "action": action,
                        "status_code": resp.status_code,
                        "response_text": resp.text
                    }
                )
                # Aggiorna lo stato dell'evento a 'failed'
                self.event_buffer.update_event_status(event_id, 'failed')
                
                if self.options["track_document_lifecycle"]:
                    lifecycle(
                        f"Evento fallito per '{file_name}'",
                        details={
                            "lifecycle_event": "EVENT_STATUS",
                            "file_name": file_name,
                            "file_path": file_path,
                            "status": "failed",
                            "event_id": event_id,
                            "status_code": resp.status_code,
                            "response": resp.text,
                            "error": True
                        }
                    )
                    
        except Exception as e:
            error(
                f"❌ Errore durante invio file {file_path}: {e}",
                details={"file_path": file_path, "error": str(e)}
            )
            event_id = self.event_buffer.find_event_by_filename(os.path.basename(file_path))
            if event_id:
                self.event_buffer.update_event_status(event_id, 'failed')

    def _delete_file_from_backend(self, filename):
        """Rimuove file dal backend/vectorstore e registra l'evento di cancellazione"""
        try:
            # Prima creiamo un evento di cancellazione nel buffer
            event_id = self.event_buffer.add_event('deleted', filename, self.folder, {
                'full_path': os.path.join(self.folder, filename),
                'relative_path': filename
            })
            
            # Aggiorna lo stato dell'evento a 'processing'
            self.event_buffer.update_event_status(event_id, 'processing')
            
            # Log con la funzione lifecycle solo se è abilitata
            if self.options["track_document_lifecycle"]:
                lifecycle(
                    f"Inizio processo di cancellazione per '{filename}'",
                    details={
                        "lifecycle_event": "DELETE_PROCESSING",
                        "file_name": filename,
                        "status": "iniziato"
                    }
                )
            
            # Risolvi l'URL del backend con logica CORRETTA:
            # 1) BACKEND_URL (se specificato)
            # 2) BACKEND_HOST + BACKEND_PORT (il vero backend)
            # 3) Fallback a localhost:8000
            backend_base = os.getenv("BACKEND_URL")
            if not backend_base:
                backend_host = os.getenv("BACKEND_HOST", "localhost")
                backend_port = os.getenv("BACKEND_PORT", "8000")
                backend_base = f"http://{backend_host}:{backend_port}"

            # Utilizziamo l'endpoint corretto per la cancellazione dei file PDF monitorati
            DELETE_URL = f"{backend_base.rstrip('/')}/api/document-monitor/delete/"
            
            # Inviamo le informazioni complete del file cancellato
            data = {
                "file_name": filename,
                "folder": self.folder,
                "action": "deleted",
                "event_id": str(event_id)  # Convertito in stringa per prevenire errori 422
            }
            
            resp = requests.post(DELETE_URL, json=data, timeout=10)
            
            if resp.status_code in [200, 204]:
                info(
                    f"✅ File '{filename}' registrato come cancellato",
                    details={
                        "file_name": filename,
                        "folder": self.folder,
                        "status_code": resp.status_code,
                        "action": "delete",
                        "event_id": event_id
                    }
                )
                # Aggiorna lo stato dell'evento a 'completed'
                self.event_buffer.update_event_status(event_id, 'completed')
                
                # Rimuovi anche l'hash dal database locale se il sistema di hash è abilitato
                if self.options["check_file_hashes"]:
                    try:
                        from .hash_db_cleaner import hash_db_cleaner
                        # Costruisci il percorso completo
                        full_path = os.path.join(self.folder, filename)
                        hash_db_cleaner.remove_file_hash(full_path)
                        
                        # Log con la funzione lifecycle se è abilitata
                        if self.options["track_document_lifecycle"]:
                            lifecycle(
                                f"Hash di '{filename}' rimosso dal database locale", 
                                details={
                                    "lifecycle_event": "HASH_REMOVED",
                                    "file_name": filename,
                                    "file_path": full_path,
                                    "success": True
                                }
                            )
                    except Exception as hash_error:
                        warning(f"⚠️ Impossibile rimuovere hash di '{filename}' dal database locale: {hash_error}")
                
                # Tenta anche di rimuovere il file dal vectorstore (per compatibilità)
                try:
                    DELETE_DOCUMENT_URL = f"{backend_base.rstrip('/')}/api/documents/{filename}"
                    doc_resp = requests.delete(DELETE_DOCUMENT_URL, timeout=5)
                    if doc_resp.status_code in [200, 204, 404]:
                        info(f"File '{filename}' rimosso anche dal vectorstore", details={"status_code": doc_resp.status_code})
                except Exception as vec_err:
                    warning(f"Errore nella rimozione dal vectorstore: {vec_err}", details={"error": str(vec_err)})
            else:
                warning(
                    f"⚠️ Errore registrazione cancellazione file '{filename}': {resp.status_code}",
                    details={
                        "file_name": filename,
                        "status_code": resp.status_code,
                        "response_text": resp.text,
                        "action": "delete",
                        "event_id": event_id
                    }
                )
                # Aggiorna lo stato dell'evento a 'failed'
                self.event_buffer.update_event_status(event_id, 'failed')
                
        except Exception as e:
            error(
                f"❌ Errore durante rimozione file {filename}: {e}",
                details={"file_name": filename, "error": str(e)}
            )
            # Tenta di aggiornare lo stato dell'evento a 'failed' se è stato creato
            try:
                event_id = self.event_buffer.find_event_by_filename(filename)
                if event_id:
                    self.event_buffer.update_event_status(event_id, 'failed')
            except:
                pass

    def _handle_directory_change(self, folder_path, action):
        """Gestisce cambamenti alle directory"""
        try:
            # Per ora, log semplice
            info(
                f"📁 Directory {action}: {folder_path}",
                details={"folder_path": folder_path, "action": action}
            )
            # TODO: Implementare invio metadati directory se necessario
            
        except Exception as e:
            error(
                f"❌ Errore gestione directory {folder_path}: {e}",
                details={"folder_path": folder_path, "error": str(e)}
            )

    def _handle_directory_deletion(self, folder_path):
        """Gestisce cancellazione directory"""
        try:
            info(
                f"🗑️ Cancellazione directory: {folder_path}",
                details={"folder_path": folder_path, "action": "delete"}
            )
            # TODO: Implementare rimozione contenuti dal vectorstore
            
        except Exception as e:
            error(
                f"❌ Errore cancellazione directory {folder_path}: {e}",
                details={"folder_path": folder_path, "error": str(e)}
            )

    def _handle_directory_move(self, old_path, new_path):
        """Gestisce spostamento directory"""
        try:
            info(
                f"📦 Spostamento directory: {old_path} → {new_path}",
                details={"old_path": old_path, "new_path": new_path, "action": "move"}
            )
            # TODO: Implementare aggiornamento path nel vectorstore
            
        except Exception as e:
            error(
                f"❌ Errore spostamento directory: {e}",
                details={"old_path": old_path, "new_path": new_path, "error": str(e)}
            )

# Mantieni compatibilità con i nomi di classe esistenti
PDFHandler = UnifiedFileHandler
DocsHandler = UnifiedFileHandler
EnhancedFileHandler = UnifiedFileHandler
SmartFileHandler = UnifiedFileHandler
