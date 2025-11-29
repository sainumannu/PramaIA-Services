"""
File Operations Processor - Gestione avanzata operazioni sui file.

Questo processore fornisce funzionalità complete per:
- Aprire Explorer su path specifici
- Copiare/spostare file e cartelle
- Eliminare file con conferma
- Creare/estrarre archivi ZIP
- Ottenere informazioni sui file
- Creare cartelle
"""

import os
import sys
import shutil
import zipfile
import subprocess
import platform
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import tkinter as tk
from tkinter import messagebox

# Configurazione logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileOperationsProcessor:
    """Processore per operazioni avanzate sui file del sistema."""
    
    def __init__(self):
        """Inizializza il processore."""
        self.platform = platform.system().lower()
        logger.info(f"FileOperationsProcessor inizializzato su piattaforma: {self.platform}")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Esegue l'operazione sui file specificata.
        
        Args:
            inputs: Dizionario con parametri di input
            
        Returns:
            Dizionario con risultati dell'operazione
        """
        try:
            operation = inputs.get('operation', '').lower()
            source_path = inputs.get('source_path', '')
            destination_path = inputs.get('destination_path', '')
            confirm_delete = inputs.get('confirm_delete', True)
            overwrite = inputs.get('overwrite', False)
            zip_compression = inputs.get('zip_compression', 'best')
            
            logger.info(f"Esecuzione operazione: {operation} su {source_path}")
            
            # Validazione input base
            if not operation:
                return self._error_result("Operazione non specificata")
            
            if not source_path:
                return self._error_result("Path sorgente non specificato")
            
            # Dispatch operazione
            operations = {
                'open_explorer': self._open_explorer,
                'copy': self._copy_file,
                'move': self._move_file,
                'delete': self._delete_file,
                'zip': self._create_zip,
                'unzip': self._extract_zip,
                'create_dir': self._create_directory,
                'file_info': self._get_file_info
            }
            
            if operation not in operations:
                return self._error_result(f"Operazione '{operation}' non supportata")
            
            # Esegui operazione
            result = await operations[operation](
                source_path, destination_path, 
                confirm_delete, overwrite, zip_compression
            )
            
            logger.info(f"Operazione {operation} completata con successo")
            return result
            
        except Exception as e:
            error_msg = f"Errore durante operazione sui file: {str(e)}"
            logger.error(error_msg)
            return self._error_result(error_msg)
    
    async def _open_explorer(self, source_path: str, *args) -> Dict[str, Any]:
        """Apre finestra Explorer/Finder sul path specificato."""
        try:
            path = Path(source_path)
            
            # Verifica che il path esista
            if not path.exists():
                return self._error_result(f"Path non esistente: {source_path}")
            
            # Se è un file, apri la cartella contenitore
            if path.is_file():
                path = path.parent
            
            # Comando specifico per piattaforma
            if self.platform == 'windows':
                subprocess.run(['explorer', str(path)], check=True)
            elif self.platform == 'darwin':  # macOS
                subprocess.run(['open', str(path)], check=True)
            elif self.platform == 'linux':
                subprocess.run(['xdg-open', str(path)], check=True)
            else:
                return self._error_result(f"Piattaforma {self.platform} non supportata per aprire explorer")
            
            return self._success_result(
                f"Explorer aperto su: {path}",
                result_path=str(path)
            )
            
        except subprocess.CalledProcessError as e:
            return self._error_result(f"Errore nell'aprire explorer: {e}")
        except Exception as e:
            return self._error_result(f"Errore inaspettato: {e}")
    
    async def _copy_file(self, source_path: str, destination_path: str, 
                        confirm_delete: bool, overwrite: bool, *args) -> Dict[str, Any]:
        """Copia file o cartella da source a destination."""
        try:
            if not destination_path:
                return self._error_result("Path di destinazione richiesto per operazione copy")
            
            source = Path(source_path)
            dest = Path(destination_path)
            
            # Verifica sorgente
            if not source.exists():
                return self._error_result(f"Sorgente non esistente: {source_path}")
            
            # Verifica destinazione esistente
            if dest.exists() and not overwrite:
                return self._error_result(f"Destinazione già esistente: {destination_path}")
            
            # Crea cartella destinazione se necessaria
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copia file o cartella
            if source.is_file():
                shutil.copy2(source, dest)
                operation_type = "file"
            elif source.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(source, dest)
                operation_type = "cartella"
            else:
                return self._error_result(f"Tipo di sorgente non supportato: {source_path}")
            
            # Ottieni info del risultato
            file_info = self._get_path_info(dest)
            
            return self._success_result(
                f"{operation_type.capitalize()} copiato/a da {source} a {dest}",
                result_path=str(dest),
                file_info=file_info
            )
            
        except PermissionError:
            return self._error_result(f"Permessi insufficienti per copiare {source_path}")
        except Exception as e:
            return self._error_result(f"Errore durante copia: {e}")
    
    async def _move_file(self, source_path: str, destination_path: str, 
                        confirm_delete: bool, overwrite: bool, *args) -> Dict[str, Any]:
        """Sposta file o cartella da source a destination."""
        try:
            if not destination_path:
                return self._error_result("Path di destinazione richiesto per operazione move")
            
            source = Path(source_path)
            dest = Path(destination_path)
            
            # Verifica sorgente
            if not source.exists():
                return self._error_result(f"Sorgente non esistente: {source_path}")
            
            # Verifica destinazione esistente
            if dest.exists() and not overwrite:
                return self._error_result(f"Destinazione già esistente: {destination_path}")
            
            # Crea cartella destinazione se necessaria
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Determina il tipo prima dello spostamento
            operation_type = "File" if source.is_file() else "Cartella"
            
            # Sposta file o cartella
            if dest.exists() and overwrite:
                if dest.is_file():
                    dest.unlink()
                elif dest.is_dir():
                    shutil.rmtree(dest)
            
            shutil.move(source, dest)
            
            # Ottieni info del risultato
            file_info = self._get_path_info(dest)
            
            return self._success_result(
                f"{operation_type} spostato/a da {source_path} a {dest}",
                result_path=str(dest),
                file_info=file_info
            )
            
        except PermissionError:
            return self._error_result(f"Permessi insufficienti per spostare {source_path}")
        except Exception as e:
            return self._error_result(f"Errore durante spostamento: {e}")
    
    async def _delete_file(self, source_path: str, destination_path: str,
                          confirm_delete: bool, *args) -> Dict[str, Any]:
        """Elimina file o cartella con conferma opzionale."""
        try:
            source = Path(source_path)
            
            if not source.exists():
                return self._error_result(f"File non esistente: {source_path}")
            
            # Richiesta conferma se abilitata
            if confirm_delete:
                confirmed = self._confirm_deletion(source)
                if not confirmed:
                    return self._success_result("Operazione annullata dall'utente")
            
            # Elimina file o cartella
            if source.is_file():
                source.unlink()
                operation_type = "File"
            elif source.is_dir():
                shutil.rmtree(source)
                operation_type = "Cartella"
            else:
                return self._error_result(f"Tipo non supportato per eliminazione: {source_path}")
            
            return self._success_result(
                f"{operation_type} eliminato/a: {source_path}"
            )
            
        except PermissionError:
            return self._error_result(f"Permessi insufficienti per eliminare {source_path}")
        except Exception as e:
            return self._error_result(f"Errore durante eliminazione: {e}")
    
    async def _create_zip(self, source_path: str, destination_path: str,
                         confirm_delete: bool, overwrite: bool, zip_compression: str) -> Dict[str, Any]:
        """Crea archivio ZIP da file o cartella."""
        try:
            if not destination_path:
                # Genera nome ZIP automatico
                source = Path(source_path)
                destination_path = str(source.with_suffix('.zip'))
            
            source = Path(source_path)
            dest = Path(destination_path)
            
            if not source.exists():
                return self._error_result(f"Sorgente non esistente: {source_path}")
            
            # Verifica destinazione
            if dest.exists() and not overwrite:
                return self._error_result(f"ZIP già esistente: {destination_path}")
            
            # Configurazione compressione
            compression_levels = {
                'none': zipfile.ZIP_STORED,
                'fast': zipfile.ZIP_DEFLATED,
                'best': zipfile.ZIP_DEFLATED
            }
            compression = compression_levels.get(zip_compression, zipfile.ZIP_DEFLATED)
            
            # Crea ZIP
            with zipfile.ZipFile(dest, 'w', compression=compression) as zipf:
                if source.is_file():
                    zipf.write(source, source.name)
                    files_count = 1
                elif source.is_dir():
                    files_count = 0
                    for file_path in source.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(source)
                            zipf.write(file_path, arcname)
                            files_count += 1
                else:
                    return self._error_result(f"Tipo sorgente non supportato: {source_path}")
            
            # Info ZIP creato
            zip_info = self._get_path_info(dest)
            zip_info['files_count'] = files_count
            zip_info['compression'] = zip_compression
            
            return self._success_result(
                f"ZIP creato: {dest} ({files_count} file)",
                result_path=str(dest),
                file_info=zip_info
            )
            
        except Exception as e:
            return self._error_result(f"Errore durante creazione ZIP: {e}")
    
    async def _extract_zip(self, source_path: str, destination_path: str,
                          confirm_delete: bool, overwrite: bool, *args) -> Dict[str, Any]:
        """Estrae archivio ZIP."""
        try:
            source = Path(source_path)
            
            if not source.exists():
                return self._error_result(f"ZIP non esistente: {source_path}")
            
            if not source.suffix.lower() == '.zip':
                return self._error_result(f"File non è un ZIP: {source_path}")
            
            # Destination di default: stessa cartella del ZIP
            if not destination_path:
                destination_path = str(source.parent / source.stem)
            
            dest = Path(destination_path)
            
            # Verifica destinazione
            if dest.exists() and not overwrite:
                return self._error_result(f"Cartella di destinazione già esistente: {destination_path}")
            
            # Crea cartella destinazione
            dest.mkdir(parents=True, exist_ok=True)
            
            # Estrai ZIP
            with zipfile.ZipFile(source, 'r') as zipf:
                zipf.extractall(dest)
                files_count = len(zipf.namelist())
            
            # Info estrazione
            extract_info = self._get_path_info(dest)
            extract_info['extracted_files'] = files_count
            
            return self._success_result(
                f"ZIP estratto: {files_count} file in {dest}",
                result_path=str(dest),
                file_info=extract_info
            )
            
        except zipfile.BadZipFile:
            return self._error_result(f"File ZIP corrotto: {source_path}")
        except Exception as e:
            return self._error_result(f"Errore durante estrazione ZIP: {e}")
    
    async def _create_directory(self, source_path: str, *args) -> Dict[str, Any]:
        """Crea cartella."""
        try:
            dest = Path(source_path)
            
            if dest.exists():
                return self._error_result(f"Cartella già esistente: {source_path}")
            
            # Crea cartella e genitori se necessari
            dest.mkdir(parents=True, exist_ok=False)
            
            # Info cartella creata
            dir_info = self._get_path_info(dest)
            
            return self._success_result(
                f"Cartella creata: {dest}",
                result_path=str(dest),
                file_info=dir_info
            )
            
        except PermissionError:
            return self._error_result(f"Permessi insufficienti per creare cartella: {source_path}")
        except Exception as e:
            return self._error_result(f"Errore durante creazione cartella: {e}")
    
    async def _get_file_info(self, source_path: str, *args) -> Dict[str, Any]:
        """Ottiene informazioni dettagliate su file o cartella."""
        try:
            source = Path(source_path)
            
            if not source.exists():
                return self._error_result(f"Path non esistente: {source_path}")
            
            file_info = self._get_path_info(source)
            
            # Info aggiuntive per cartelle
            if source.is_dir():
                try:
                    files = list(source.rglob('*'))
                    file_info['total_items'] = len(files)
                    file_info['files_count'] = len([f for f in files if f.is_file()])
                    file_info['dirs_count'] = len([f for f in files if f.is_dir()])
                except PermissionError:
                    file_info['access_error'] = "Permessi insufficienti per analizzare contenuto"
            
            return self._success_result(
                f"Informazioni ottenute per: {source_path}",
                file_info=file_info
            )
            
        except Exception as e:
            return self._error_result(f"Errore durante recupero informazioni: {e}")
    
    def _get_path_info(self, path: Path) -> Dict[str, Any]:
        """Ottiene informazioni dettagliate su un path."""
        try:
            stat = path.stat()
            
            info = {
                'path': str(path),
                'name': path.name,
                'parent': str(path.parent),
                'exists': path.exists(),
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'size_bytes': stat.st_size,
                'size_human': self._format_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:],
                'extension': path.suffix.lower()
            }
            
            return info
            
        except Exception as e:
            return {
                'path': str(path),
                'error': f"Errore nel recupero info: {e}"
            }
    
    def _format_size(self, size_bytes: int) -> str:
        """Formatta dimensione file in formato human-readable."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
    
    def _confirm_deletion(self, path: Path) -> bool:
        """Mostra dialog di conferma per eliminazione."""
        try:
            root = tk.Tk()
            root.withdraw()  # Nasconde finestra principale
            
            file_type = "cartella" if path.is_dir() else "file"
            message = f"Sei sicuro di voler eliminare il {file_type}:\\n\\n{path}\\n\\nQuesta operazione non può essere annullata."
            
            result = messagebox.askyesno(
                "Conferma eliminazione",
                message,
                icon='warning'
            )
            
            root.destroy()
            return result
            
        except Exception as e:
            logger.warning(f"Errore nella conferma eliminazione: {e}")
            # Fallback: assumiamo conferma
            return True
    
    def _success_result(self, message: str, result_path: str = "", file_info: Dict = None) -> Dict[str, Any]:
        """Crea risultato di successo."""
        result = {
            'success': True,
            'message': message,
            'result_path': result_path,
            'file_info': file_info or {},
            'error': ''
        }
        return result
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Crea risultato di errore."""
        result = {
            'success': False,
            'message': f"Errore: {error_message}",
            'result_path': '',
            'file_info': {},
            'error': error_message
        }
        return result