import json
import aiohttp
import time
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

class SemanticSearchProcessor:
    """
    Processore per ricerche semantiche utilizzando il VectorstoreService.
    Interfaccia con il servizio per trovare documenti semanticamente simili alla query.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Configurazione del VectorstoreService
        self.vectorstore_base_url = config.get("vectorstore_base_url", "http://localhost:8090")
        self.default_collection = config.get("default_collection", "documents")
        self.max_results = config.get("max_results", 5)
        self.min_similarity_score = config.get("min_similarity_score", 0.1)
        self.timeout = config.get("timeout", 30)
        
        # Configurazione ricerca
        self.enable_fallback_search = config.get("enable_fallback_search", True)
        self.include_metadata = config.get("include_metadata", True)
        self.sort_by_relevance = config.get("sort_by_relevance", True)
        
        self._log_info(f"Semantic Search Processor inizializzato per nodo {node_id}")
        self._log_info(f"VectorstoreService URL: {self.vectorstore_base_url}")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Esegue una ricerca semantica utilizzando il VectorstoreService.
        
        Args:
            inputs: Dizionario con la query e parametri di ricerca
            
        Returns:
            Dizionario con i risultati della ricerca semantica
        """
        try:
            # Estrai parametri dall'input
            question = inputs.get("question", inputs.get("query", ""))
            if not question:
                raise ValueError("Campo 'question' o 'query' richiesto ma non fornito")
            
            collection = inputs.get("collection", self.default_collection)
            max_results = inputs.get("max_results", inputs.get("limit", self.max_results))
            min_score = inputs.get("min_similarity_score", self.min_similarity_score)
            
            # Metadati della ricerca
            user_id = inputs.get("user_id")
            session_id = inputs.get("session_id")
            
            self._log_info(f"Ricerca semantica per: '{question[:100]}...' in collezione '{collection}'")
            
            # Esegui la ricerca semantica
            search_results = await self._perform_semantic_search(
                question, collection, max_results, min_score
            )
            
            # Elabora e filtra i risultati
            processed_results = self._process_search_results(search_results, question)
            
            # Prepara l'output
            result = {
                "search_type": "semantic",
                "query": question,
                "collection": collection,
                "results": processed_results,
                "total_found": len(processed_results),
                "search_metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "vectorstore_url": self.vectorstore_base_url,
                    "max_results_requested": max_results,
                    "min_similarity_threshold": min_score
                }
            }
            
            self._log_info(f"Ricerca completata: {len(processed_results)} risultati trovati")
            
            return result
            
        except Exception as e:
            self._log_error(f"Errore nella ricerca semantica: {e}")
            
            # Fallback se la ricerca principale fallisce
            if self.enable_fallback_search:
                fallback_results = await self._fallback_search(inputs)
                return fallback_results
            
            return {
                "search_type": "semantic",
                "query": inputs.get("question", ""),
                "results": [],
                "total_found": 0,
                "error": str(e),
                "search_metadata": {
                    "error": True,
                    "timestamp": time.time()
                }
            }
    
    async def _perform_semantic_search(self, 
                                     question: str, 
                                     collection: str, 
                                     max_results: int,
                                     min_score: float) -> Dict[str, Any]:
        """
        Esegue la ricerca semantica tramite API del VectorstoreService.
        
        Args:
            question: Domanda per la ricerca
            collection: Nome della collezione
            max_results: Numero massimo di risultati
            min_score: Punteggio minimo di similarità
            
        Returns:
            Risultati della ricerca dal VectorstoreService
        """
        # Prepara l'URL per la ricerca
        search_url = f"{self.vectorstore_base_url}/documents/{collection}/query"
        
        # Payload per la richiesta
        payload = {
            "query_text": question,
            "limit": max_results
        }
        
        # Headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Esegui la richiesta HTTP
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            self._log_debug(f"POST {search_url} con payload: {payload}")
            
            async with session.post(search_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self._log_debug(f"Risposta VectorstoreService: {len(data.get('matches', []))} matches")
                    return data
                else:
                    error_text = await response.text()
                    raise Exception(f"VectorstoreService error {response.status}: {error_text}")
    
    def _process_search_results(self, search_data: Dict[str, Any], original_query: str) -> List[Dict[str, Any]]:
        """
        Elabora i risultati della ricerca dal VectorstoreService.
        
        Args:
            search_data: Dati dalla risposta del VectorstoreService
            original_query: Query originale per il contesto
            
        Returns:
            Lista di risultati elaborati e filtrati
        """
        matches = search_data.get("matches", [])
        processed = []
        
        for match in matches:
            # Estrai i dati del match
            similarity_score = match.get("similarity_score", 0.0)
            
            # Filtra per punteggio minimo
            if similarity_score < self.min_similarity_score:
                continue
            
            # Prepara il risultato elaborato
            processed_match = {
                "id": match.get("id"),
                "document": match.get("document", ""),
                "similarity_score": similarity_score,
                "metadata": match.get("metadata", {}) if self.include_metadata else {},
                "search_context": {
                    "query": original_query,
                    "match_type": "semantic",
                    "relevance_tier": self._classify_relevance(similarity_score)
                }
            }
            
            # Aggiungi informazioni aggiuntive se disponibili
            if "collection" in match:
                processed_match["collection"] = match["collection"]
            
            # Calcola snippet di testo rilevante se il documento è lungo
            document_text = processed_match["document"]
            if len(document_text) > 500:
                snippet = self._extract_relevant_snippet(document_text, original_query)
                processed_match["snippet"] = snippet
            
            processed.append(processed_match)
        
        # Ordina per rilevanza se richiesto
        if self.sort_by_relevance:
            processed.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return processed
    
    def _classify_relevance(self, similarity_score: float) -> str:
        """
        Classifica la rilevanza basata sul punteggio di similarità.
        
        Args:
            similarity_score: Punteggio di similarità (0.0 - 1.0)
            
        Returns:
            Classificazione di rilevanza
        """
        if similarity_score >= 0.8:
            return "high"
        elif similarity_score >= 0.6:
            return "medium"
        elif similarity_score >= 0.4:
            return "low"
        else:
            return "minimal"
    
    def _extract_relevant_snippet(self, document_text: str, query: str, snippet_length: int = 300) -> str:
        """
        Estrae uno snippet rilevante dal documento basato sulla query.
        
        Args:
            document_text: Testo completo del documento
            query: Query di ricerca
            snippet_length: Lunghezza desiderata dello snippet
            
        Returns:
            Snippet di testo rilevante
        """
        # Semplice implementazione: trova la prima occorrenza di una parola chiave della query
        query_words = [word.lower().strip() for word in query.split() if len(word) > 3]
        document_lower = document_text.lower()
        
        best_position = 0
        for word in query_words:
            pos = document_lower.find(word)
            if pos != -1:
                # Trova l'inizio della frase che contiene la parola
                start = max(0, pos - snippet_length // 2)
                best_position = start
                break
        
        # Estrai lo snippet
        end_position = min(len(document_text), best_position + snippet_length)
        snippet = document_text[best_position:end_position]
        
        # Pulisci l'inizio e la fine dello snippet
        if best_position > 0:
            snippet = "..." + snippet
        if end_position < len(document_text):
            snippet = snippet + "..."
        
        return snippet
    
    async def _fallback_search(self, original_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ricerca di fallback quando la ricerca principale fallisce.
        
        Args:
            original_inputs: Input originali della ricerca
            
        Returns:
            Risultati di fallback
        """
        self._log_warning("Utilizzo ricerca di fallback")
        
        try:
            # Prova con una ricerca più semplice o con parametri diversi
            question = original_inputs.get("question", original_inputs.get("query", ""))
            
            # Prova ricerca con l'endpoint alternativo
            search_url = f"{self.vectorstore_base_url}/search"
            
            payload = {
                "query": question,
                "limit": 3  # Meno risultati per il fallback
            }
            
            timeout = aiohttp.ClientTimeout(total=10)  # Timeout più breve per fallback
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(search_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "search_type": "semantic_fallback",
                            "query": question,
                            "results": data.get("results", []),
                            "total_found": len(data.get("results", [])),
                            "search_metadata": {
                                "fallback": True,
                                "timestamp": time.time()
                            }
                        }
        except Exception as e:
            self._log_error(f"Anche la ricerca di fallback è fallita: {e}")
        
        # Ultimo fallback: risultato vuoto
        return {
            "search_type": "semantic_failed",
            "query": original_inputs.get("question", ""),
            "results": [],
            "total_found": 0,
            "error": "Tutte le ricerche semantiche sono fallite",
            "search_metadata": {
                "fallback_failed": True,
                "timestamp": time.time()
            }
        }
    
    def _log_info(self, message: str) -> None:
        """Registra un messaggio informativo."""
        try:
            log_info(f"[SemanticSearch] {message}")
        except Exception:
            pass
    
    def _log_debug(self, message: str) -> None:
        """Registra un messaggio di debug."""
        try:
            log_debug(f"[SemanticSearch] {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """Registra un messaggio di avviso."""
        try:
            log_warning(f"[SemanticSearch] {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """Registra un messaggio di errore."""
        try:
            log_error(f"[SemanticSearch] {message}")
        except Exception:
            pass