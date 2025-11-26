import json
import re
import time
from typing import Dict, Any, List, Optional, Union

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

class GenericQueryAnalyzerProcessor:
    """
    Processore generico per analizzare query e determinare strategie di elaborazione.
    Completamente configurabile per diversi scenari: chat, search, classification, intent detection, ecc.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Configurazione tipi di analisi
        self.analysis_types = config.get("analysis_types", ["classification", "intent", "strategy"])
        self.default_analysis_type = config.get("default_analysis_type", "classification")
        
        # Pattern configurabili per diversi domini
        self.analysis_patterns = config.get("analysis_patterns", {
            "semantic": ["contenuto", "spiega", "cos'è", "come", "dimmi"],
            "metadata": ["quando", "autore", "tipo", "data", "formato"],
            "temporal": [r'\b\d{4}\b', r'\boggi\b', r'\bieri\b', r'\bsettimana\b'],
            "intent_search": ["trova", "cerca", "mostra", "dammi"],
            "intent_info": ["cos'è", "cosa", "chi", "dove", "quale"],
            "intent_procedure": ["come", "modo", "procedura", "processo"]
        })
        
        # Soglie di confidenza configurabili
        self.confidence_thresholds = config.get("confidence_thresholds", {
            "semantic": 0.3,
            "metadata": 0.2,
            "intent": 0.4,
            "classification": 0.3
        })
        
        # Strategia di fallback
        self.fallback_strategy = config.get("fallback_strategy", {
            "type": "both",
            "confidence": 0.5,
            "reason": "Strategia predefinita"
        })
        
        # Configurazione output
        self.output_format = config.get("output_format", "detailed")  # "detailed", "simple", "classification_only"
        self.include_scores = config.get("include_scores", True)
        self.include_reasoning = config.get("include_reasoning", True)
        
        # Classificatori personalizzati
        self.custom_classifiers = config.get("custom_classifiers", {})
        
        # Normalizzazione input
        self.input_field = config.get("input_field", "query")  # Campo da analizzare
        self.text_preprocessing = config.get("text_preprocessing", {
            "lowercase": True,
            "remove_punctuation": False,
            "normalize_whitespace": True
        })
        
        self._log_info(f"Generic Query Analyzer inizializzato per nodo {node_id}")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizza la query in modo generico e configurabile.
        
        Args:
            inputs: Dizionario con la query e metadati
            
        Returns:
            Risultato dell'analisi configurabile
        """
        try:
            # Estrai il testo da analizzare (campo configurabile)
            query_text = self._extract_query_text(inputs)
            if not query_text:
                raise ValueError(f"Campo '{self.input_field}' richiesto ma non fornito o vuoto")
            
            # Metadati del contesto
            context_data = inputs.get("context", {})
            user_id = inputs.get("user_id", context_data.get("user_id"))
            session_id = inputs.get("session_id", context_data.get("session_id"))
            
            self._log_info(f"Analisi query generica: '{query_text[:100]}...'")
            
            # Pre-processing del testo
            processed_text = self._preprocess_text(query_text)
            
            # Analisi multi-dimensionale
            analysis_results = {}
            
            # Esegui tutti i tipi di analisi configurati
            for analysis_type in self.analysis_types:
                analysis_results[analysis_type] = self._perform_analysis(processed_text, analysis_type)
            
            # Determina strategia/output finale
            final_strategy = self._determine_final_strategy(analysis_results, processed_text)
            
            # Genera output nel formato richiesto
            result = self._generate_output(query_text, analysis_results, final_strategy, {
                "user_id": user_id,
                "session_id": session_id,
                "context": context_data
            })
            
            self._log_info(f"Analisi completata: strategia {final_strategy.get('type', 'unknown')}")
            
            return result
            
        except Exception as e:
            self._log_error(f"Errore nell'analisi generica: {e}")
            
            # Fallback generico
            return self._generate_fallback_output(inputs.get(self.input_field, ""), str(e))
    
    def _extract_query_text(self, inputs: Dict[str, Any]) -> str:
        """
        Estrae il testo da analizzare dall'input in modo configurabile.
        
        Args:
            inputs: Input del nodo
            
        Returns:
            Testo da analizzare
        """
        # Prova il campo configurato
        text = inputs.get(self.input_field)
        
        if not text:
            # Fallback su campi comuni
            for field in ["query", "question", "text", "message", "content"]:
                text = inputs.get(field)
                if text:
                    break
        
        # Se è un oggetto complesso, estrai il testo
        if isinstance(text, dict):
            text = text.get("text") or text.get("content") or str(text)
        
        return str(text) if text else ""
    
    def _preprocess_text(self, text: str) -> str:
        """
        Pre-processa il testo secondo la configurazione.
        
        Args:
            text: Testo originale
            
        Returns:
            Testo processato
        """
        processed = text
        
        if self.text_preprocessing.get("normalize_whitespace", True):
            processed = re.sub(r'\s+', ' ', processed.strip())
        
        if self.text_preprocessing.get("lowercase", True):
            processed = processed.lower()
        
        if self.text_preprocessing.get("remove_punctuation", False):
            processed = re.sub(r'[^\w\s]', ' ', processed)
            processed = re.sub(r'\s+', ' ', processed)
        
        return processed
    
    def _perform_analysis(self, text: str, analysis_type: str) -> Dict[str, Any]:
        """
        Esegue un tipo specifico di analisi sul testo.
        
        Args:
            text: Testo da analizzare
            analysis_type: Tipo di analisi da eseguire
            
        Returns:
            Risultato dell'analisi specifica
        """
        if analysis_type == "classification":
            return self._classify_by_patterns(text)
        elif analysis_type == "intent":
            return self._detect_intent(text)
        elif analysis_type == "strategy":
            return self._determine_strategy(text)
        elif analysis_type == "sentiment":
            return self._analyze_sentiment(text)
        elif analysis_type == "entities":
            return self._extract_entities(text)
        elif analysis_type == "complexity":
            return self._assess_complexity(text)
        elif analysis_type in self.custom_classifiers:
            return self._apply_custom_classifier(text, analysis_type)
        else:
            self._log_warning(f"Tipo di analisi sconosciuto: {analysis_type}")
            return {"type": "unknown", "confidence": 0.0}
    
    def _classify_by_patterns(self, text: str) -> Dict[str, Any]:
        """
        Classifica il testo basandosi sui pattern configurati.
        
        Args:
            text: Testo da classificare
            
        Returns:
            Risultato della classificazione
        """
        scores = {}
        matches = {}
        
        for category, patterns in self.analysis_patterns.items():
            category_matches = []
            category_score = 0.0
            
            for pattern in patterns:
                if isinstance(pattern, str):
                    # Pattern stringa semplice
                    if pattern in text:
                        category_matches.append(pattern)
                        category_score += 1.0
                else:
                    # Pattern regex
                    regex_matches = re.findall(pattern, text)
                    if regex_matches:
                        category_matches.extend(regex_matches)
                        category_score += len(regex_matches)
            
            # Normalizza il punteggio
            max_possible = len(patterns)
            normalized_score = min(category_score / max_possible, 1.0) if max_possible > 0 else 0.0
            
            scores[category] = normalized_score
            matches[category] = category_matches
        
        # Trova la categoria migliore
        best_category = max(scores, key=scores.get) if scores else "unknown"
        best_score = scores.get(best_category, 0.0)
        
        return {
            "best_category": best_category,
            "confidence": best_score,
            "all_scores": scores,
            "matches": matches,
            "analysis_type": "classification"
        }
    
    def _detect_intent(self, text: str) -> Dict[str, Any]:
        """
        Rileva l'intent della query.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Intent rilevato
        """
        intent_patterns = {
            "search": self.analysis_patterns.get("intent_search", ["trova", "cerca"]),
            "information": self.analysis_patterns.get("intent_info", ["cos'è", "cosa"]),
            "procedure": self.analysis_patterns.get("intent_procedure", ["come", "modo"]),
            "comparison": self.analysis_patterns.get("intent_compare", ["confronta", "differenza"]),
            "question": ["\\?", "domanda", "chiedo"]
        }
        
        intent_scores = {}
        for intent, patterns in intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                if isinstance(pattern, str):
                    score += 1.0 if pattern in text else 0.0
                else:
                    matches = re.findall(pattern, text)
                    score += len(matches)
            
            intent_scores[intent] = score / len(patterns) if patterns else 0.0
        
        best_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "general"
        confidence = intent_scores.get(best_intent, 0.0)
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "all_intents": intent_scores,
            "analysis_type": "intent"
        }
    
    def _determine_strategy(self, text: str) -> Dict[str, Any]:
        """
        Determina la strategia di processing basata sul testo.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Strategia consigliata
        """
        # Analizza per categorie di strategia
        semantic_indicators = len([p for p in self.analysis_patterns.get("semantic", []) if p in text])
        metadata_indicators = len([p for p in self.analysis_patterns.get("metadata", []) if p in text])
        temporal_indicators = sum(len(re.findall(p, text)) for p in self.analysis_patterns.get("temporal", []))
        
        semantic_score = semantic_indicators / max(len(self.analysis_patterns.get("semantic", [])), 1)
        metadata_score = (metadata_indicators + temporal_indicators) / max(len(self.analysis_patterns.get("metadata", [])) + len(self.analysis_patterns.get("temporal", [])), 1)
        
        # Determina strategia
        semantic_threshold = self.confidence_thresholds.get("semantic", 0.3)
        metadata_threshold = self.confidence_thresholds.get("metadata", 0.2)
        
        needs_semantic = semantic_score >= semantic_threshold
        needs_metadata = metadata_score >= metadata_threshold
        
        if needs_semantic and needs_metadata:
            strategy_type = "both"
            confidence = (semantic_score + metadata_score) / 2
        elif needs_semantic:
            strategy_type = "semantic"
            confidence = semantic_score
        elif needs_metadata:
            strategy_type = "metadata"
            confidence = metadata_score
        else:
            strategy_type = self.fallback_strategy.get("type", "both")
            confidence = 0.5
        
        return {
            "strategy": strategy_type,
            "confidence": confidence,
            "needs_semantic": needs_semantic,
            "needs_metadata": needs_metadata,
            "semantic_score": semantic_score,
            "metadata_score": metadata_score,
            "analysis_type": "strategy"
        }
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analizza il sentiment del testo (implementazione base).
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Sentiment rilevato
        """
        positive_words = ["buono", "bene", "ottimo", "perfetto", "grazie", "fantastico"]
        negative_words = ["male", "sbagliato", "errore", "problema", "cattivo", "pessimo"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = positive_count / (positive_count + negative_count + 1)
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = negative_count / (positive_count + negative_count + 1)
        else:
            sentiment = "neutral"
            confidence = 0.5
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
            "analysis_type": "sentiment"
        }
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Estrae entità dal testo (implementazione base).
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Entità estratte
        """
        # Pattern base per entità comuni
        entities = {
            "dates": re.findall(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', text),
            "years": re.findall(r'\b\d{4}\b', text),
            "numbers": re.findall(r'\b\d+\b', text),
            "emails": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
            "urls": re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        }
        
        # Rimuovi entità vuote
        entities = {k: v for k, v in entities.items() if v}
        entity_count = sum(len(v) for v in entities.values())
        
        return {
            "entities": entities,
            "entity_count": entity_count,
            "entity_types": list(entities.keys()),
            "analysis_type": "entities"
        }
    
    def _assess_complexity(self, text: str) -> Dict[str, Any]:
        """
        Valuta la complessità del testo.
        
        Args:
            text: Testo da valutare
            
        Returns:
            Valutazione della complessità
        """
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        avg_word_length = sum(len(word) for word in text.split()) / max(word_count, 1)
        
        # Indicatori di complessità
        complex_words = len([word for word in text.split() if len(word) > 7])
        conjunctions = len(re.findall(r'\b(tuttavia|inoltre|nonostante|sebbene|mentre|oppure|però|infatti)\b', text.lower()))
        
        # Calcola score di complessità
        complexity_score = (
            (word_count / 20) * 0.3 +
            (avg_word_length / 10) * 0.2 +
            (complex_words / max(word_count, 1)) * 0.3 +
            (conjunctions / max(sentence_count, 1)) * 0.2
        )
        
        if complexity_score < 0.3:
            level = "simple"
        elif complexity_score < 0.7:
            level = "medium"
        else:
            level = "complex"
        
        return {
            "complexity_level": level,
            "complexity_score": min(complexity_score, 1.0),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_word_length": avg_word_length,
            "complex_words": complex_words,
            "analysis_type": "complexity"
        }
    
    def _apply_custom_classifier(self, text: str, classifier_name: str) -> Dict[str, Any]:
        """
        Applica un classificatore personalizzato.
        
        Args:
            text: Testo da classificare
            classifier_name: Nome del classificatore
            
        Returns:
            Risultato della classificazione personalizzata
        """
        classifier_config = self.custom_classifiers.get(classifier_name, {})
        patterns = classifier_config.get("patterns", {})
        
        if not patterns:
            return {"type": "unknown", "confidence": 0.0, "analysis_type": "custom"}
        
        scores = {}
        for category, category_patterns in patterns.items():
            score = 0.0
            for pattern in category_patterns:
                if pattern in text:
                    score += 1.0
            scores[category] = score / len(category_patterns) if category_patterns else 0.0
        
        best_category = max(scores, key=scores.get) if scores else "unknown"
        confidence = scores.get(best_category, 0.0)
        
        return {
            "category": best_category,
            "confidence": confidence,
            "all_scores": scores,
            "classifier": classifier_name,
            "analysis_type": "custom"
        }
    
    def _determine_final_strategy(self, analysis_results: Dict[str, Any], text: str) -> Dict[str, Any]:
        """
        Determina la strategia finale basata su tutti i risultati di analisi.
        
        Args:
            analysis_results: Risultati di tutte le analisi
            text: Testo originale
            
        Returns:
            Strategia finale
        """
        # Se c'è un'analisi di strategia, usala come base
        if "strategy" in analysis_results:
            return analysis_results["strategy"]
        
        # Altrimenti, combina i risultati disponibili
        final_strategy = self.fallback_strategy.copy()
        
        # Usa classificazione se disponibile
        if "classification" in analysis_results:
            classification = analysis_results["classification"]
            best_category = classification.get("best_category", "unknown")
            
            if best_category in ["semantic", "content", "information"]:
                final_strategy.update({
                    "type": "semantic",
                    "confidence": classification.get("confidence", 0.5),
                    "reason": f"Classificato come {best_category}"
                })
            elif best_category in ["metadata", "temporal", "structure"]:
                final_strategy.update({
                    "type": "metadata", 
                    "confidence": classification.get("confidence", 0.5),
                    "reason": f"Classificato come {best_category}"
                })
        
        # Aggiungi informazioni da intent se disponibile
        if "intent" in analysis_results:
            intent_data = analysis_results["intent"]
            final_strategy["intent"] = intent_data.get("intent", "unknown")
        
        return final_strategy
    
    def _generate_output(self, original_text: str, analysis_results: Dict[str, Any], 
                        final_strategy: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera l'output finale nel formato configurato.
        
        Args:
            original_text: Testo originale
            analysis_results: Risultati di tutte le analisi
            final_strategy: Strategia finale determinata
            metadata: Metadati del contesto
            
        Returns:
            Output formattato
        """
        if self.output_format == "simple":
            return {
                "strategy": final_strategy.get("type", "unknown"),
                "confidence": final_strategy.get("confidence", 0.5)
            }
        elif self.output_format == "classification_only":
            classification = analysis_results.get("classification", {})
            return {
                "category": classification.get("best_category", "unknown"),
                "confidence": classification.get("confidence", 0.0),
                "matches": classification.get("matches", {})
            }
        else:  # detailed
            result = {
                "original_query": original_text,
                "strategy": final_strategy,
                "metadata": {
                    **metadata,
                    "timestamp": time.time(),
                    "analyzer_version": "2.0.0-generic",
                    "node_id": self.node_id
                }
            }
            
            if self.include_scores:
                result["analysis_results"] = analysis_results
            
            if self.include_reasoning:
                result["reasoning"] = self._generate_reasoning(analysis_results, final_strategy)
            
            return result
    
    def _generate_reasoning(self, analysis_results: Dict[str, Any], final_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera spiegazione del ragionamento seguito.
        
        Args:
            analysis_results: Risultati delle analisi
            final_strategy: Strategia finale
            
        Returns:
            Spiegazione del ragionamento
        """
        reasoning = {
            "strategy_reason": final_strategy.get("reason", "Strategia determinata automaticamente"),
            "confidence_factors": []
        }
        
        # Analizza i fattori che hanno influenzato la confidenza
        for analysis_type, result in analysis_results.items():
            confidence = result.get("confidence", 0.0)
            if confidence > 0.3:
                reasoning["confidence_factors"].append({
                    "analysis": analysis_type,
                    "confidence": confidence,
                    "contribution": f"Analisi {analysis_type} con confidenza {confidence:.2f}"
                })
        
        return reasoning
    
    def _generate_fallback_output(self, query: str, error: str) -> Dict[str, Any]:
        """
        Genera output di fallback in caso di errore.
        
        Args:
            query: Query originale
            error: Descrizione dell'errore
            
        Returns:
            Output di fallback
        """
        return {
            "original_query": query,
            "strategy": self.fallback_strategy,
            "error": error,
            "metadata": {
                "error": True,
                "timestamp": time.time(),
                "node_id": self.node_id
            }
        }
    
    def _log_info(self, message: str) -> None:
        """Registra un messaggio informativo."""
        try:
            log_info(f"[GenericQueryAnalyzer] {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """Registra un messaggio di avviso."""
        try:
            log_warning(f"[GenericQueryAnalyzer] {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """Registra un messaggio di errore."""
        try:
            log_error(f"[GenericQueryAnalyzer] {message}")
        except Exception:
            pass