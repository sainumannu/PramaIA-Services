import json
import re
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

class ChatQueryAnalyzerProcessor:
    """
    Processore per analizzare domande di chat e determinare il tipo di ricerca necessaria.
    Decide se serve ricerca semantica, ricerca sui metadati, o entrambe.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Estrai parametri di configurazione
        self.semantic_keywords = config.get("semantic_keywords", [
            "contenuto", "parla di", "spiega", "cos'è", "come", "perché", 
            "dimmi", "trova", "cerca", "informazioni su", "riguarda",
            "argomento", "tema", "descrive", "tratta"
        ])
        
        self.metadata_keywords = config.get("metadata_keywords", [
            "quando", "creato", "data", "autore", "scritto da", "formato",
            "tipo file", "dimensione", "modificato", "ultimo", "recente",
            "oggi", "ieri", "settimana", "mese", "anno", "prima", "dopo"
        ])
        
        self.temporal_patterns = config.get("temporal_patterns", [
            r'\b\d{4}\b',  # Anno (es. 2023)
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # Data (es. 23/11/2025)
            r'\boggi\b', r'\bieri\b', r'\bdomani\b',
            r'\bsettimana\b', r'\bmese\b', r'\banno\b',
            r'\brec\w*\b', r'\bultim\w*\b'
        ])
        
        self.confidence_threshold_semantic = config.get("confidence_threshold_semantic", 0.3)
        self.confidence_threshold_metadata = config.get("confidence_threshold_metadata", 0.2)
        
        self.default_strategy = config.get("default_strategy", "both")
        
        self._log_info(f"Chat Query Analyzer inizializzato per nodo {node_id}")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizza la query dell'utente e determina la strategia di ricerca.
        
        Args:
            inputs: Dizionario con la query dell'utente e i metadati
            
        Returns:
            Dizionario con l'analisi della query e la strategia consigliata
        """
        try:
            # Estrai la query dell'input
            question = inputs.get("question", "")
            if not question:
                raise ValueError("Campo 'question' richiesto ma non fornito")
            
            # Metadati aggiuntivi per il contesto
            user_id = inputs.get("user_id")
            session_id = inputs.get("session_id")
            mode = inputs.get("mode", "rag")
            
            self._log_info(f"Analisi query: '{question[:100]}...' per user {user_id}")
            
            # Analizza la query
            analysis = self._analyze_query(question)
            
            # Determina la strategia di ricerca
            strategy = self._determine_search_strategy(analysis)
            
            # Prepara l'output
            result = {
                "original_question": question,
                "analysis": analysis,
                "search_strategy": strategy,
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "mode": mode,
                    "timestamp": time.time(),
                    "analyzer_version": "1.0.0"
                }
            }
            
            self._log_info(f"Strategia determinata: {strategy['type']} (semantic: {strategy['needs_semantic']}, metadata: {strategy['needs_metadata']})")
            
            return result
            
        except Exception as e:
            self._log_error(f"Errore nell'analisi della query: {e}")
            # Fallback a strategia predefinita
            return {
                "original_question": inputs.get("question", ""),
                "analysis": {"error": str(e)},
                "search_strategy": {
                    "type": self.default_strategy,
                    "needs_semantic": True,
                    "needs_metadata": self.default_strategy in ["metadata", "both"],
                    "confidence": 0.5,
                    "reason": f"Fallback per errore: {e}"
                },
                "metadata": {
                    "error": True,
                    "timestamp": time.time()
                }
            }
    
    def _analyze_query(self, question: str) -> Dict[str, Any]:
        """
        Analizza la query per identificare intent e caratteristiche.
        
        Args:
            question: Domanda dell'utente
            
        Returns:
            Dizionario con l'analisi dettagliata
        """
        question_lower = question.lower()
        
        analysis = {
            "original_length": len(question),
            "word_count": len(question.split()),
            "semantic_indicators": [],
            "metadata_indicators": [],
            "temporal_references": [],
            "question_type": self._classify_question_type(question),
            "complexity": self._assess_complexity(question)
        }
        
        # Cerca indicatori semantici
        for keyword in self.semantic_keywords:
            if keyword in question_lower:
                analysis["semantic_indicators"].append(keyword)
        
        # Cerca indicatori di metadati
        for keyword in self.metadata_keywords:
            if keyword in question_lower:
                analysis["metadata_indicators"].append(keyword)
        
        # Cerca riferimenti temporali
        for pattern in self.temporal_patterns:
            matches = re.findall(pattern, question_lower)
            analysis["temporal_references"].extend(matches)
        
        # Calcola score di confidenza
        semantic_score = len(analysis["semantic_indicators"]) / len(self.semantic_keywords)
        metadata_score = (len(analysis["metadata_indicators"]) + len(analysis["temporal_references"])) / (len(self.metadata_keywords) + len(self.temporal_patterns))
        
        analysis["semantic_confidence"] = min(semantic_score * 2, 1.0)  # Normalizzato 0-1
        analysis["metadata_confidence"] = min(metadata_score * 3, 1.0)  # Normalizzato 0-1
        
        return analysis
    
    def _classify_question_type(self, question: str) -> str:
        """
        Classifica il tipo di domanda.
        
        Args:
            question: Domanda dell'utente
            
        Returns:
            Tipo di domanda
        """
        question_lower = question.lower().strip()
        
        # Domande informative (cosa, chi, dove)
        if any(word in question_lower for word in ["cos'è", "cosa", "chi", "dove", "quale"]):
            return "informational"
        
        # Domande temporali (quando)
        if any(word in question_lower for word in ["quando", "data", "ora", "tempo"]):
            return "temporal"
        
        # Domande procedurali (come)
        if any(word in question_lower for word in ["come", "modo", "procedura", "processo"]):
            return "procedural"
        
        # Domande causali (perché)
        if any(word in question_lower for word in ["perché", "motivo", "causa", "ragione"]):
            return "causal"
        
        # Richieste di ricerca generica
        if any(word in question_lower for word in ["trova", "cerca", "dimmi", "mostra"]):
            return "search"
        
        return "general"
    
    def _assess_complexity(self, question: str) -> str:
        """
        Valuta la complessità della domanda.
        
        Args:
            question: Domanda dell'utente
            
        Returns:
            Livello di complessità
        """
        word_count = len(question.split())
        
        # Presenza di congiunzioni complesse
        complex_indicators = ["tuttavia", "inoltre", "nonostante", "sebbene", "mentre", "oppure"]
        has_complex_language = any(word in question.lower() for word in complex_indicators)
        
        # Presenza di multipli criteri
        multiple_criteria = question.count(" e ") + question.count(" o ") + question.count(",")
        
        if word_count < 5:
            return "simple"
        elif word_count < 15 and not has_complex_language:
            return "medium"
        elif word_count >= 15 or has_complex_language or multiple_criteria > 2:
            return "complex"
        else:
            return "medium"
    
    def _determine_search_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determina la strategia di ricerca basata sull'analisi.
        
        Args:
            analysis: Risultato dell'analisi della query
            
        Returns:
            Strategia di ricerca consigliata
        """
        semantic_conf = analysis["semantic_confidence"]
        metadata_conf = analysis["metadata_confidence"]
        question_type = analysis["question_type"]
        
        # Logica di decisione
        needs_semantic = semantic_conf >= self.confidence_threshold_semantic
        needs_metadata = metadata_conf >= self.confidence_threshold_metadata
        
        # Aggiustamenti basati sul tipo di domanda
        if question_type == "temporal":
            needs_metadata = True
            metadata_conf = max(metadata_conf, 0.8)
        
        if question_type in ["informational", "procedural", "causal"]:
            needs_semantic = True
            semantic_conf = max(semantic_conf, 0.7)
        
        # Se non ci sono indicatori chiari, usa strategia predefinita
        if not needs_semantic and not needs_metadata:
            if self.default_strategy == "semantic":
                needs_semantic = True
            elif self.default_strategy == "metadata":
                needs_metadata = True
            else:  # both
                needs_semantic = True
                needs_metadata = True
        
        # Determina il tipo di strategia
        if needs_semantic and needs_metadata:
            strategy_type = "both"
            confidence = (semantic_conf + metadata_conf) / 2
            reason = "Richiede sia ricerca semantica che metadata"
        elif needs_semantic:
            strategy_type = "semantic"
            confidence = semantic_conf
            reason = "Focus su ricerca semantica del contenuto"
        elif needs_metadata:
            strategy_type = "metadata"
            confidence = metadata_conf
            reason = "Focus su ricerca nei metadati"
        else:
            strategy_type = "both"
            confidence = 0.5
            reason = "Strategia predefinita per sicurezza"
        
        return {
            "type": strategy_type,
            "needs_semantic": needs_semantic,
            "needs_metadata": needs_metadata,
            "confidence": confidence,
            "reason": reason,
            "semantic_confidence": semantic_conf,
            "metadata_confidence": metadata_conf,
            "priority": "semantic" if semantic_conf > metadata_conf else "metadata"
        }
    
    def _log_info(self, message: str) -> None:
        """Registra un messaggio informativo."""
        try:
            log_info(f"[ChatQueryAnalyzer] {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """Registra un messaggio di avviso."""
        try:
            log_warning(f"[ChatQueryAnalyzer] {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """Registra un messaggio di errore."""
        try:
            log_error(f"[ChatQueryAnalyzer] {message}")
        except Exception:
            pass