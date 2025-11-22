"""
Client per interrogare i filtri del server da utilizzare negli agent
Ottimizza il trasferimento evitando file non processabili
"""

import requests
import logging
from typing import Dict, List, Optional, Any
import os
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class AgentFilterClient:
    """
    Client per gli agent per interrogare i filtri del server
    """
    
    def __init__(self, backend_url: Optional[str] = None):
        # Risolvi backend URL con priorità: BACKEND_URL -> BACKEND_BASE_URL -> BACKEND_HOST+PORT -> fallback
        if backend_url:
            resolved = backend_url
        else:
            resolved = os.getenv("BACKEND_URL")
            if not resolved:
                resolved = os.getenv("BACKEND_BASE_URL")
                if not resolved:
                    backend_host = os.getenv("BACKEND_HOST", "localhost")
                    backend_port = os.getenv("BACKEND_PORT", "8000")
                    resolved = f"http://{backend_host}:{backend_port}"

        self.backend_url = resolved
        self.filters_endpoint = f"{self.backend_url}/api/agent-filters"
        self.cached_extensions = None
        self.cache_timestamp = 0
        self.cache_ttl = 300  # Cache per 5 minuti
        
    def should_process_file(self, file_path: str, file_size_bytes: Optional[int] = None) -> Dict[str, Any]:
        """
        Determina se e come processare un file
        
        Returns:
            - should_upload: bool
            - should_process_content: bool
            - action: str
            - extract_metadata: List[str]
        """
        try:
            # Pre-filtering locale con cache per ottimizzare
            if self._should_skip_by_extension(file_path):
                return {
                    "should_upload": False,
                    "should_process_content": False,
                    "action": "skip",
                    "extract_metadata": [],
                    "reason": "Extension filtered locally"
                }
            
            # Query server per decisione definitiva
            response = requests.post(
                f"{self.filters_endpoint}/evaluate-file/",
                json={
                    "file_path": file_path,
                    "file_size_bytes": file_size_bytes
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                evaluation = result["evaluation"]
                
                return {
                    "should_upload": evaluation.get("should_upload", False),
                    "should_process_content": evaluation.get("should_process", False),
                    "action": evaluation.get("action", "skip"),
                    "extract_metadata": evaluation.get("extract_metadata", []),
                    "filter_name": evaluation.get("filter_name", "unknown"),
                    "file_size_mb": evaluation.get("file_size_mb", 0),
                    "reason": f"Server filter: {evaluation.get('filter_name', 'unknown')}"
                }
            else:
                logger.warning(f"Errore query filtri server: {response.status_code}")
                return self._fallback_decision(file_path, file_size_bytes)
                
        except Exception as e:
            logger.warning(f"Errore connessione filtri server: {e}")
            return self._fallback_decision(file_path, file_size_bytes)
            
    def evaluate_batch_files(self, files_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valuta un batch di file per ottimizzare le chiamate API
        
        Args:
            files_info: Lista di {"file_path": "...", "file_size_bytes": 123}
        """
        try:
            # Pre-filtering locale per file ovviamente da skippare
            filtered_files = []
            skipped_locally = []
            
            for file_info in files_info:
                file_path = file_info.get("file_path", "")
                if self._should_skip_by_extension(file_path):
                    skipped_locally.append({
                        "file_path": file_path,
                        "evaluation": {
                            "action": "skip",
                            "should_upload": False,
                            "should_process": False,
                            "reason": "Skipped locally by extension"
                        }
                    })
                else:
                    filtered_files.append(file_info)
            
            # Query server solo per file che potrebbero essere processabili
            server_results = []
            if filtered_files:
                response = requests.post(
                    f"{self.filters_endpoint}/evaluate-batch/",
                    json={"files": filtered_files},
                    timeout=30
                )
                
                if response.status_code == 200:
                    batch_result = response.json()
                    server_results = batch_result.get("results", [])
                else:
                    logger.warning(f"Errore batch query filtri: {response.status_code}")
                    # Fallback per ogni file
                    for file_info in filtered_files:
                        server_results.append({
                            "file_path": file_info.get("file_path", ""),
                            "evaluation": self._fallback_decision(
                                file_info.get("file_path", ""),
                                file_info.get("file_size_bytes")
                            )
                        })
            
            # Combina risultati
            all_results = skipped_locally + server_results
            
            return all_results
            
        except Exception as e:
            logger.error(f"Errore batch evaluation: {e}")
            # Fallback per tutti i file
            return [
                {
                    "file_path": file_info.get("file_path", ""),
                    "evaluation": self._fallback_decision(
                        file_info.get("file_path", ""),
                        file_info.get("file_size_bytes")
                    )
                }
                for file_info in files_info
            ]
            
    def get_supported_extensions(self) -> Dict[str, List[str]]:
        """
        Ottieni estensioni supportate, con cache locale
        """
        current_time = time.time()
        
        # Usa cache se valida
        if (self.cached_extensions and 
            current_time - self.cache_timestamp < self.cache_ttl):
            return self.cached_extensions
            
        try:
            response = requests.get(
                f"{self.filters_endpoint}/supported-extensions/",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.cached_extensions = result.get("extensions_by_action", {})
                self.cache_timestamp = current_time
                
                logger.info(f"Cache estensioni aggiornata: {len(self.cached_extensions)} categorie")
                return self.cached_extensions
            else:
                logger.warning(f"Errore ottenimento estensioni: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Errore connessione per estensioni: {e}")
            
        # Fallback con estensioni di base
        return self._get_fallback_extensions()
        
    def _should_skip_by_extension(self, file_path: str) -> bool:
        """
        Pre-filtering locale per evitare chiamate API inutili
        """
        try:
            extension = Path(file_path).suffix.lower()
            
            # Estensioni sempre da skippare (ottimizzazione locale)
            always_skip = {
                '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
                '.exe', '.msi', '.dmg', '.deb', '.rpm',
                '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
                '.iso', '.img', '.bin'
            }
            
            return extension in always_skip
            
        except Exception:
            return False
            
    def _fallback_decision(self, file_path: str, file_size_bytes: Optional[int]) -> Dict[str, Any]:
        """
        Decisione di fallback quando il server non è raggiungibile
        """
        try:
            extension = Path(file_path).suffix.lower()
            file_size_mb = (file_size_bytes or 0) / (1024 * 1024)
            
            # Documenti sicuri da processare
            safe_documents = {'.pdf', '.txt', '.md', '.docx', '.doc'}
            
            # Codice sorgente
            source_code = {'.py', '.js', '.ts', '.html', '.css', '.json'}
            
            if extension in safe_documents and file_size_mb < 50:
                return {
                    "should_upload": True,
                    "should_process_content": True,
                    "action": "process_full",
                    "extract_metadata": ["filename", "size", "modified_date", "path"],
                    "reason": "Fallback - safe document"
                }
            elif extension in source_code and file_size_mb < 5:
                return {
                    "should_upload": True,
                    "should_process_content": True,
                    "action": "process_full",
                    "extract_metadata": ["filename", "size", "modified_date", "path"],
                    "reason": "Fallback - source code"
                }
            elif file_size_mb < 1:  # File molto piccoli - solo metadati
                return {
                    "should_upload": True,
                    "should_process_content": False,
                    "action": "metadata_only",
                    "extract_metadata": ["filename", "size", "modified_date", "path"],
                    "reason": "Fallback - small file metadata"
                }
            else:
                return {
                    "should_upload": False,
                    "should_process_content": False,
                    "action": "skip",
                    "extract_metadata": [],
                    "reason": "Fallback - unknown/large file"
                }
                
        except Exception as e:
            return {
                "should_upload": False,
                "should_process_content": False,
                "action": "skip",
                "extract_metadata": [],
                "reason": f"Fallback error: {str(e)}"
            }
            
    def _get_fallback_extensions(self) -> Dict[str, List[str]]:
        """Estensioni di fallback quando server non raggiungibile"""
        return {
            "process_full": [".pdf", ".txt", ".md", ".docx", ".doc", ".py", ".js", ".html"],
            "metadata_only": [".jpg", ".png", ".mp3", ".wav"],
            "skip": [".mp4", ".avi", ".exe", ".zip", ".rar"]
        }
        
# Istanza globale per gli agent
agent_filter_client = AgentFilterClient()
