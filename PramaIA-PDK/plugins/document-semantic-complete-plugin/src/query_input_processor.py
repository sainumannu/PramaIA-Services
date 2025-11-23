"""
Query Input Processor

Elabora e prepara la query utente per la ricerca semantica.
"""

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


class QueryInputProcessor:
    """Processore per elaborare l'input query dell'utente."""
    
    def __init__(self):
        pass
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Elabora la query dell'utente per la ricerca semantica.
        """
        logger.info("[QueryInput] INGRESSO nodo: process")
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            raw_query = inputs.get('query', '')
            if not raw_query or not raw_query.strip():
                raise ValueError("Query vuota o mancante")
            max_query_length = config.get('max_query_length', 500)
            enable_preprocessing = config.get('enable_preprocessing', True)
            query_language = config.get('query_language', 'auto')
            expand_query = config.get('expand_query', False)
            processed_query = await self._process_query(
                raw_query=raw_query,
                max_query_length=max_query_length,
                enable_preprocessing=enable_preprocessing,
                query_language=query_language,
                expand_query=expand_query
            )
            logger.info(f"[QueryInput] USCITA nodo (successo): Query elaborata: '{processed_query[:50]}...'")
            return {
                "status": "success",
                "processed_query": processed_query,
                "query_metadata": {
                    "original_query": raw_query,
                    "processed_query": processed_query,
                    "query_length": len(processed_query),
                    "language": query_language,
                    "preprocessing_enabled": enable_preprocessing,
                    "query_expanded": expand_query
                }
            }
        except Exception as e:
            logger.error(f"[QueryInput] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "processed_query": "",
                "query_metadata": {
                    "original_query": "",
                    "processed_query": "",
                    "query_length": 0
                }
            }
    
    async def _process_query(self, raw_query: str, max_query_length: int,
                           enable_preprocessing: bool, query_language: str,
                           expand_query: bool) -> str:
        """
        Elabora la query grezza.
        
        Args:
            raw_query: Query originale dell'utente
            max_query_length: Lunghezza massima query
            enable_preprocessing: Se abilitare preprocessing
            query_language: Lingua della query
            expand_query: Se espandere la query
            
        Returns:
            Query elaborata
        """
        processed_query = raw_query.strip()
        
        # Applica lunghezza massima
        if len(processed_query) > max_query_length:
            processed_query = processed_query[:max_query_length].strip()
            logger.info(f"📏 Query troncata a {max_query_length} caratteri")
        
        # Preprocessing se abilitato
        if enable_preprocessing:
            processed_query = self._preprocess_query(processed_query)
        
        # Espansione query se richiesta
        if expand_query:
            processed_query = self._expand_query(processed_query, query_language)
        
        # Validazione finale
        if not processed_query or len(processed_query.strip()) < 3:
            logger.warning("⚠️ Query troppo breve dopo elaborazione")
            processed_query = raw_query.strip()  # Fallback to original
        
        return processed_query
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocessing della query.
        
        Args:
            query: Query da preprocessare
            
        Returns:
            Query preprocessata
        """
        # Rimuovi caratteri extra
        query = re.sub(r'\s+', ' ', query)  # Normalizza spazi
        query = re.sub(r'[^\w\s\-\.\?\!]', '', query)  # Rimuovi caratteri speciali
        
        # Rimuovi parole stop molto comuni (opzionale)
        stop_words = ['il', 'la', 'di', 'che', 'e', 'a', 'un', 'una', 'per', 'con', 'non', 'una', 'su']
        words = query.split()
        
        # Mantieni almeno 3 parole significative
        filtered_words = [w for w in words if w.lower() not in stop_words or len(words) <= 3]
        
        if len(filtered_words) >= 2:
            query = ' '.join(filtered_words)
        
        return query.strip()
    
    def _expand_query(self, query: str, language: str) -> str:
        """
        Espande la query con sinonimi o termini correlati.
        
        Args:
            query: Query da espandere
            language: Lingua della query
            
        Returns:
            Query espansa
        """
        # Espansione semplice basata su parole chiave comuni
        expansions = {
            'it': {
                'documento': 'documento testo file',
                'ricerca': 'ricerca trova cerca',
                'informazione': 'informazione dato info',
                'analisi': 'analisi analizza esame studio',
                'rapporto': 'rapporto report documento relazione',
                'progetto': 'progetto piano lavoro',
                'sistema': 'sistema struttura organizzazione',
                'processo': 'processo procedura metodo'
            },
            'en': {
                'document': 'document file text',
                'search': 'search find lookup',
                'information': 'information data info',
                'analysis': 'analysis analyze examination study',
                'report': 'report document summary',
                'project': 'project plan work',
                'system': 'system structure organization',
                'process': 'process procedure method'
            }
        }
        
        # Applica espansioni se disponibili
        lang_expansions = expansions.get(language, expansions.get('it', {}))
        
        words = query.lower().split()
        expanded_terms = []
        
        for word in words:
            if word in lang_expansions:
                expanded_terms.append(lang_expansions[word])
            else:
                expanded_terms.append(word)
        
        expanded_query = ' '.join(expanded_terms)
        
        # Limita lunghezza espansione
        if len(expanded_query) > len(query) * 2:
            expanded_query = query  # Fallback se troppo lunga
        
        return expanded_query
    
    def _detect_query_language(self, query: str) -> str:
        """
        Rileva la lingua della query (semplice).
        
        Args:
            query: Query da analizzare
            
        Returns:
            Codice lingua rilevato
        """
        # Parole indicative per italiano
        italian_words = ['come', 'cosa', 'dove', 'quando', 'perche', 'quale', 'chi', 
                        'documento', 'informazione', 'ricerca', 'trova', 'analisi']
        
        # Parole indicative per inglese
        english_words = ['how', 'what', 'where', 'when', 'why', 'which', 'who',
                        'document', 'information', 'search', 'find', 'analysis']
        
        query_lower = query.lower()
        
        italian_count = sum(1 for word in italian_words if word in query_lower)
        english_count = sum(1 for word in english_words if word in query_lower)
        
        if italian_count > english_count:
            return 'it'
        elif english_count > italian_count:
            return 'en'
        else:
            return 'auto'  # Non determinabile


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il nodo Query Input."""
    processor = QueryInputProcessor()
    return await processor.process(context)
