import json
import aiohttp
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Logger adapter: prefer local .logger, fallback to pramaialog client, else stdlib
try:
    from .logger import debug as log_debug, info as log_info, warning as log_warning, error as log_error
    from .logger import flush as log_flush, close as log_close
except Exception:
    try:
        from PramaIA_LogService.clients.pramaialog import PramaIALogger

        _pl = PramaIALogger()

        def log_debug(*a, **k):
            try:
                _pl.debug(*a, **k)
            except Exception:
                pass

        def log_info(*a, **k):
            try:
                _pl.info(*a, **k)
            except Exception:
                pass

        def log_warning(*a, **k):
            try:
                _pl.warning(*a, **k)
            except Exception:
                pass

        def log_error(*a, **k):
            try:
                _pl.error(*a, **k)
            except Exception:
                pass
    except Exception:
        import logging as _std_logging

        _logger = _std_logging.getLogger(__name__)

        def log_debug(*a, **k):
            _logger.debug(*a, **k)

        def log_info(*a, **k):
            _logger.info(*a, **k)

        def log_warning(*a, **k):
            _logger.warning(*a, **k)

        def log_error(*a, **k):
            _logger.error(*a, **k)

class MetadataSearchProcessor:
    """
    Processore per ricerche sui metadati dei documenti.
    Interfaccia con VectorstoreService per cercare documenti basandosi su metadati
    come date di creazione, autori, tipi di file, dimensioni, etc.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Configurazione del VectorstoreService
        self.vectorstore_base_url = config.get("vectorstore_base_url", "http://localhost:8090")
        self.max_results = config.get("max_results", 10)
        self.timeout = config.get("timeout", 30)
        
        # Configurazione ricerca metadati
        self.date_formats = config.get("date_formats", [
            "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"
        ])
        
        self.temporal_keywords = config.get("temporal_keywords", {
            "oggi": 0,
            "ieri": -1,
            "settimana": -7,
            "mese": -30,
            "anno": -365,
            "recente": -7,
            "ultimo": -30
        })
        
        self.file_type_mapping = config.get("file_type_mapping", {
            "pdf": [".pdf"],
            "documento": [".doc", ".docx", ".txt"],
            "immagine": [".jpg", ".jpeg", ".png", ".gif"],
            "excel": [".xls", ".xlsx"],
            "powerpoint": [".ppt", ".pptx"]
        })
        
        self._log_info(f"Metadata Search Processor inizializzato per nodo {node_id}")
        self._log_info(f"VectorstoreService URL: {self.vectorstore_base_url}")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Esegue una ricerca basata sui metadati.
        
        Args:
            inputs: Dizionario con la query e criteri di ricerca
            
        Returns:
            Dizionario con i risultati della ricerca sui metadati
        """
        try:
            # Estrai parametri dall'input
            question = inputs.get("question", inputs.get("query", ""))
            if not question:
                raise ValueError("Campo 'question' o 'query' richiesto ma non fornito")
            
            max_results = inputs.get("max_results", inputs.get("limit", self.max_results))
            
            # Metadati della ricerca
            user_id = inputs.get("user_id")
            session_id = inputs.get("session_id")
            
            self._log_info(f"Ricerca metadati per: '{question[:100]}...'")
            
            # Analizza la query per estrarre criteri di metadati
            metadata_criteria = self._extract_metadata_criteria(question)
            
            # Ottieni la lista completa dei documenti
            all_documents = await self._fetch_all_documents()
            
            # Filtra i documenti basandosi sui criteri di metadati
            filtered_documents = self._filter_by_metadata(all_documents, metadata_criteria)
            
            # Limita i risultati
            limited_results = filtered_documents[:max_results]
            
            # Prepara l'output
            result = {
                "search_type": "metadata",
                "query": question,
                "criteria": metadata_criteria,
                "results": limited_results,
                "total_found": len(filtered_documents),
                "total_returned": len(limited_results),
                "search_metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "vectorstore_url": self.vectorstore_base_url,
                    "max_results_requested": max_results
                }
            }
            
            self._log_info(f"Ricerca metadati completata: {len(limited_results)} risultati trovati")
            
            return result
            
        except Exception as e:
            self._log_error(f"Errore nella ricerca metadati: {e}")
            
            return {
                "search_type": "metadata",
                "query": inputs.get("question", ""),
                "results": [],
                "total_found": 0,
                "error": str(e),
                "search_metadata": {
                    "error": True,
                    "timestamp": time.time()
                }
            }
    
    def _extract_metadata_criteria(self, question: str) -> Dict[str, Any]:
        """
        Estrae criteri di ricerca sui metadati dalla query.
        
        Args:
            question: Domanda dell'utente
            
        Returns:
            Dizionario con i criteri di ricerca estratti
        """
        question_lower = question.lower()
        criteria = {}
        
        # Estrai criteri temporali
        date_criteria = self._extract_date_criteria(question_lower)
        if date_criteria:
            criteria["date"] = date_criteria
        
        # Estrai criteri sui tipi di file
        file_type_criteria = self._extract_file_type_criteria(question_lower)
        if file_type_criteria:
            criteria["file_type"] = file_type_criteria
        
        # Estrai criteri su autore/creatore
        author_criteria = self._extract_author_criteria(question_lower)
        if author_criteria:
            criteria["author"] = author_criteria
        
        # Estrai criteri su dimensione
        size_criteria = self._extract_size_criteria(question_lower)
        if size_criteria:
            criteria["size"] = size_criteria
        
        # Estrai criteri su collezione
        collection_criteria = self._extract_collection_criteria(question_lower)
        if collection_criteria:
            criteria["collection"] = collection_criteria
        
        return criteria
    
    def _extract_date_criteria(self, question_lower: str) -> Optional[Dict[str, Any]]:
        """Estrae criteri di ricerca basati sulla data."""
        date_criteria = {}
        
        # Cerca date specifiche
        for date_format in self.date_formats:
            pattern = None
            if date_format == "%Y-%m-%d":
                pattern = r'\b\d{4}-\d{1,2}-\d{1,2}\b'
            elif date_format == "%d/%m/%Y":
                pattern = r'\b\d{1,2}/\d{1,2}/\d{4}\b'
            elif date_format == "%d-%m-%Y":
                pattern = r'\b\d{1,2}-\d{1,2}-\d{4}\b'
            
            if pattern:
                matches = re.findall(pattern, question_lower)
                if matches:
                    try:
                        parsed_date = datetime.strptime(matches[0], date_format)
                        date_criteria["specific_date"] = parsed_date.isoformat()
                        break
                    except ValueError:
                        continue
        
        # Cerca riferimenti temporali relativi
        for keyword, days_offset in self.temporal_keywords.items():
            if keyword in question_lower:
                target_date = datetime.now() + timedelta(days=days_offset)
                if days_offset == 0:  # "oggi"
                    date_criteria["date_range"] = {
                        "start": target_date.replace(hour=0, minute=0, second=0).isoformat(),
                        "end": target_date.replace(hour=23, minute=59, second=59).isoformat()
                    }
                elif days_offset == -1:  # "ieri"
                    date_criteria["date_range"] = {
                        "start": target_date.replace(hour=0, minute=0, second=0).isoformat(),
                        "end": target_date.replace(hour=23, minute=59, second=59).isoformat()
                    }
                else:  # periodi più lunghi
                    date_criteria["date_range"] = {
                        "start": target_date.isoformat(),
                        "end": datetime.now().isoformat()
                    }
                break
        
        # Cerca anni specifici
        year_matches = re.findall(r'\b(20\d{2}|19\d{2})\b', question_lower)
        if year_matches:
            year = int(year_matches[0])
            date_criteria["year"] = year
        
        return date_criteria if date_criteria else None
    
    def _extract_file_type_criteria(self, question_lower: str) -> Optional[List[str]]:
        """Estrae criteri di ricerca basati sul tipo di file."""
        file_types = []
        
        for type_name, extensions in self.file_type_mapping.items():
            if type_name in question_lower:
                file_types.extend(extensions)
        
        # Cerca estensioni dirette
        extension_pattern = r'\.(\w+)'
        extension_matches = re.findall(extension_pattern, question_lower)
        for ext in extension_matches:
            file_types.append(f".{ext}")
        
        return list(set(file_types)) if file_types else None
    
    def _extract_author_criteria(self, question_lower: str) -> Optional[str]:
        """Estrae criteri di ricerca basati sull'autore."""
        # Pattern per identificare riferimenti all'autore
        author_patterns = [
            r'autore\s+(.+?)(?:\s|$)',
            r'scritto\s+da\s+(.+?)(?:\s|$)',
            r'creato\s+da\s+(.+?)(?:\s|$)',
            r'di\s+([A-Za-z]+\s+[A-Za-z]+)',
        ]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, question_lower)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _extract_size_criteria(self, question_lower: str) -> Optional[Dict[str, Any]]:
        """Estrae criteri di ricerca basati sulla dimensione."""
        size_criteria = {}
        
        # Cerca riferimenti a dimensioni
        if "grande" in question_lower or "grosso" in question_lower:
            size_criteria["min_size"] = 1024 * 1024  # 1MB
        
        if "piccolo" in question_lower:
            size_criteria["max_size"] = 1024 * 100  # 100KB
        
        # Cerca dimensioni specifiche (MB, KB, GB)
        size_pattern = r'(\d+)\s*(mb|kb|gb)'
        size_matches = re.findall(size_pattern, question_lower)
        if size_matches:
            value, unit = size_matches[0]
            value = int(value)
            if unit == "kb":
                size_bytes = value * 1024
            elif unit == "mb":
                size_bytes = value * 1024 * 1024
            elif unit == "gb":
                size_bytes = value * 1024 * 1024 * 1024
            
            if "maggiore" in question_lower or "più" in question_lower:
                size_criteria["min_size"] = size_bytes
            elif "minore" in question_lower or "meno" in question_lower:
                size_criteria["max_size"] = size_bytes
            else:
                size_criteria["target_size"] = size_bytes
        
        return size_criteria if size_criteria else None
    
    def _extract_collection_criteria(self, question_lower: str) -> Optional[str]:
        """Estrae criteri di ricerca basati sulla collezione."""
        # Cerca riferimenti a collezioni specifiche
        collection_keywords = ["collezione", "cartella", "directory", "gruppo"]
        
        for keyword in collection_keywords:
            if keyword in question_lower:
                # Cerca il nome dopo la parola chiave
                pattern = rf'{keyword}\s+([a-zA-Z0-9_-]+)'
                matches = re.findall(pattern, question_lower)
                if matches:
                    return matches[0]
        
        return None
    
    async def _fetch_all_documents(self) -> List[Dict[str, Any]]:
        """
        Recupera tutti i documenti dal VectorstoreService.
        
        Returns:
            Lista di tutti i documenti con i loro metadati
        """
        documents_url = f"{self.vectorstore_base_url}/documents/"
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Recupera i documenti a pagine per gestire grandi dataset
            all_documents = []
            offset = 0
            limit = 100
            
            while True:
                params = {"limit": limit, "offset": offset}
                
                async with session.get(documents_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        documents = data.get("documents", [])
                        
                        if not documents:
                            break
                        
                        all_documents.extend(documents)
                        
                        # Se abbiamo ricevuto meno documenti del limite, abbiamo finito
                        if len(documents) < limit:
                            break
                        
                        offset += limit
                    else:
                        error_text = await response.text()
                        raise Exception(f"VectorstoreService error {response.status}: {error_text}")
            
            self._log_debug(f"Recuperati {len(all_documents)} documenti totali")
            return all_documents
    
    def _filter_by_metadata(self, documents: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filtra i documenti basandosi sui criteri di metadati.
        
        Args:
            documents: Lista di documenti da filtrare
            criteria: Criteri di filtro
            
        Returns:
            Lista di documenti filtrati
        """
        filtered = []
        
        for doc in documents:
            if self._document_matches_criteria(doc, criteria):
                # Aggiungi informazioni sulla corrispondenza
                doc_copy = doc.copy()
                doc_copy["match_criteria"] = self._get_match_reasons(doc, criteria)
                doc_copy["match_score"] = self._calculate_metadata_match_score(doc, criteria)
                filtered.append(doc_copy)
        
        # Ordina per punteggio di corrispondenza
        filtered.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return filtered
    
    def _document_matches_criteria(self, doc: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """
        Verifica se un documento corrisponde ai criteri specificati.
        
        Args:
            doc: Documento da verificare
            criteria: Criteri di filtro
            
        Returns:
            True se il documento corrisponde ai criteri
        """
        # Filtra per data
        if "date" in criteria:
            if not self._matches_date_criteria(doc, criteria["date"]):
                return False
        
        # Filtra per tipo di file
        if "file_type" in criteria:
            if not self._matches_file_type_criteria(doc, criteria["file_type"]):
                return False
        
        # Filtra per autore
        if "author" in criteria:
            if not self._matches_author_criteria(doc, criteria["author"]):
                return False
        
        # Filtra per dimensione
        if "size" in criteria:
            if not self._matches_size_criteria(doc, criteria["size"]):
                return False
        
        # Filtra per collezione
        if "collection" in criteria:
            if not self._matches_collection_criteria(doc, criteria["collection"]):
                return False
        
        return True
    
    def _matches_date_criteria(self, doc: Dict[str, Any], date_criteria: Dict[str, Any]) -> bool:
        """Verifica se il documento corrisponde ai criteri di data."""
        doc_created_at = doc.get("created_at")
        if not doc_created_at:
            return False
        
        try:
            # Converte la data del documento in datetime
            if isinstance(doc_created_at, str):
                doc_date = datetime.fromisoformat(doc_created_at.replace('Z', '+00:00'))
            else:
                doc_date = doc_created_at
            
            # Verifica data specifica
            if "specific_date" in date_criteria:
                target_date = datetime.fromisoformat(date_criteria["specific_date"])
                return doc_date.date() == target_date.date()
            
            # Verifica range di date
            if "date_range" in date_criteria:
                start_date = datetime.fromisoformat(date_criteria["date_range"]["start"])
                end_date = datetime.fromisoformat(date_criteria["date_range"]["end"])
                return start_date <= doc_date <= end_date
            
            # Verifica anno
            if "year" in date_criteria:
                return doc_date.year == date_criteria["year"]
            
        except (ValueError, TypeError) as e:
            self._log_warning(f"Errore nel parsing della data per documento {doc.get('id', 'unknown')}: {e}")
            return False
        
        return True
    
    def _matches_file_type_criteria(self, doc: Dict[str, Any], file_types: List[str]) -> bool:
        """Verifica se il documento corrisponde ai criteri di tipo file."""
        # Controlla il nome del file se presente
        filename = doc.get("filename", doc.get("metadata", {}).get("filename", ""))
        if filename:
            filename_lower = filename.lower()
            return any(filename_lower.endswith(ext) for ext in file_types)
        
        # Controlla il tipo MIME se presente
        mime_type = doc.get("metadata", {}).get("mime_type", "")
        if mime_type:
            # Mappatura semplice di tipi MIME
            mime_type_lower = mime_type.lower()
            for ext in file_types:
                if ext == ".pdf" and "pdf" in mime_type_lower:
                    return True
                if ext in [".jpg", ".jpeg", ".png", ".gif"] and "image" in mime_type_lower:
                    return True
                if ext in [".doc", ".docx"] and "word" in mime_type_lower:
                    return True
        
        return False
    
    def _matches_author_criteria(self, doc: Dict[str, Any], author: str) -> bool:
        """Verifica se il documento corrisponde ai criteri di autore."""
        metadata = doc.get("metadata", {})
        
        # Controlla vari campi per l'autore
        author_fields = ["author", "creator", "created_by", "owner"]
        author_lower = author.lower()
        
        for field in author_fields:
            doc_author = metadata.get(field, "")
            if doc_author and author_lower in doc_author.lower():
                return True
        
        return False
    
    def _matches_size_criteria(self, doc: Dict[str, Any], size_criteria: Dict[str, Any]) -> bool:
        """Verifica se il documento corrisponde ai criteri di dimensione."""
        doc_size = doc.get("metadata", {}).get("file_size")
        if doc_size is None:
            return False
        
        try:
            doc_size = int(doc_size)
            
            if "min_size" in size_criteria and doc_size < size_criteria["min_size"]:
                return False
            
            if "max_size" in size_criteria and doc_size > size_criteria["max_size"]:
                return False
            
            if "target_size" in size_criteria:
                # Permetti una tolleranza del 10%
                target = size_criteria["target_size"]
                tolerance = target * 0.1
                return abs(doc_size - target) <= tolerance
            
        except (ValueError, TypeError):
            return False
        
        return True
    
    def _matches_collection_criteria(self, doc: Dict[str, Any], collection: str) -> bool:
        """Verifica se il documento corrisponde ai criteri di collezione."""
        doc_collection = doc.get("collection", "")
        return collection.lower() in doc_collection.lower()
    
    def _get_match_reasons(self, doc: Dict[str, Any], criteria: Dict[str, Any]) -> List[str]:
        """Ottiene le ragioni per cui il documento corrisponde ai criteri."""
        reasons = []
        
        if "date" in criteria and self._matches_date_criteria(doc, criteria["date"]):
            reasons.append("Data corrispondente")
        
        if "file_type" in criteria and self._matches_file_type_criteria(doc, criteria["file_type"]):
            reasons.append("Tipo file corrispondente")
        
        if "author" in criteria and self._matches_author_criteria(doc, criteria["author"]):
            reasons.append("Autore corrispondente")
        
        if "size" in criteria and self._matches_size_criteria(doc, criteria["size"]):
            reasons.append("Dimensione corrispondente")
        
        if "collection" in criteria and self._matches_collection_criteria(doc, criteria["collection"]):
            reasons.append("Collezione corrispondente")
        
        return reasons
    
    def _calculate_metadata_match_score(self, doc: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calcola un punteggio di corrispondenza per i metadati."""
        score = 0.0
        total_criteria = len(criteria)
        
        if total_criteria == 0:
            return 0.0
        
        # Ogni criterio soddisfatto aggiunge punti
        if "date" in criteria and self._matches_date_criteria(doc, criteria["date"]):
            score += 1.0
        
        if "file_type" in criteria and self._matches_file_type_criteria(doc, criteria["file_type"]):
            score += 1.0
        
        if "author" in criteria and self._matches_author_criteria(doc, criteria["author"]):
            score += 1.0
        
        if "size" in criteria and self._matches_size_criteria(doc, criteria["size"]):
            score += 1.0
        
        if "collection" in criteria and self._matches_collection_criteria(doc, criteria["collection"]):
            score += 1.0
        
        return score / total_criteria
    
    def _log_info(self, message: str) -> None:
        """Registra un messaggio informativo."""
        try:
            log_info(f"[MetadataSearch] {message}")
        except Exception:
            pass
    
    def _log_debug(self, message: str) -> None:
        """Registra un messaggio di debug."""
        try:
            log_debug(f"[MetadataSearch] {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """Registra un messaggio di avviso."""
        try:
            log_warning(f"[MetadataSearch] {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """Registra un messaggio di errore."""
        try:
            log_error(f"[MetadataSearch] {message}")
        except Exception:
            pass