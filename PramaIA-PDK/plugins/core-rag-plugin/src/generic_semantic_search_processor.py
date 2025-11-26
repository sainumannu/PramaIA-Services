import json
import aiohttp
import time
from typing import Dict, Any, List, Optional, Union
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

class SearchConnector(ABC):
    """Interfaccia astratta per connettori di ricerca."""
    
    @abstractmethod
    async def search(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue una ricerca."""
        pass
    
    @abstractmethod
    def format_response(self, raw_response: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Formatta la risposta del backend."""
        pass

class VectorstoreConnector(SearchConnector):
    """Connettore per VectorstoreService PramaIA."""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "http://localhost:8090")
        self.timeout = config.get("timeout", 30)
        self.default_collection = config.get("default_collection", "documents")
    
    async def search(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue ricerca su VectorstoreService."""
        collection = params.get("collection", self.default_collection)
        search_url = f"{self.base_url}/documents/{collection}/query"
        
        payload = {
            "query_text": query,
            "limit": params.get("limit", 5)
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(search_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"VectorstoreService error {response.status}: {error_text}")
    
    def format_response(self, raw_response: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Formatta risposta VectorstoreService."""
        matches = raw_response.get("matches", [])
        results = []
        
        for match in matches:
            result = {
                "id": match.get("id"),
                "content": match.get("document", ""),
                "score": match.get("similarity_score", 0.0),
                "metadata": match.get("metadata", {}),
                "source_type": "vectorstore",
                "raw_data": match
            }
            results.append(result)
        
        return results

class ElasticsearchConnector(SearchConnector):
    """Connettore per Elasticsearch."""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "http://localhost:9200")
        self.index = config.get("index", "documents")
        self.timeout = config.get("timeout", 30)
    
    async def search(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue ricerca su Elasticsearch."""
        search_url = f"{self.base_url}/{self.index}/_search"
        
        payload = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": params.get("fields", ["content", "title", "description"])
                }
            },
            "size": params.get("limit", 5)
        }
        
        headers = {"Content-Type": "application/json"}
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(search_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Elasticsearch error {response.status}: {error_text}")
    
    def format_response(self, raw_response: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Formatta risposta Elasticsearch."""
        hits = raw_response.get("hits", {}).get("hits", [])
        results = []
        
        for hit in hits:
            source = hit.get("_source", {})
            result = {
                "id": hit.get("_id"),
                "content": source.get("content", ""),
                "score": hit.get("_score", 0.0),
                "metadata": {k: v for k, v in source.items() if k != "content"},
                "source_type": "elasticsearch",
                "raw_data": hit
            }
            results.append(result)
        
        return results

class GenericHTTPConnector(SearchConnector):
    """Connettore HTTP generico configurabile."""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url")
        self.endpoint = config.get("endpoint", "/search")
        self.method = config.get("method", "POST").upper()
        self.timeout = config.get("timeout", 30)
        self.headers = config.get("headers", {})
        self.payload_template = config.get("payload_template", {"query": "{query}"})
        self.response_mapping = config.get("response_mapping", {
            "results_field": "results",
            "id_field": "id",
            "content_field": "content",
            "score_field": "score"
        })
    
    async def search(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue ricerca su endpoint HTTP generico."""
        search_url = f"{self.base_url}{self.endpoint}"
        
        # Costruisci payload da template
        payload = self._build_payload(query, params)
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if self.method == "GET":
                async with session.get(search_url, params=payload, headers=self.headers) as response:
                    return await self._handle_response(response)
            else:  # POST
                async with session.post(search_url, json=payload, headers=self.headers) as response:
                    return await self._handle_response(response)
    
    def _build_payload(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Costruisce payload da template."""
        payload = {}
        for key, value in self.payload_template.items():
            if isinstance(value, str) and "{query}" in value:
                payload[key] = value.format(query=query)
            elif isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                param_name = value[1:-1]
                payload[key] = params.get(param_name, value)
            else:
                payload[key] = value
        
        # Aggiungi parametri extra
        for key, value in params.items():
            if key not in payload:
                payload[key] = value
        
        return payload
    
    async def _handle_response(self, response):
        """Gestisce risposta HTTP."""
        if response.status == 200:
            return await response.json()
        else:
            error_text = await response.text()
            raise Exception(f"HTTP error {response.status}: {error_text}")
    
    def format_response(self, raw_response: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Formatta risposta usando mapping configurabile."""
        mapping = self.response_mapping
        results_field = mapping.get("results_field", "results")
        
        # Naviga nella struttura per trovare i risultati
        raw_results = raw_response
        for field in results_field.split("."):
            raw_results = raw_results.get(field, [])
        
        if not isinstance(raw_results, list):
            raw_results = [raw_results] if raw_results else []
        
        results = []
        for item in raw_results:
            result = {
                "id": self._extract_field(item, mapping.get("id_field", "id")),
                "content": self._extract_field(item, mapping.get("content_field", "content")),
                "score": self._extract_field(item, mapping.get("score_field", "score"), 0.0),
                "metadata": self._extract_metadata(item, mapping),
                "source_type": "http_generic",
                "raw_data": item
            }
            results.append(result)
        
        return results
    
    def _extract_field(self, item: Dict[str, Any], field_path: str, default=None):
        """Estrae campo usando dot notation."""
        value = item
        for field in field_path.split("."):
            if isinstance(value, dict):
                value = value.get(field, default)
            else:
                return default
        return value if value is not None else default
    
    def _extract_metadata(self, item: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Estrae metadati escludendo campi principali."""
        excluded_fields = {
            mapping.get("id_field", "id"),
            mapping.get("content_field", "content"), 
            mapping.get("score_field", "score")
        }
        
        metadata = {}
        for key, value in item.items():
            if key not in excluded_fields:
                metadata[key] = value
        
        return metadata

class GenericSemanticSearchProcessor:
    """
    Processore generico per ricerche semantiche su diversi backend.
    Supporta VectorstoreService, Elasticsearch, e connettori HTTP generici.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Configurazione backend
        self.backend_type = config.get("backend_type", "vectorstore")
        self.backend_config = config.get("backend_config", {})
        
        # Configurazione ricerca
        self.default_params = config.get("default_search_params", {
            "limit": 5,
            "collection": "documents"
        })
        
        # Configurazione filtri
        self.min_score = config.get("min_score", 0.1)
        self.max_results = config.get("max_results", 10)
        
        # Configurazione output
        self.output_format = config.get("output_format", "detailed")  # "detailed", "simple", "raw"
        self.include_metadata = config.get("include_metadata", True)
        self.include_snippets = config.get("include_snippets", True)
        self.snippet_length = config.get("snippet_length", 300)
        
        # Configurazione fallback
        self.enable_fallback = config.get("enable_fallback", True)
        self.fallback_backends = config.get("fallback_backends", [])
        
        # Inizializza connettore principale
        self.connector = self._create_connector(self.backend_type, self.backend_config)
        
        # Inizializza connettori di fallback
        self.fallback_connectors = []
        for fb_config in self.fallback_backends:
            fb_type = fb_config.get("type")
            fb_connector = self._create_connector(fb_type, fb_config.get("config", {}))
            if fb_connector:
                self.fallback_connectors.append(fb_connector)
        
        self._log_info(f"Generic Semantic Search inizializzato per nodo {node_id}")
        self._log_info(f"Backend principale: {self.backend_type}")
    
    def _create_connector(self, backend_type: str, backend_config: Dict[str, Any]) -> Optional[SearchConnector]:
        """Crea connettore per il backend specificato."""
        try:
            if backend_type == "vectorstore":
                return VectorstoreConnector(backend_config)
            elif backend_type == "elasticsearch":
                return ElasticsearchConnector(backend_config)
            elif backend_type == "http" or backend_type == "generic":
                return GenericHTTPConnector(backend_config)
            else:
                self._log_warning(f"Tipo di backend sconosciuto: {backend_type}")
                return None
        except Exception as e:
            self._log_error(f"Errore creazione connettore {backend_type}: {e}")
            return None
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Esegue ricerca semantica generica su backend configurato.
        
        Args:
            inputs: Dizionario con parametri di ricerca
            
        Returns:
            Risultati della ricerca
        """
        try:
            # Estrai parametri di ricerca
            query_text = self._extract_query_text(inputs)
            if not query_text:
                raise ValueError("Query di ricerca richiesta ma non fornita")
            
            search_params = self._build_search_params(inputs)
            
            # Metadati del contesto
            context_data = inputs.get("context", {})
            user_id = inputs.get("user_id", context_data.get("user_id"))
            session_id = inputs.get("session_id", context_data.get("session_id"))
            
            self._log_info(f"Ricerca semantica: '{query_text[:100]}...'")
            
            # Esegui ricerca su backend principale
            search_results = await self._perform_search(query_text, search_params)
            
            # Applica filtri e elaborazioni
            filtered_results = self._filter_and_process_results(search_results, query_text)
            
            # Genera output nel formato richiesto
            result = self._generate_output(query_text, filtered_results, search_params, {
                "user_id": user_id,
                "session_id": session_id,
                "context": context_data
            })
            
            self._log_info(f"Ricerca completata: {len(filtered_results)} risultati")
            
            return result
            
        except Exception as e:
            self._log_error(f"Errore nella ricerca semantica: {e}")
            
            # Prova fallback se abilitato
            if self.enable_fallback and self.fallback_connectors:
                fallback_result = await self._try_fallback_search(inputs, str(e))
                if fallback_result:
                    return fallback_result
            
            # Output di errore
            return self._generate_error_output(inputs, str(e))
    
    def _extract_query_text(self, inputs: Dict[str, Any]) -> str:
        """
        Estrae il testo della query dall'input.
        
        Args:
            inputs: Input del nodo
            
        Returns:
            Testo della query
        """
        # Prova campi comuni per la query
        for field in ["query", "question", "text", "search_text", "q"]:
            value = inputs.get(field)
            if value:
                return str(value)
        
        return ""
    
    def _build_search_params(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Costruisce parametri di ricerca combinando defaults e input.
        
        Args:
            inputs: Input del nodo
            
        Returns:
            Parametri di ricerca completi
        """
        params = self.default_params.copy()
        
        # Override con parametri dall'input
        search_params = inputs.get("search_params", {})
        params.update(search_params)
        
        # Parametri specifici con nomi alternativi
        if "limit" not in params:
            params["limit"] = inputs.get("max_results", inputs.get("limit", self.default_params.get("limit", 5)))
        
        if "collection" not in params:
            params["collection"] = inputs.get("collection", inputs.get("index", self.default_params.get("collection", "documents")))
        
        return params
    
    async def _perform_search(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Esegue la ricerca usando il connettore principale.
        
        Args:
            query: Testo della query
            params: Parametri di ricerca
            
        Returns:
            Risultati della ricerca
        """
        if not self.connector:
            raise Exception("Nessun connettore disponibile per la ricerca")
        
        # Esegui ricerca raw
        raw_response = await self.connector.search(query, params)
        
        # Formatta risultati
        formatted_results = self.connector.format_response(raw_response, query)
        
        return formatted_results
    
    def _filter_and_process_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Filtra e elabora i risultati della ricerca.
        
        Args:
            results: Risultati grezzi
            query: Query originale
            
        Returns:
            Risultati filtrati ed elaborati
        """
        processed_results = []
        
        for result in results:
            # Filtra per punteggio minimo
            score = result.get("score", 0.0)
            if score < self.min_score:
                continue
            
            # Elabora il risultato
            processed_result = result.copy()
            
            # Aggiungi classificazione rilevanza
            processed_result["relevance_tier"] = self._classify_relevance(score)
            
            # Genera snippet se richiesto e necessario
            if self.include_snippets:
                content = processed_result.get("content", "")
                if content and len(content) > self.snippet_length:
                    snippet = self._extract_snippet(content, query)
                    processed_result["snippet"] = snippet
            
            # Rimuovi metadati se non richiesti
            if not self.include_metadata:
                processed_result.pop("metadata", None)
            
            # Aggiungi context di ricerca
            processed_result["search_context"] = {
                "query": query,
                "backend": self.backend_type,
                "timestamp": time.time()
            }
            
            processed_results.append(processed_result)
            
            # Limita risultati se necessario
            if len(processed_results) >= self.max_results:
                break
        
        # Ordina per punteggio (già fatto dal backend di solito, ma per sicurezza)
        processed_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return processed_results
    
    def _classify_relevance(self, score: float) -> str:
        """
        Classifica la rilevanza basata sul punteggio.
        
        Args:
            score: Punteggio di similarità
            
        Returns:
            Classificazione di rilevanza
        """
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "minimal"
    
    def _extract_snippet(self, content: str, query: str) -> str:
        """
        Estrae snippet rilevante dal contenuto.
        
        Args:
            content: Contenuto completo
            query: Query di ricerca
            
        Returns:
            Snippet rilevante
        """
        # Trova migliore posizione per snippet
        query_words = [word.lower().strip() for word in query.split() if len(word) > 2]
        content_lower = content.lower()
        
        best_pos = 0
        max_matches = 0
        
        # Cerca la posizione con più match di parole della query
        for i in range(0, len(content), 50):
            window = content_lower[i:i+self.snippet_length]
            matches = sum(1 for word in query_words if word in window)
            if matches > max_matches:
                max_matches = matches
                best_pos = i
        
        # Estrai snippet
        end_pos = min(len(content), best_pos + self.snippet_length)
        snippet = content[best_pos:end_pos]
        
        # Aggiungi ellipsis se necessario
        if best_pos > 0:
            snippet = "..." + snippet
        if end_pos < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    async def _try_fallback_search(self, inputs: Dict[str, Any], original_error: str) -> Optional[Dict[str, Any]]:
        """
        Prova ricerca su backend di fallback.
        
        Args:
            inputs: Input originali
            original_error: Errore del backend principale
            
        Returns:
            Risultati di fallback o None
        """
        query_text = self._extract_query_text(inputs)
        search_params = self._build_search_params(inputs)
        
        for i, connector in enumerate(self.fallback_connectors):
            try:
                self._log_warning(f"Provo fallback {i+1}/{len(self.fallback_connectors)}")
                
                raw_response = await connector.search(query_text, search_params)
                formatted_results = connector.format_response(raw_response, query_text)
                filtered_results = self._filter_and_process_results(formatted_results, query_text)
                
                # Successo del fallback
                result = self._generate_output(query_text, filtered_results, search_params, {
                    "fallback": True,
                    "fallback_index": i,
                    "original_error": original_error
                })
                
                self._log_info(f"Fallback {i+1} riuscito: {len(filtered_results)} risultati")
                return result
                
            except Exception as fb_error:
                self._log_warning(f"Fallback {i+1} fallito: {fb_error}")
                continue
        
        return None
    
    def _generate_output(self, query: str, results: List[Dict[str, Any]], 
                        search_params: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera output nel formato configurato.
        
        Args:
            query: Query originale
            results: Risultati elaborati
            search_params: Parametri di ricerca utilizzati
            metadata: Metadati del contesto
            
        Returns:
            Output formattato
        """
        if self.output_format == "simple":
            return {
                "results": [{"id": r.get("id"), "content": r.get("content"), "score": r.get("score")} for r in results],
                "total_found": len(results)
            }
        elif self.output_format == "raw":
            return {"results": results}
        else:  # detailed
            return {
                "search_type": "semantic",
                "backend": self.backend_type,
                "query": query,
                "results": results,
                "total_found": len(results),
                "search_params": search_params,
                "search_metadata": {
                    **metadata,
                    "timestamp": time.time(),
                    "min_score_threshold": self.min_score,
                    "max_results_limit": self.max_results,
                    "node_id": self.node_id
                }
            }
    
    def _generate_error_output(self, inputs: Dict[str, Any], error: str) -> Dict[str, Any]:
        """
        Genera output di errore.
        
        Args:
            inputs: Input originali
            error: Descrizione errore
            
        Returns:
            Output di errore
        """
        return {
            "search_type": "semantic",
            "backend": self.backend_type,
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
            log_info(f"[GenericSemanticSearch] {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """Registra un messaggio di avviso."""
        try:
            log_warning(f"[GenericSemanticSearch] {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """Registra un messaggio di errore."""
        try:
            log_error(f"[GenericSemanticSearch] {message}")
        except Exception:
            pass