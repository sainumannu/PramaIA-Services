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

class GenericAggregatorProcessor:
    """
    Processore generico per aggregare risultati da fonti multiple.
    Può combinare e deduplicare risultati di qualsiasi tipo con scoring configurabile.
    Completamente riutilizzabile per diversi workflow e scenari.
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
        
        self._log_info(f"Generic Aggregator inizializzato per nodo {node_id}")
    
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
    
    def _calculate_combined_scores(self, results: List[Dict[str, Any]], sources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calcola punteggi combinati per tutti i risultati.
        
        Args:
            results: Lista di risultati da valutare
            sources: Fonti originali per pesatura
            
        Returns:
            Lista di risultati ordinati per punteggio
        """
        if not results:
            return []
        
        # Calcola pesi per fonte
        source_weights = self._calculate_source_weights(sources)
        
        for result in results:
            source = result.get("source", "unknown")
            source_weight = source_weights.get(source, 1.0)
            original_score = result.get("score", 0.0)
            
            # Calcola score combinato basato su strategia
            if self.scoring_method == "weighted_average":
                combined_score = original_score * source_weight
            elif self.scoring_method == "max":
                combined_score = max(original_score, source_weight)
            elif self.scoring_method == "product":
                combined_score = original_score * source_weight
            else:  # "sum"
                combined_score = original_score + source_weight
            
            result["combined_score"] = combined_score
            result["source_weight"] = source_weight
            result["score_breakdown"] = {
                "original": original_score,
                "source_weight": source_weight,
                "combined": combined_score,
                "method": self.scoring_method
            }
        
        # Normalizza scores se richiesto
        if self.score_normalization:
            results = self._normalize_scores(results)
        
        # Ordina per punteggio combinato
        results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        
        return results
    
    def _calculate_source_weights(self, sources: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcola i pesi per ogni fonte basandosi sulla configurazione.
        
        Args:
            sources: Dizionario delle fonti
            
        Returns:
            Dizionario con i pesi per fonte
        """
        weights = {}
        source_names = list(sources.keys())
        
        # Se ci sono pesi configurati, usali
        if isinstance(self.weights, dict):
            for source_name in source_names:
                # Cerca peso esatto o usa pattern matching
                weight = self.weights.get(source_name)
                if weight is None:
                    # Cerca pattern (es. "semantic" per "semantic_results")
                    for pattern, value in self.weights.items():
                        if pattern in source_name:
                            weight = value
                            break
                
                weights[source_name] = weight or 1.0
        else:
            # Pesi uguali per tutti
            equal_weight = 1.0 / len(source_names) if source_names else 1.0
            weights = {name: equal_weight for name in source_names}
        
        return weights
    
    def _normalize_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizza i punteggi combinati tra 0 e 1.
        
        Args:
            results: Lista di risultati con punteggi
            
        Returns:
            Lista con punteggi normalizzati
        """
        if not results:
            return results
        
        scores = [r.get("combined_score", 0) for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        # Evita divisione per zero
        if max_score == min_score:
            for result in results:
                result["normalized_score"] = 1.0
        else:
            for result in results:
                original = result.get("combined_score", 0)
                normalized = (original - min_score) / (max_score - min_score)
                result["normalized_score"] = normalized
                result["combined_score"] = normalized  # Sostituisce il score originale
        
        return results
    
    def _generate_output(self, results: List[Dict[str, Any]], sources: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera l'output finale nel formato richiesto.
        
        Args:
            results: Risultati finali
            sources: Fonti originali
            context: Contesto della richiesta
            
        Returns:
            Output formattato
        """
        base_output = {
            "results": results,
            "total_count": len(results),
            "sources_summary": self._generate_sources_summary(sources)
        }
        
        # Aggiungi metadati se richiesti
        if self.include_metadata:
            base_output["processing_metadata"] = {
                "aggregation_strategy": self.aggregation_strategy,
                "scoring_method": self.scoring_method,
                "deduplication_enabled": self.enable_deduplication,
                "source_weights": self._calculate_source_weights(sources)
            }
        
        # Aggiungi informazioni sulle fonti se richieste
        if self.include_sources:
            base_output["sources"] = self._extract_source_info(results)
        
        # Formatta l'output se richiesto
        if self.output_format == "formatted_text":
            base_output["formatted_output"] = self._format_as_text(results, context)
        elif self.output_format == "structured":
            # Già strutturato
            pass
        elif self.output_format == "raw":
            # Solo i risultati
            return {"results": results}
        
        return base_output
    
    def _generate_sources_summary(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un riassunto delle fonti utilizzate.
        
        Args:
            sources: Fonti originali
            
        Returns:
            Riassunto delle fonti
        """
        summary = {
            "total_sources": len(sources),
            "source_names": list(sources.keys()),
            "results_per_source": {}
        }
        
        for name, data in sources.items():
            if isinstance(data, dict):
                result_count = len(data.get("results", []))
            else:
                result_count = len(data) if isinstance(data, list) else 1
            
            summary["results_per_source"][name] = result_count
        
        return summary
    
    def _extract_source_info(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Estrae informazioni sulle fonti dai risultati.
        
        Args:
            results: Lista di risultati
            
        Returns:
            Lista di informazioni sulle fonti
        """
        source_info = []
        
        for result in results:
            info = {
                "id": result.get("id"),
                "source": result.get("source"),
                "score": result.get("combined_score", result.get("score", 0)),
                "type": result.get("source_type", "unknown")
            }
            
            # Aggiungi metadati rilevanti
            metadata = result.get("metadata", {})
            for key in ["title", "filename", "url", "created_at", "author"]:
                if key in metadata:
                    info[key] = metadata[key]
            
            source_info.append(info)
        
        return source_info
    
    def _format_as_text(self, results: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """
        Formatta i risultati come testo leggibile.
        
        Args:
            results: Lista di risultati
            context: Contesto per personalizzazione
            
        Returns:
            Testo formattato
        """
        if not results:
            return self.format_templates["no_results_template"]
        
        # Header
        source_count = len(set(r.get("source") for r in results))
        header = self.format_templates["summary_template"].format(
            count=len(results),
            sources=source_count
        )
        
        # Items
        formatted_items = []
        for i, result in enumerate(results, 1):
            item_text = self.format_templates["item_template"].format(
                index=i,
                title=result.get("metadata", {}).get("title", f"Item {result.get('id', i)}"),
                content=result.get("content", "")[:200] + ("..." if len(result.get("content", "")) > 200 else ""),
                score=f"({result.get('combined_score', 0):.2f})" if result.get('combined_score') else ""
            )
            formatted_items.append(item_text)
        
        return f"{header}\n\n" + "\n\n".join(formatted_items)
    
    def _log_info(self, message: str) -> None:
        """Registra un messaggio informativo."""
        try:
            log_info(f"[GenericAggregator] {message}")
        except Exception:
            pass
    
    def _log_debug(self, message: str) -> None:
        """Registra un messaggio di debug."""
        try:
            log_debug(f"[GenericAggregator] {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """Registra un messaggio di avviso."""
        try:
            log_warning(f"[GenericAggregator] {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """Registra un messaggio di errore."""
        try:
            log_error(f"[GenericAggregator] {message}")
        except Exception:
            pass