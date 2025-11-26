import json
import aiohttp
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from abc import ABC, abstractmethod

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

class MetadataExtractor(ABC):
    """Interfaccia astratta per estrattori di criteri metadati."""
    
    @abstractmethod
    def extract_criteria(self, query: str) -> Dict[str, Any]:
        """Estrae criteri di metadati dalla query."""
        pass

class DateExtractor(MetadataExtractor):
    """Estrattore per criteri temporali."""
    
    def __init__(self, config: Dict[str, Any]):
        self.date_formats = config.get("date_formats", [
            "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"
        ])
        
        self.temporal_keywords = config.get("temporal_keywords", {
            "today": 0, "oggi": 0,
            "yesterday": -1, "ieri": -1,
            "week": -7, "settimana": -7,
            "month": -30, "mese": -30,
            "year": -365, "anno": -365,
            "recent": -7, "recente": -7,
            "last": -30, "ultimo": -30
        })
        
        self.date_patterns = config.get("date_patterns", [
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # YYYY-MM-DD
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',   # DD/MM/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',   # DD-MM-YYYY
            r'\b(20\d{2}|19\d{2})\b'        # Year only
        ])
    
    def extract_criteria(self, query: str) -> Dict[str, Any]:
        """Estrae criteri temporali dalla query."""
        query_lower = query.lower()
        criteria = {}
        
        # Cerca date specifiche
        for pattern in self.date_patterns:
            matches = re.findall(pattern, query)
            if matches:
                date_str = matches[0]
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    if len(date_str) == 4:  # Anno
                        criteria["year"] = int(date_str)
                    else:  # Data completa
                        criteria["specific_date"] = parsed_date.isoformat()
                    break
        
        # Cerca riferimenti temporali relativi
        for keyword, days_offset in self.temporal_keywords.items():
            if keyword in query_lower:
                target_date = datetime.now() + timedelta(days=days_offset)
                
                if days_offset == 0:  # "oggi/today"
                    criteria["date_range"] = {
                        "start": target_date.replace(hour=0, minute=0, second=0).isoformat(),
                        "end": target_date.replace(hour=23, minute=59, second=59).isoformat()
                    }
                elif days_offset == -1:  # "ieri/yesterday"
                    criteria["date_range"] = {
                        "start": target_date.replace(hour=0, minute=0, second=0).isoformat(),
                        "end": target_date.replace(hour=23, minute=59, second=59).isoformat()
                    }
                else:  # periodi più lunghi
                    criteria["date_range"] = {
                        "start": target_date.isoformat(),
                        "end": datetime.now().isoformat()
                    }
                break
        
        return criteria if criteria else {}
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parsa stringa data usando formati configurati."""
        for date_format in self.date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        return None

class FileTypeExtractor(MetadataExtractor):
    """Estrattore per criteri di tipo file."""
    
    def __init__(self, config: Dict[str, Any]):
        self.type_mapping = config.get("type_mapping", {
            "pdf": [".pdf"],
            "document": [".doc", ".docx", ".txt"],
            "documento": [".doc", ".docx", ".txt"],
            "image": [".jpg", ".jpeg", ".png", ".gif"],
            "immagine": [".jpg", ".jpeg", ".png", ".gif"],
            "excel": [".xls", ".xlsx"],
            "powerpoint": [".ppt", ".pptx"],
            "video": [".mp4", ".avi", ".mov"],
            "audio": [".mp3", ".wav", ".flac"]
        })
        
        self.extension_pattern = r'\.(\w+)'
    
    def extract_criteria(self, query: str) -> Dict[str, Any]:
        """Estrae criteri di tipo file."""
        query_lower = query.lower()
        file_types = []
        
        # Cerca tipi nominali
        for type_name, extensions in self.type_mapping.items():
            if type_name in query_lower:
                file_types.extend(extensions)
        
        # Cerca estensioni dirette
        extension_matches = re.findall(self.extension_pattern, query_lower)
        for ext in extension_matches:
            file_types.append(f".{ext}")
        
        return {"file_types": list(set(file_types))} if file_types else {}

class SizeExtractor(MetadataExtractor):
    """Estrattore per criteri di dimensione."""
    
    def __init__(self, config: Dict[str, Any]):
        self.size_keywords = config.get("size_keywords", {
            "large": {"min_size": 1024 * 1024},    # 1MB
            "big": {"min_size": 1024 * 1024},
            "grande": {"min_size": 1024 * 1024},
            "grosso": {"min_size": 1024 * 1024},
            "small": {"max_size": 1024 * 100},      # 100KB
            "little": {"max_size": 1024 * 100},
            "piccolo": {"max_size": 1024 * 100}
        })
        
        self.size_pattern = r'(\d+)\s*(kb|mb|gb|byte)'
        self.size_units = {
            "byte": 1,
            "kb": 1024,
            "mb": 1024 * 1024,
            "gb": 1024 * 1024 * 1024
        }
    
    def extract_criteria(self, query: str) -> Dict[str, Any]:
        """Estrae criteri di dimensione."""
        query_lower = query.lower()
        size_criteria = {}
        
        # Cerca keyword di dimensione
        for keyword, criteria in self.size_keywords.items():
            if keyword in query_lower:
                size_criteria.update(criteria)
                break
        
        # Cerca dimensioni specifiche
        size_matches = re.findall(self.size_pattern, query_lower)
        if size_matches:
            value, unit = size_matches[0]
            value = int(value)
            size_bytes = value * self.size_units.get(unit, 1)
            
            if any(word in query_lower for word in ["greater", "more", "maggiore", "più"]):
                size_criteria["min_size"] = size_bytes
            elif any(word in query_lower for word in ["less", "smaller", "minore", "meno"]):
                size_criteria["max_size"] = size_bytes
            else:
                size_criteria["target_size"] = size_bytes
        
        return size_criteria if size_criteria else {}

class AuthorExtractor(MetadataExtractor):
    """Estrattore per criteri di autore."""
    
    def __init__(self, config: Dict[str, Any]):
        self.author_patterns = config.get("author_patterns", [
            r'author\s+(.+?)(?:\s|$)',
            r'written\s+by\s+(.+?)(?:\s|$)',
            r'created\s+by\s+(.+?)(?:\s|$)',
            r'by\s+([A-Za-z]+\s+[A-Za-z]+)',
            r'autore\s+(.+?)(?:\s|$)',
            r'scritto\s+da\s+(.+?)(?:\s|$)',
            r'creato\s+da\s+(.+?)(?:\s|$)',
            r'di\s+([A-Za-z]+\s+[A-Za-z]+)'
        ])
    
    def extract_criteria(self, query: str) -> Dict[str, Any]:
        """Estrae criteri di autore."""
        query_lower = query.lower()
        
        for pattern in self.author_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                return {"author": matches[0].strip()}
        
        return {}

class GenericMetadataExtractor(MetadataExtractor):
    """Estrattore generico configurabile per qualsiasi campo metadati."""
    
    def __init__(self, config: Dict[str, Any]):
        self.field_patterns = config.get("field_patterns", {})
        # Formato: {"field_name": {"patterns": ["pattern1", "pattern2"], "type": "string|number|boolean"}}
    
    def extract_criteria(self, query: str) -> Dict[str, Any]:
        """Estrae criteri generici."""
        query_lower = query.lower()
        criteria = {}
        
        for field_name, field_config in self.field_patterns.items():
            patterns = field_config.get("patterns", [])
            field_type = field_config.get("type", "string")
            
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                if matches:
                    value = matches[0]
                    
                    # Converte il tipo se necessario
                    if field_type == "number":
                        try:
                            value = float(value)
                        except ValueError:
                            continue
                    elif field_type == "boolean":
                        value = value.lower() in ["true", "yes", "si", "sì", "1"]
                    
                    criteria[field_name] = value
                    break
        
        return criteria

class DataSourceAdapter(ABC):
    """Interfaccia astratta per adattatori di fonte dati."""
    
    @abstractmethod
    async def fetch_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recupera dati dalla fonte."""
        pass
    
    @abstractmethod
    def filter_data(self, data: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtra dati basandosi sui criteri."""
        pass

class VectorstoreAdapter(DataSourceAdapter):
    """Adattatore per VectorstoreService."""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "http://localhost:8090")
        self.timeout = config.get("timeout", 30)
        
        # Mapping tra campi del query e campi del documento
        self.field_mapping = config.get("field_mapping", {
            "created_at": ["created_at", "timestamp", "date_created"],
            "filename": ["filename", "name", "title"],
            "file_size": ["file_size", "size", "length"],
            "author": ["author", "creator", "created_by", "owner"],
            "mime_type": ["mime_type", "content_type", "type"]
        })
    
    async def fetch_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recupera documenti dal VectorstoreService."""
        documents_url = f"{self.base_url}/documents/"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            all_documents = []
            offset = 0
            limit = params.get("batch_size", 100)
            
            while True:
                request_params = {"limit": limit, "offset": offset}
                
                async with session.get(documents_url, params=request_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        documents = data.get("documents", [])
                        
                        if not documents:
                            break
                        
                        all_documents.extend(documents)
                        
                        if len(documents) < limit:
                            break
                        
                        offset += limit
                    else:
                        error_text = await response.text()
                        raise Exception(f"VectorstoreService error {response.status}: {error_text}")
            
            return all_documents
    
    def filter_data(self, data: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtra documenti basandosi sui criteri."""
        filtered = []
        
        for doc in data:
            if self._document_matches_criteria(doc, criteria):
                doc_copy = doc.copy()
                doc_copy["match_score"] = self._calculate_match_score(doc, criteria)
                doc_copy["match_reasons"] = self._get_match_reasons(doc, criteria)
                filtered.append(doc_copy)
        
        # Ordina per punteggio
        filtered.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return filtered
    
    def _document_matches_criteria(self, doc: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Verifica se documento soddisfa tutti i criteri."""
        for criterion_type, criterion_value in criteria.items():
            if not self._matches_criterion(doc, criterion_type, criterion_value):
                return False
        return True
    
    def _matches_criterion(self, doc: Dict[str, Any], criterion_type: str, criterion_value: Any) -> bool:
        """Verifica singolo criterio."""
        if criterion_type == "date" or criterion_type.endswith("_date"):
            return self._matches_date_criterion(doc, criterion_value)
        elif criterion_type == "file_types":
            return self._matches_file_type_criterion(doc, criterion_value)
        elif criterion_type == "author":
            return self._matches_text_criterion(doc, "author", criterion_value)
        elif criterion_type in ["min_size", "max_size", "target_size"]:
            return self._matches_size_criterion(doc, criterion_type, criterion_value)
        else:
            # Criterio generico
            return self._matches_generic_criterion(doc, criterion_type, criterion_value)
    
    def _matches_date_criterion(self, doc: Dict[str, Any], date_criteria: Dict[str, Any]) -> bool:
        """Verifica criteri di data."""
        doc_date_str = self._get_document_field(doc, "created_at")
        if not doc_date_str:
            return False
        
        try:
            doc_date = datetime.fromisoformat(str(doc_date_str).replace('Z', '+00:00'))
            
            if "specific_date" in date_criteria:
                target_date = datetime.fromisoformat(date_criteria["specific_date"])
                return doc_date.date() == target_date.date()
            
            if "date_range" in date_criteria:
                start_date = datetime.fromisoformat(date_criteria["date_range"]["start"])
                end_date = datetime.fromisoformat(date_criteria["date_range"]["end"])
                return start_date <= doc_date <= end_date
            
            if "year" in date_criteria:
                return doc_date.year == date_criteria["year"]
            
        except (ValueError, TypeError):
            return False
        
        return True
    
    def _matches_file_type_criterion(self, doc: Dict[str, Any], file_types: List[str]) -> bool:
        """Verifica criteri di tipo file."""
        filename = self._get_document_field(doc, "filename")
        if filename:
            filename_lower = filename.lower()
            if any(filename_lower.endswith(ext) for ext in file_types):
                return True
        
        mime_type = self._get_document_field(doc, "mime_type")
        if mime_type:
            mime_lower = mime_type.lower()
            for ext in file_types:
                if self._mime_type_matches_extension(mime_lower, ext):
                    return True
        
        return False
    
    def _matches_text_criterion(self, doc: Dict[str, Any], field: str, value: str) -> bool:
        """Verifica criteri di testo."""
        doc_value = self._get_document_field(doc, field)
        if doc_value:
            return value.lower() in str(doc_value).lower()
        return False
    
    def _matches_size_criterion(self, doc: Dict[str, Any], criterion_type: str, value: Union[int, float]) -> bool:
        """Verifica criteri di dimensione."""
        doc_size = self._get_document_field(doc, "file_size")
        if doc_size is None:
            return False
        
        try:
            doc_size = float(doc_size)
            
            if criterion_type == "min_size":
                return doc_size >= value
            elif criterion_type == "max_size":
                return doc_size <= value
            elif criterion_type == "target_size":
                tolerance = value * 0.1
                return abs(doc_size - value) <= tolerance
            
        except (ValueError, TypeError):
            return False
        
        return True
    
    def _matches_generic_criterion(self, doc: Dict[str, Any], field: str, value: Any) -> bool:
        """Verifica criterio generico."""
        doc_value = self._get_document_field(doc, field)
        if doc_value is None:
            return False
        
        if isinstance(value, str):
            return str(value).lower() in str(doc_value).lower()
        else:
            return doc_value == value
    
    def _get_document_field(self, doc: Dict[str, Any], field: str) -> Any:
        """Ottiene campo del documento usando mapping."""
        possible_fields = self.field_mapping.get(field, [field])
        
        # Cerca nel documento principale
        for possible_field in possible_fields:
            if possible_field in doc:
                return doc[possible_field]
        
        # Cerca nei metadati
        metadata = doc.get("metadata", {})
        for possible_field in possible_fields:
            if possible_field in metadata:
                return metadata[possible_field]
        
        return None
    
    def _mime_type_matches_extension(self, mime_type: str, extension: str) -> bool:
        """Verifica se tipo MIME corrisponde all'estensione."""
        ext_lower = extension.lower()
        
        if ext_lower == ".pdf" and "pdf" in mime_type:
            return True
        if ext_lower in [".jpg", ".jpeg", ".png", ".gif"] and "image" in mime_type:
            return True
        if ext_lower in [".doc", ".docx"] and "word" in mime_type:
            return True
        if ext_lower in [".xls", ".xlsx"] and "excel" in mime_type:
            return True
        if ext_lower in [".ppt", ".pptx"] and "powerpoint" in mime_type:
            return True
        
        return False
    
    def _calculate_match_score(self, doc: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calcola punteggio di match."""
        if not criteria:
            return 0.0
        
        matched_criteria = sum(1 for c_type, c_value in criteria.items() 
                              if self._matches_criterion(doc, c_type, c_value))
        
        return matched_criteria / len(criteria)
    
    def _get_match_reasons(self, doc: Dict[str, Any], criteria: Dict[str, Any]) -> List[str]:
        """Ottiene ragioni del match."""
        reasons = []
        
        for criterion_type, criterion_value in criteria.items():
            if self._matches_criterion(doc, criterion_type, criterion_value):
                reasons.append(f"{criterion_type}: {criterion_value}")
        
        return reasons

class GenericMetadataSearchProcessor:
    """
    Processore generico per ricerche sui metadati.
    Completamente configurabile per diversi schemi di dati e fonti.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Configurazione estrattori
        self.extractors = self._initialize_extractors(config.get("extractors", {}))
        
        # Configurazione adattatore dati
        data_source_config = config.get("data_source", {"type": "vectorstore"})
        self.data_adapter = self._initialize_data_adapter(data_source_config)
        
        # Configurazione ricerca
        self.max_results = config.get("max_results", 10)
        self.enable_scoring = config.get("enable_scoring", True)
        
        # Configurazione output
        self.output_format = config.get("output_format", "detailed")  # "detailed", "simple", "raw"
        self.include_match_details = config.get("include_match_details", True)
        
        # Campo per query
        self.input_field = config.get("input_field", "query")
        
        self._log_info(f"Generic Metadata Search inizializzato per nodo {node_id}")
    
    def _initialize_extractors(self, extractors_config: Dict[str, Any]) -> Dict[str, MetadataExtractor]:
        """Inizializza estrattori di criteri."""
        extractors = {}
        
        # Estrattori standard
        if extractors_config.get("date_enabled", True):
            extractors["date"] = DateExtractor(extractors_config.get("date", {}))
        
        if extractors_config.get("file_type_enabled", True):
            extractors["file_type"] = FileTypeExtractor(extractors_config.get("file_type", {}))
        
        if extractors_config.get("size_enabled", True):
            extractors["size"] = SizeExtractor(extractors_config.get("size", {}))
        
        if extractors_config.get("author_enabled", True):
            extractors["author"] = AuthorExtractor(extractors_config.get("author", {}))
        
        # Estrattori personalizzati
        for name, extractor_config in extractors_config.get("custom", {}).items():
            extractors[name] = GenericMetadataExtractor(extractor_config)
        
        return extractors
    
    def _initialize_data_adapter(self, data_source_config: Dict[str, Any]) -> DataSourceAdapter:
        """Inizializza adattatore per fonte dati."""
        source_type = data_source_config.get("type", "vectorstore")
        
        if source_type == "vectorstore":
            return VectorstoreAdapter(data_source_config.get("config", {}))
        else:
            raise ValueError(f"Tipo di fonte dati non supportato: {source_type}")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Esegue ricerca sui metadati in modo generico.
        
        Args:
            inputs: Dizionario con parametri di ricerca
            
        Returns:
            Risultati della ricerca
        """
        try:
            # Estrai query
            query_text = self._extract_query_text(inputs)
            if not query_text:
                raise ValueError(f"Campo '{self.input_field}' richiesto ma non fornito")
            
            # Metadati del contesto
            context_data = inputs.get("context", {})
            user_id = inputs.get("user_id", context_data.get("user_id"))
            session_id = inputs.get("session_id", context_data.get("session_id"))
            
            self._log_info(f"Ricerca metadati: '{query_text[:100]}...'")
            
            # Estrai criteri dai metadati
            metadata_criteria = self._extract_all_criteria(query_text)
            
            # Parametri per fetch dati
            fetch_params = {
                "batch_size": inputs.get("batch_size", 100),
                "max_total": inputs.get("max_total", 1000)
            }
            
            # Recupera dati
            all_data = await self.data_adapter.fetch_data(fetch_params)
            
            # Filtra basandosi sui criteri
            filtered_data = self.data_adapter.filter_data(all_data, metadata_criteria)
            
            # Limita risultati
            limited_results = filtered_data[:self.max_results]
            
            # Genera output
            result = self._generate_output(query_text, limited_results, metadata_criteria, {
                "user_id": user_id,
                "session_id": session_id,
                "context": context_data,
                "total_documents": len(all_data),
                "matched_documents": len(filtered_data)
            })
            
            self._log_info(f"Ricerca completata: {len(limited_results)} risultati")
            
            return result
            
        except Exception as e:
            self._log_error(f"Errore nella ricerca metadati: {e}")
            
            return self._generate_error_output(inputs, str(e))
    
    def _extract_query_text(self, inputs: Dict[str, Any]) -> str:
        """Estrae testo della query dall'input."""
        # Prova il campo configurato
        text = inputs.get(self.input_field)
        
        if not text:
            # Fallback su campi comuni
            for field in ["query", "question", "text", "search_text"]:
                text = inputs.get(field)
                if text:
                    break
        
        return str(text) if text else ""
    
    def _extract_all_criteria(self, query: str) -> Dict[str, Any]:
        """Estrae tutti i criteri di metadati dalla query."""
        all_criteria = {}
        
        for extractor_name, extractor in self.extractors.items():
            try:
                criteria = extractor.extract_criteria(query)
                if criteria:
                    all_criteria.update(criteria)
                    self._log_debug(f"Estrattore {extractor_name}: {criteria}")
            except Exception as e:
                self._log_warning(f"Errore nell'estrattore {extractor_name}: {e}")
        
        return all_criteria
    
    def _generate_output(self, query: str, results: List[Dict[str, Any]], 
                        criteria: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Genera output nel formato configurato."""
        if self.output_format == "simple":
            return {
                "results": [{"id": r.get("id"), "match_score": r.get("match_score", 0)} for r in results],
                "total_found": len(results)
            }
        elif self.output_format == "raw":
            return {"results": results}
        else:  # detailed
            output = {
                "search_type": "metadata",
                "query": query,
                "criteria": criteria,
                "results": results,
                "total_found": len(results),
                "search_metadata": {
                    **metadata,
                    "timestamp": time.time(),
                    "node_id": self.node_id,
                    "extractors_used": list(self.extractors.keys())
                }
            }
            
            if not self.include_match_details:
                # Rimuovi dettagli di match dai risultati
                for result in output["results"]:
                    result.pop("match_reasons", None)
                    result.pop("match_score", None)
            
            return output
    
    def _generate_error_output(self, inputs: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Genera output di errore."""
        return {
            "search_type": "metadata",
            "query": self._extract_query_text(inputs),
            "results": [],
            "total_found": 0,
            "error": error,
            "search_metadata": {
                "error": True,
                "timestamp": time.time(),
                "node_id": self.node_id
            }
        }
    
    def _log_info(self, message: str) -> None:
        """Registra un messaggio informativo."""
        try:
            log_info(f"[GenericMetadataSearch] {message}")
        except Exception:
            pass
    
    def _log_debug(self, message: str) -> None:
        """Registra un messaggio di debug."""
        try:
            log_debug(f"[GenericMetadataSearch] {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """Registra un messaggio di avviso."""
        try:
            log_warning(f"[GenericMetadataSearch] {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """Registra un messaggio di errore."""
        try:
            log_error(f"[GenericMetadataSearch] {message}")
        except Exception:
            pass