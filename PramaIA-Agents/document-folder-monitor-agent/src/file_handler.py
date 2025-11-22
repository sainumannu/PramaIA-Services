"""
Enhanced File Handler con sistema di filtri intelligenti
"""
import threading
import time
import json
import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from pathlib import Path
from .event_buffer import EventBuffer, event_buffer
from .filter_client import agent_filter_client
from .logger import info, warning, error, debug, document_detected, document_modified, document_transmitted, document_processed, document_stored

class SmartFileHandler(FileSystemEventHandler):
    """
    Handler con filtri intelligenti per evitare trasferimenti inutili
    """
    def __init__(self, document_list, folder, event_buffer):
        self.document_list = document_list
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
        """Gestisce creazione di file e cartelle con filtri intelligenti"""
        if event.is_directory:
            info(f"📁 Nuova cartella creata: {event.src_path}")
            # Le cartelle vengono sempre processate per metadati
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
        document_detected(
            document_id=file_name,  # Usa il nome file come ID temporaneo fino a quando non otteniamo l'ID dal backend
            path=file_path,
            details={
                "file_size": file_size,
                "relative_path": relative_path,
                "detection_type": "file_creation"
            }
        )
        
        # Interroga il sistema di filtri per decidere come gestire il file
        filter_decision = self.filter_client.should_process_file(file_path, file_size)
        
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
            if any(file_path.lower().endswith(ext) for ext in supported_extensions):
                self.document_list.append(file_name)        # Invia al backend solo se i filtri lo consentono
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
        
        info(
            f"🗑️ File cancellato: {relative_path}",
            details={
                "file_name": file_name,
                "relative_path": relative_path,
                "event_type": "deleted"
            }
        )
        
        # Tracciamento del ciclo di vita del documento cancellato
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
        
        # Verifichiamo se la classe del gestore è la principale
        # Se siamo in SmartFileHandler.py, usiamo il nostro metodo
        # Se siamo in file_handler.py ma è stato istanziato come SmartFileHandler, non dobbiamo generare log duplicati
        import inspect
        caller_frame = inspect.currentframe()
        caller_filename = inspect.getouterframes(caller_frame)[1].filename
        
        # Se il file chiamante è smart_file_handler.py o questo è un'istanza di SmartFileHandler ma non è la classe principale,
        # allora evitiamo di registrare il log per evitare duplicazioni
        if 'smart_file_handler.py' in caller_filename or (
            not self.__class__.__module__.endswith('file_handler') and 
            not self.__class__.__name__ == 'SmartFileHandler'
        ):
            # Debug per capire quali eventi stiamo filtrando
            debug(f"Evitato log duplicato per '{file_name}' in file_handler.py", 
                 details={"caller": caller_filename, "class": self.__class__.__name__})
        else:
            # Solo se siamo nella classe principale, tracciamo il ciclo di vita
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
            info(
                f"🔄 Re-invio file modificato: {file_name}",
                details={
                    "file_name": file_name,
                    "filter_decision": filter_decision
                }
            )
            self._send_file_to_backend(file_path, 'modified', filter_decision)
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
            if is_rename:
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
        import requests
        from .logger import info, error, warning
        
        try:
            import os
            BACKEND_HOST = os.getenv("BACKEND_HOST") or "localhost"
            BACKEND_PORT = os.getenv("BACKEND_PORT") or "8000"
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
            
            # Cerca l'evento esistente o crea un nuovo evento
            event_id = self.event_buffer.find_event_by_filename(file_name)
            
            # Se non esiste un evento, ne creiamo uno adesso
            if not event_id:
                event_id = self.event_buffer.add_event(action, file_name, self.folder, {
                    'full_path': file_path,
                    'relative_path': self._get_relative_path(file_path),
                    'filter_action': filter_decision['action'],
                    'extract_metadata': filter_decision['extract_metadata']
                })
            
            # Aggiorna lo stato dell'evento a 'processing'
            self.event_buffer.update_event_status(event_id, 'processing')
            
            import requests
            BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
            BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", f"http://localhost:{BACKEND_PORT}")
            UPLOAD_URL = f"{BACKEND_BASE_URL}/api/document-monitor/upload/"
            
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
                
                resp = requests.post(UPLOAD_URL, files=files, data=data, timeout=30)
            
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
                
                # Tracciamento del ciclo di vita: documento trasmesso al backend
                document_transmitted(
                    document_id=file_name,
                    target_system="backend",
                    status="success",
                    details={
                        "action": action,
                        "response_code": resp.status_code,
                        "file_path": file_path
                    }
                )
                
                # Elaborazione della risposta dal backend
                try:
                    result = resp.json()
                    document_id = None
                    
                    # Log completo della risposta per debug
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
                    
                    # Se il file è un duplicato, aggiorna lo stato dell'evento
                    if is_duplicate:
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
                    if not document_id:
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
                    
                    if document_id:
                        self.event_buffer.update_event_document_id(event_id, document_id)
                        info(f"Document ID salvato nell'evento {event_id}: {document_id}")
                        
                        # Tracciamento del ciclo di vita: documento archiviato nel sistema
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
                    else:
                        warning(f"⚠️ Nessun document_id trovato nella risposta per '{file_name}'", 
                                details={"file_name": file_name})
                    
                    # Se non è stato già impostato come duplicato, imposta lo stato a 'completed'
                    # Controlla prima lo stato attuale dell'evento
                    # Dobbiamo leggere lo stato corrente dal database
                    current_state = self.event_buffer.get_event_status(event_id)
                    if current_state != 'duplicate':
                        # Solo se non è già stato impostato come duplicato, imposta come completato
                        self.event_buffer.update_event_status(event_id, 'completed')
                        info(f"Stato dell'evento aggiornato a 'completed' per '{file_name}'", 
                             details={"file_name": file_name, "event_id": event_id})
                        
                        # Tracciamento del ciclo di vita: documento processato
                        document_processed(
                            document_id=document_id or file_name,  # Usa document_id se disponibile, altrimenti file_name
                            processor_id="backend_workflow",
                            status="completed",
                            details={
                                "file_name": file_name,
                                "event_id": event_id,
                                "workflow_result": "success"
                            }
                        )
                except Exception as e:
                    warning(
                        f"⚠️ Errore durante l'estrazione del document_id per '{file_name}'",
                        details={"file_name": file_name, "error": str(e)}
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
            
            import requests
            BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
            BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", f"http://localhost:{BACKEND_PORT}")
            
            # Utilizziamo l'endpoint corretto per la cancellazione dei file PDF monitorati
            DELETE_URL = f"{BACKEND_BASE_URL}/api/document-monitor/delete/"
            
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
                
                # Tenta anche di rimuovere il file dal vectorstore (per compatibilità)
                try:
                    DELETE_DOCUMENT_URL = f"{BACKEND_BASE_URL}/api/documents/{filename}"
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

# Mantieni compatibilità
DocsHandler = SmartFileHandler
EnhancedFileHandler = SmartFileHandler
