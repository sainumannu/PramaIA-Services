"""
Enhanced File Handler con sistema di filtri intelligenti
"""
import threading
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from pathlib import Path
from .event_buffer import EventBuffer
from .filter_client import agent_filter_client
from .logger import info, warning, error, debug, lifecycle

class SmartFileHandler(FileSystemEventHandler):
    """
    Handler con filtri intelligenti per evitare trasferimenti inutili
    """
    def __init__(self, pdf_list, folder, event_buffer):
        self.pdf_list = pdf_list
        self.folder = folder
        self.event_buffer = event_buffer
        self.filter_client = agent_filter_client
        
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

    def on_created(self, event):
        """Gestisce creazione di file e cartelle con filtri intelligenti, evitando log duplicati."""
        if event.is_directory:
            info(f"📁 Nuova cartella creata: {event.src_path}")
            self._handle_directory_change(event.src_path, "created")
            return

        file_path = str(event.src_path)
        file_name = os.path.basename(file_path)
        relative_path = self._get_relative_path(file_path)
        file_size = self._get_file_size(file_path)

        # Evita log duplicati: se esiste già un evento per questo file (pending o completed), non loggare/inviare
        existing_event_id = self.event_buffer.find_event_by_filename(file_name)
        if existing_event_id:
            # Puoi loggare solo una volta per debug, oppure saltare del tutto
            debug(f"Evento già presente per file {file_name}, ignoro nuovo evento di creazione.")
            return
            
        # Log dettagliato dell'evento di creazione file
        info(
            f"🔎 Rilevato evento CREATE per '{file_name}'",
            details={
                "event_type": "create",
                "file_name": file_name,
                "file_path": file_path,
                "folder": self.folder,
                "file_size": file_size
            }
        )
        
        # Verifica hash del file e registra nel log
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
                info(
                    f"✅ Verificato hash nel database per '{file_name}'",
                    details={
                        "operation": "hash_db_operation",
                        "action": "check",
                        "file_name": file_name,
                        "file_path": file_path,
                        "hash_value": stored_hash.hash_value
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

        # Interroga il sistema di filtri per decidere come gestire il file
        filter_decision = self.filter_client.should_process_file(file_path, file_size)

        # Logging avanzato della decisione di filtro
        info(
            f"🔎 Decisione filtro per '{os.path.basename(file_path)}'", 
            details={
                "operation": "filter_decision",
                "file_path": file_path,
                "filter_name": filter_decision.get('filter_name', 'unknown'),
                "decision": filter_decision
            }
        )

        info(
            f"🔍 Decisione filtri: {filter_decision['action']} - {filter_decision['reason']}",
            details={
                "file_name": file_name,
                "filter_decision": filter_decision
            }
        )

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

        if file_path.lower().endswith('.pdf'):
            self.pdf_list.append(file_name)

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
            f"🔎 Rilevato evento DELETE per '{file_name}'",
            details={
                "event_type": "delete",
                "file_name": file_name,
                "file_path": event.src_path,
                "folder": self.folder
            }
        )
        
        # Log con la funzione lifecycle (utilizziamo solo questo per evitare duplicazioni)
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
        
        info(
            f"🗑️ File cancellato: {relative_path}",
            details={
                "file_name": file_name,
                "relative_path": relative_path,
                "event_type": "deleted"
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
        
        # IMPORTANTE: Non chiamare lifecycle qui, perché verrà già chiamata da document_modified nel file_handler.py
        
        # Valuta con filtri
        filter_decision = self.filter_client.should_process_file(file_path, file_size)
        
        if filter_decision['should_upload']:
            # Log di processo usando solo lifecycle
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

    def on_moved(self, event):
        """Gestisce spostamento/rinomina di file e cartelle"""
        old_name = os.path.basename(event.src_path)
        new_name = os.path.basename(event.dest_path)
        
        info(
            f"📦 Spostamento: {old_name} → {new_name}",
            details={
                "old_name": old_name,
                "new_name": new_name,
                "old_path": event.src_path,
                "new_path": event.dest_path,
                "event_type": "moved"
            }
        )
        
        if event.is_directory:
            self._handle_directory_move(event.src_path, event.dest_path)
        else:
            # Per i file spostati: cancella vecchio e aggiungi nuovo
            self._delete_file_from_backend(old_name)
            
            # Valuta nuovo file con filtri
            dest_path = str(event.dest_path)
            file_size = self._get_file_size(dest_path)
            filter_decision = self.filter_client.should_process_file(dest_path, file_size)
            
            if filter_decision['should_upload']:
                self._send_file_to_backend(dest_path, 'moved', filter_decision)

    def _send_file_to_backend(self, file_path, action, filter_decision):
        """Invia file al backend con informazioni sui filtri"""
        try:
            file_name = os.path.basename(file_path)
            
            # Log inizio del ciclo di vita di questo documento
            # Utilizziamo solo la funzione lifecycle per evitare duplicazioni
            lifecycle(
                f"Inizio elaborazione documento '{file_name}'",
                details={
                    "lifecycle_event": "START_PROCESSING",
                    "log_type": "lifecycle",  # Assicuriamo che questo sia impostato correttamente
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
            
            import requests
            # Risolvi BACKEND URL con priorità: BACKEND_URL -> BACKEND_BASE_URL -> BACKEND_HOST+PORT -> fallback
            backend_base = os.getenv("BACKEND_URL")
            if not backend_base:
                backend_base = os.getenv("BACKEND_BASE_URL")
                if not backend_base:
                    backend_port = os.getenv("BACKEND_PORT", "8000")
                    backend_base = os.getenv("BACKEND_BASE_URL", f"http://localhost:{backend_port}")

            UPLOAD_URL = f"{backend_base.rstrip('/')}/api/document-monitor/upload/"
            
            # Log delle informazioni sull'hash prima dell'invio
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
                
                # Includi informazioni sui filtri nei metadati
                data = {
                    "action": action,
                    "full_path": file_path,
                    "relative_path": self._get_relative_path(file_path),
                    "filter_action": filter_decision['action'],
                    "extract_metadata": json.dumps(filter_decision['extract_metadata']),
                    "filter_name": filter_decision.get('filter_name', 'unknown'),
                    "should_process_content": filter_decision['should_process_content']
                }
                
                # Log della richiesta prima dell'invio
                info(
                    f"📤 Invio richiesta al backend per '{file_name}'",
                    details={
                        "operation": "backend_request",
                        "request_type": "upload",
                        "file_name": file_name,
                        "file_path": file_path,
                        "payload": str(data)
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
                    f"✅ File '{file_name}' inviato al backend ({action})",
                    details={
                        "file_name": file_name,
                        "action": action,
                        "filter_name": filter_decision.get('filter_name', 'unknown'),
                        "status_code": resp.status_code
                    }
                )
                
                # Aggiorna lo stato dell'evento a 'completed'
                self.event_buffer.update_event_status(event_id, 'completed')
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
                    info(f"Risposta completa dal backend:", details={"response": result})
                    
                    # Se il file è un duplicato, registra questa informazione nei log avanzati
                    if status == 'duplicate':
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
        """Rimuove file dal backend/vectorstore e dal database locale degli hash"""
        try:
            # Log con la funzione lifecycle (utilizziamo solo questo per evitare duplicazioni)
            lifecycle(
                f"Inizio processo di cancellazione per '{filename}'",
                details={
                    "lifecycle_event": "DELETE_PROCESSING",
                    "file_name": filename,
                    "status": "iniziato"
                }
            )
            
            import requests
            backend_base = os.getenv("BACKEND_URL")
            if not backend_base:
                pra_host = os.getenv("PRAMAIALOG_HOST")
                pra_port = os.getenv("PRAMAIALOG_PORT")
                if pra_host:
                    if not pra_host.startswith(("http://", "https://")):
                        pra_host = f"http://{pra_host}"
                    if pra_port and not pra_host.rstrip('/').split(':')[-1].isdigit():
                        pra_host = f"{pra_host.rstrip('/') }:{pra_port}"
                    backend_base = pra_host
                else:
                    backend_port = os.getenv("BACKEND_PORT", "8000")
                    backend_base = os.getenv("BACKEND_BASE_URL", f"http://localhost:{backend_port}")

            DELETE_URL = f"{backend_base.rstrip('/')}/api/documents/{filename}"
            
            resp = requests.delete(DELETE_URL, timeout=10)
            
            if resp.status_code in [200, 204, 404]:
                info(
                    f"✅ File '{filename}' rimosso dal vectorstore",
                    details={
                        "file_name": filename,
                        "status_code": resp.status_code,
                        "action": "delete"
                    }
                )
                
                # Rimuovi anche l'hash dal database locale
                try:
                    from .hash_db_cleaner import hash_db_cleaner
                    # Costruisci il percorso completo
                    full_path = os.path.join(self.folder, filename)
                    hash_db_cleaner.remove_file_hash(full_path)
                    
                    # Log con la funzione lifecycle (utilizziamo solo questo per evitare duplicazioni)
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
                
            else:
                warning(
                    f"⚠️ Errore rimozione file '{filename}': {resp.status_code}",
                    details={
                        "file_name": filename,
                        "status_code": resp.status_code,
                        "response_text": resp.text,
                        "action": "delete"
                    }
                )
                
        except Exception as e:
            error(
                f"❌ Errore durante rimozione file {filename}: {e}",
                details={"file_name": filename, "error": str(e)}
            )

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

# Mantieni compatibilità
PDFHandler = SmartFileHandler
EnhancedFileHandler = SmartFileHandler
