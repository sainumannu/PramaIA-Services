import json
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

class ResponseAggregatorProcessor:
    """
    Processore generico per aggregare risultati da fonti multiple.
    Può combinare e deduplicare risultati di qualsiasi tipo con scoring configurabile.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Configurazione aggregazione generica
        self.max_total_results = config.get("max_total_results", 10)
        self.aggregation_strategy = config.get("aggregation_strategy", "weighted_merge")
        self.weights = config.get("source_weights", {"primary": 0.7, "secondary": 0.3})
        
        # Configurazione deduplicazione
        self.enable_deduplication = config.get("enable_deduplication", True)
        self.dedup_field = config.get("deduplication_field", "id")
        self.similarity_threshold = config.get("similarity_threshold", 0.8)
        
        # Configurazione output
        self.output_format = config.get("output_format", "structured")  # "structured", "formatted_text", "raw"
        self.include_metadata = config.get("include_metadata", True)
        self.include_sources = config.get("include_sources", True)
        
        # Template configurabili per formattazione
        self.format_templates = config.get("format_templates", {
            "item_template": "{index}. {title}\n   {content}",
            "summary_template": "Found {count} results from {sources} sources",
            "no_results_template": "No results found",
            "error_template": "Error occurred: {error}"
        })
        
        # Configurazione scoring
        self.scoring_method = config.get("scoring_method", "weighted_average")
        self.score_normalization = config.get("score_normalization", True)
        
        self._log_info(f"Generic Response Aggregator inizializzato per nodo {node_id}")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggrega risultati da fonti multiple in modo generico.
        
        Args:
            inputs: Dizionario con risultati da aggregare
            
        Returns:
            Dizionario con risultati aggregati
        """
        try:
            # Estrai input in modo generico
            results_sources = self._extract_result_sources(inputs)
            context_data = inputs.get("context", {})
            
            # Metadati della richiesta
            request_id = inputs.get("request_id", context_data.get("id", "unknown"))
            user_id = inputs.get("user_id", context_data.get("user_id"))
            
            self._log_info(f"Aggregazione risultati per request: {request_id}")
            self._log_debug(f"Fonti trovate: {list(results_sources.keys())}")
            
            # Estrai e normalizza i risultati
            all_results = self._extract_and_normalize_results(results_sources)
            
            # Deduplica se abilitato
            if self.enable_deduplication:
                all_results = self._deduplicate_results(all_results)
            
            # Calcola punteggi combinati
            scored_results = self._calculate_combined_scores(all_results, results_sources)
            
            # Limita i risultati
            final_results = scored_results[:self.max_total_results]
            
            # Genera output nel formato richiesto
            output = self._generate_output(final_results, results_sources, context_data)
            
            # Aggiungi metadati
            output["aggregation_metadata"] = {
                "request_id": request_id,
                "user_id": user_id,
                "timestamp": time.time(),
                "sources_count": len(results_sources),
                "total_results": len(all_results),
                "final_count": len(final_results),
                "deduplication_applied": self.enable_deduplication,
                "aggregation_strategy": self.aggregation_strategy
            }
            
            self._log_info(f"Aggregazione completata: {len(final_results)} risultati finali")
            
            return output
            
        except Exception as e:
            self._log_error(f"Errore nell'aggregazione: {e}")
            
            # Output di fallback generico
            return {
                "results": [],
                "total_count": 0,
                "error": str(e),
                "aggregation_metadata": {
                    "error": True,
                    "timestamp": time.time()
                }
            }
    
    def _extract_result_sources(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estrae le fonti di risultati dall'input in modo generico.
        
        Args:
            inputs: Input del nodo
            
        Returns:
            Dizionario con le fonti di risultati
        """
        sources = {}
        
        # Cerca campi che contengono risultati
        for key, value in inputs.items():
            # Salta metadati e campi di controllo
            if key in ["context", "user_id", "session_id", "request_id", "timestamp"]:
                continue
                
            # Identifica risultati per pattern del nome
            if (key.endswith("_results") or key.endswith("_data") or 
                key == "results" or key == "data" or key == "items"):
                
                if isinstance(value, dict) and "results" in value:
                    sources[key] = value
                elif isinstance(value, list):
                    sources[key] = {"results": value, "source_type": key}
                elif isinstance(value, dict) and any(k in value for k in ["items", "matches", "documents"]):
                    sources[key] = value
        
        # Se non trova nulla, prova con tutti i dict/list non-meta
        if not sources:
            for key, value in inputs.items():
                if key not in ["context", "user_id", "session_id", "request_id", "timestamp"]:
                    if isinstance(value, (dict, list)):
                        sources[key] = {"results": value, "source_type": "auto_detected"}
        
        return sources
    
    def _extract_and_normalize_results(self, sources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Estrae e normalizza risultati da tutte le fonti.
        
        Args:
            sources: Dizionario con le fonti di risultati
            
        Returns:
            Lista di risultati normalizzati
        """
        all_results = []
        
        for source_name, source_data in sources.items():
            try:
                # Estrai la lista di risultati dalla fonte
                if isinstance(source_data, dict):
                    results_list = (source_data.get("results") or 
                                  source_data.get("items") or 
                                  source_data.get("matches") or 
                                  source_data.get("documents") or
                                  [])
                else:
                    results_list = source_data if isinstance(source_data, list) else []
                
                # Normalizza ogni risultato
                for i, result in enumerate(results_list):
                    normalized = self._normalize_result_item(result, source_name, i)
                    if normalized:
                        all_results.append(normalized)
                        
            except Exception as e:
                self._log_warning(f"Errore nell'estrazione da fonte {source_name}: {e}")
        
        return all_results
    
    def _normalize_result_item(self, result: Any, source_name: str, index: int) -> Optional[Dict[str, Any]]:
        """
        Normalizza un singolo item di risultato in formato standard.
        
        Args:
            result: Item da normalizzare
            source_name: Nome della fonte
            index: Indice nell'array di risultati
            
        Returns:
            Item normalizzato o None se non valido
        """
        if not result:
            return None
            
        # Se è già un dict, usa come base
        if isinstance(result, dict):
            normalized = result.copy()
        else:
            # Converte altri tipi in dict
            normalized = {
                "content": str(result),
                "raw_data": result
            }
        
        # Aggiungi metadati standard
        normalized.update({
            "source": source_name,
            "source_index": index,
            "aggregator_id": self.node_id
        })
        
        # Standardizza campi comuni
        self._standardize_common_fields(normalized)
        
        return normalized
    
    def _standardize_common_fields(self, item: Dict[str, Any]) -> None:
        """
        Standardizza campi comuni in formato consistente.
        
        Args:
            item: Item da standardizzare (modificato in-place)
        """
        # Standardizza ID
        if "id" not in item:
            item["id"] = (item.get("document_id") or 
                         item.get("item_id") or 
                         f"{item['source']}_{item['source_index']}")
        
        # Standardizza content/text
        if "content" not in item:
            item["content"] = (item.get("text") or 
                             item.get("document") or 
                             item.get("description") or 
                             str(item.get("title", "")))
        
        # Standardizza score
        if "score" not in item:
            item["score"] = (item.get("similarity_score") or 
                           item.get("match_score") or 
                           item.get("confidence") or 
                           item.get("weight") or 0.0)
        
        # Standardizza metadata
        if "metadata" not in item:
            item["metadata"] = {}
        
        # Sposta campi extra in metadata
        extra_fields = ["title", "snippet", "url", "filename", "created_at", "author"]
        for field in extra_fields:
            if field in item and field not in ["content", "score", "id", "source"]:
                item["metadata"][field] = item[field]
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rimuove duplicati basandosi sul campo di deduplicazione.
        
        Args:
            results: Lista di risultati
            
        Returns:
            Lista deduplicata
        """
        if not self.enable_deduplication or not results:
            return results
        
        seen = {}
        deduplicated = []
        
        for result in results:
            # Usa il campo configurato per deduplicazione
            dedup_value = result.get(self.dedup_field)
            
            if dedup_value and dedup_value in seen:
                # Merge con il risultato esistente
                existing = seen[dedup_value]
                merged = self._merge_duplicate_results(existing, result)
                # Sostituisce nella lista
                for i, item in enumerate(deduplicated):
                    if item.get(self.dedup_field) == dedup_value:
                        deduplicated[i] = merged
                        break
            else:
                seen[dedup_value] = result
                deduplicated.append(result)
        
        return deduplicated
    
    def _merge_duplicate_results(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge due risultati duplicati.
        
        Args:
            existing: Risultato esistente
            new: Nuovo risultato
            
        Returns:
            Risultato merged
        """
        merged = existing.copy()
        
        # Combina score (prende il massimo)
        merged["score"] = max(existing.get("score", 0), new.get("score", 0))
        
        # Combina sources
        existing_sources = existing.get("sources", [existing.get("source")])
        new_sources = new.get("sources", [new.get("source")])
        if isinstance(existing_sources, str):
            existing_sources = [existing_sources]
        if isinstance(new_sources, str):
            new_sources = [new_sources]
        
        merged["sources"] = list(set(existing_sources + new_sources))
        
        # Merge metadata
        if "metadata" in new:
            if "metadata" not in merged:
                merged["metadata"] = {}
            merged["metadata"].update(new["metadata"])
        
        # Prende il contenuto più lungo se diverso
        if len(new.get("content", "")) > len(merged.get("content", "")):
            merged["content"] = new["content"]
        
        return merged
        """
        Estrae e normalizza documenti dai risultati di ricerca.
        
        Args:
            search_results: Risultati della ricerca (semantica o metadati)
            search_type: Tipo di ricerca ("semantic" o "metadata")
            
        Returns:
            Lista di documenti normalizzati
        """
        if not search_results or "results" not in search_results:
            return []
        
        results = search_results["results"]
        if not isinstance(results, list):
            return []
        
        normalized_docs = []
        
        for doc in results:
            normalized_doc = {
                "id": doc.get("id", ""),
                "content": doc.get("document", doc.get("content", "")),
                "search_type": search_type,
                "original_data": doc.copy()
            }
            
            # Aggiungi punteggi specifici per tipo
            if search_type == "semantic":
                normalized_doc["semantic_score"] = doc.get("similarity_score", 0.0)
                normalized_doc["metadata_score"] = 0.0
            else:  # metadata
                normalized_doc["semantic_score"] = 0.0
                normalized_doc["metadata_score"] = doc.get("match_score", 1.0)
            
            # Aggiungi metadati
            normalized_doc["metadata"] = doc.get("metadata", {})
            
            # Aggiungi snippet se disponibile
            if self.include_snippets:
                normalized_doc["snippet"] = doc.get("snippet", "")
            
            # Aggiungi informazioni sulla corrispondenza
            if "match_criteria" in doc:
                normalized_doc["match_reasons"] = doc["match_criteria"]
            
            if "search_context" in doc:
                normalized_doc["context"] = doc["search_context"]
            
            normalized_docs.append(normalized_doc)
        
        return normalized_docs
    
    def _combine_and_deduplicate(self, 
                                semantic_docs: List[Dict[str, Any]], 
                                metadata_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combina i risultati e rimuove duplicati.
        
        Args:
            semantic_docs: Documenti dalla ricerca semantica
            metadata_docs: Documenti dalla ricerca sui metadati
            
        Returns:
            Lista di documenti combinati e deduplicati
        """
        if not self.enable_deduplication:
            return semantic_docs + metadata_docs
        
        # Mappa per tracciare documenti per ID
        docs_by_id = {}
        
        # Aggiungi documenti semantici
        for doc in semantic_docs:
            doc_id = doc["id"]
            docs_by_id[doc_id] = doc
        
        # Aggiungi documenti metadati, combinando se già presenti
        for doc in metadata_docs:
            doc_id = doc["id"]
            
            if doc_id in docs_by_id:
                # Combina i punteggi
                existing_doc = docs_by_id[doc_id]
                existing_doc["metadata_score"] = max(
                    existing_doc["metadata_score"], 
                    doc["metadata_score"]
                )
                existing_doc["search_type"] = "both"
                
                # Combina metadati aggiuntivi
                if "match_reasons" in doc:
                    existing_reasons = existing_doc.get("match_reasons", [])
                    existing_doc["match_reasons"] = existing_reasons + doc["match_reasons"]
                
            else:
                docs_by_id[doc_id] = doc
        
        return list(docs_by_id.values())
    
    def _calculate_combined_scores(self, 
                                 documents: List[Dict[str, Any]], 
                                 search_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calcola punteggi combinati e ordina i documenti.
        
        Args:
            documents: Lista di documenti da valutare
            search_strategy: Strategia di ricerca utilizzata
            
        Returns:
            Lista di documenti ordinati per punteggio
        """
        strategy_type = search_strategy.get("type", "both")
        
        for doc in documents:
            semantic_score = doc["semantic_score"]
            metadata_score = doc["metadata_score"]
            
            # Calcola il punteggio combinato in base alla strategia
            if strategy_type == "semantic":
                combined_score = semantic_score
            elif strategy_type == "metadata":
                combined_score = metadata_score
            else:  # both
                combined_score = (
                    semantic_score * self.semantic_weight + 
                    metadata_score * self.metadata_weight
                )
            
            doc["combined_score"] = combined_score
            doc["score_breakdown"] = {
                "semantic": semantic_score,
                "metadata": metadata_score,
                "combined": combined_score,
                "weights": {
                    "semantic": self.semantic_weight,
                    "metadata": self.metadata_weight
                }
            }
        
        # Ordina per punteggio combinato
        documents.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return documents
    
    def _generate_response_text(self, 
                              documents: List[Dict[str, Any]], 
                              search_strategy: Dict[str, Any], 
                              original_question: str) -> str:
        """
        Genera il testo della risposta basato sui documenti trovati.
        
        Args:
            documents: Documenti da includere nella risposta
            search_strategy: Strategia di ricerca utilizzata
            original_question: Domanda originale
            
        Returns:
            Testo della risposta
        """
        if not documents:
            return self.response_templates["no_results"]
        
        strategy_type = search_strategy.get("type", "both")
        
        if self.response_format == "summary":
            return self._generate_summary_response(documents, strategy_type)
        else:  # detailed
            return self._generate_detailed_response(documents, strategy_type)
    
    def _generate_summary_response(self, documents: List[Dict[str, Any]], strategy_type: str) -> str:
        """Genera una risposta in formato riassunto."""
        count = len(documents)
        template = self.response_templates.get(strategy_type, self.response_templates["both"])
        
        # Crea un riassunto semplice
        summary_parts = []
        
        for i, doc in enumerate(documents[:5], 1):  # Solo i primi 5 per il riassunto
            doc_info = f"{i}. "
            if "metadata" in doc and "filename" in doc["metadata"]:
                doc_info += f"File: {doc['metadata']['filename']}"
            else:
                doc_info += f"Documento ID: {doc['id']}"
            
            if doc.get("combined_score", 0) > 0.8:
                doc_info += " (Alta rilevanza)"
            elif doc.get("combined_score", 0) > 0.5:
                doc_info += " (Media rilevanza)"
            
            summary_parts.append(doc_info)
        
        if count > 5:
            summary_parts.append(f"... e altri {count - 5} documenti")
        
        results_text = "\n".join(summary_parts)
        return template.format(count=count, results=results_text)
    
    def _generate_detailed_response(self, documents: List[Dict[str, Any]], strategy_type: str) -> str:
        """Genera una risposta in formato dettagliato."""
        count = len(documents)
        template = self.response_templates.get(strategy_type, self.response_templates["both"])
        
        # Crea dettagli per ogni documento
        detailed_parts = []
        
        for i, doc in enumerate(documents, 1):
            doc_part = f"\n{i}. "
            
            # Titolo o ID
            if "metadata" in doc and "filename" in doc["metadata"]:
                doc_part += f"**{doc['metadata']['filename']}**"
            else:
                doc_part += f"**Documento {doc['id']}**"
            
            # Punteggio di rilevanza
            score = doc.get("combined_score", 0)
            if score > 0.8:
                doc_part += " ⭐⭐⭐"
            elif score > 0.6:
                doc_part += " ⭐⭐"
            elif score > 0.4:
                doc_part += " ⭐"
            
            # Snippet se disponibile
            snippet = doc.get("snippet", "")
            if snippet and self.include_snippets:
                doc_part += f"\n   📄 {snippet}"
            
            # Informazioni sui metadati se dalla ricerca metadata
            if doc.get("search_type") in ["metadata", "both"] and "match_reasons" in doc:
                reasons = ", ".join(doc["match_reasons"])
                doc_part += f"\n   🔍 Corrispondenze: {reasons}"
            
            # Data di creazione se disponibile
            if "metadata" in doc and "created_at" in doc["metadata"]:
                doc_part += f"\n   📅 Creato: {doc['metadata']['created_at'][:10]}"
            
            detailed_parts.append(doc_part)
        
        results_text = "".join(detailed_parts)
        return template.format(count=count, results=results_text)
    
    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Estrae informazioni sulle fonti dai documenti.
        
        Args:
            documents: Lista di documenti
            
        Returns:
            Lista di informazioni sulle fonti
        """
        sources = []
        
        for doc in documents:
            source = {
                "id": doc["id"],
                "type": doc.get("search_type", "unknown"),
                "score": doc.get("combined_score", 0.0)
            }
            
            # Aggiungi metadati rilevanti
            metadata = doc.get("metadata", {})
            if "filename" in metadata:
                source["filename"] = metadata["filename"]
            if "created_at" in metadata:
                source["created_at"] = metadata["created_at"]
            if "author" in metadata:
                source["author"] = metadata["author"]
            
            sources.append(source)
        
        return sources
    
    def _log_info(self, message: str) -> None:
        """Registra un messaggio informativo."""
        try:
            log_info(f"[ResponseAggregator] {message}")
        except Exception:
            pass
    
    def _log_debug(self, message: str) -> None:
        """Registra un messaggio di debug."""
        try:
            log_debug(f"[ResponseAggregator] {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """Registra un messaggio di avviso."""
        try:
            log_warning(f"[ResponseAggregator] {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """Registra un messaggio di errore."""
        try:
            log_error(f"[ResponseAggregator] {message}")
        except Exception:
            pass