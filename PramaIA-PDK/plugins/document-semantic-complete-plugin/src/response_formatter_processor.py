"""
Response Formatter Processor

Formatta la risposta finale del sistema di ricerca semantica dei documenti.
"""

import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseFormatterProcessor:
    """Processore per formattare la risposta finale del sistema."""
    
    def __init__(self):
        pass
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Formatta la risposta finale del sistema.
        
        Args:
            context: Contesto di esecuzione con inputs e config
            
        Returns:
            Dict contenente la risposta formattata
        """
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            
            # Ottieni risposta LLM e metadati
            llm_response = inputs.get('llm_response', {})
            processing_metadata = inputs.get('processing_metadata', {})
            
            if not llm_response:
                logger.warning("⚠️ Nessuna risposta LLM fornita")
                return self._create_default_response("Nessuna risposta disponibile.")
            
            # Configurazione formattazione
            output_format = config.get('output_format', 'detailed')  # detailed, simple, json, markdown
            include_metadata = config.get('include_metadata', True)
            include_sources = config.get('include_sources', True)
            include_confidence = config.get('include_confidence', True)
            max_response_length = config.get('max_response_length', 0)  # 0 = no limit
            
            # Formatta risposta secondo il formato richiesto
            formatted_response = await self._format_response(
                llm_response=llm_response,
                processing_metadata=processing_metadata,
                output_format=output_format,
                include_metadata=include_metadata,
                include_sources=include_sources,
                include_confidence=include_confidence,
                max_response_length=max_response_length
            )
            
            logger.info(f"✅ Risposta formattata in formato {output_format}")
            
            return {
                "status": "success",
                "formatted_response": formatted_response,
                "formatting_metadata": {
                    "output_format": output_format,
                    "response_length": len(formatted_response.get('content', '')),
                    "formatted_at": datetime.now().isoformat(),
                    "included_metadata": include_metadata,
                    "included_sources": include_sources
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Errore formattazione risposta: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "formatted_response": self._create_error_response(str(e)),
                "formatting_metadata": {
                    "output_format": "error",
                    "response_length": 0,
                    "formatted_at": datetime.now().isoformat()
                }
            }
    
    async def _format_response(self, llm_response: Dict[str, Any], 
                             processing_metadata: Dict[str, Any],
                             output_format: str,
                             include_metadata: bool,
                             include_sources: bool,
                             include_confidence: bool,
                             max_response_length: int) -> Dict[str, Any]:
        """
        Formatta la risposta secondo il formato specificato.
        
        Args:
            llm_response: Risposta del LLM
            processing_metadata: Metadati del processing
            output_format: Formato di output
            include_metadata: Se includere metadati
            include_sources: Se includere informazioni sulle fonti
            include_confidence: Se includere score di confidenza
            max_response_length: Lunghezza massima risposta
            
        Returns:
            Risposta formattata
        """
        content = llm_response.get('content', '')
        
        # Applica limite lunghezza se specificato
        if max_response_length > 0 and len(content) > max_response_length:
            content = content[:max_response_length] + "..."
            logger.info(f"📏 Risposta troncata a {max_response_length} caratteri")
        
        if output_format == "simple":
            return self._format_simple(content)
        elif output_format == "json":
            return self._format_json(content, llm_response, processing_metadata, 
                                   include_metadata, include_sources, include_confidence)
        elif output_format == "markdown":
            return self._format_markdown(content, llm_response, processing_metadata,
                                       include_metadata, include_sources, include_confidence)
        else:  # detailed (default)
            return self._format_detailed(content, llm_response, processing_metadata,
                                       include_metadata, include_sources, include_confidence)
    
    def _format_simple(self, content: str) -> Dict[str, Any]:
        """Formato semplice - solo il contenuto."""
        return {
            "content": content,
            "format": "simple"
        }
    
    def _format_json(self, content: str, llm_response: Dict[str, Any], 
                    processing_metadata: Dict[str, Any],
                    include_metadata: bool, include_sources: bool, 
                    include_confidence: bool) -> Dict[str, Any]:
        """Formato JSON strutturato."""
        response = {
            "answer": content,
            "format": "json"
        }
        
        if include_metadata:
            response["metadata"] = {
                "model": llm_response.get('model', 'unknown'),
                "provider": llm_response.get('provider', 'unknown'),
                "documents_processed": processing_metadata.get('documents_processed', 0),
                "total_tokens": llm_response.get('usage', {}).get('total_tokens', 0)
            }
        
        if include_sources:
            response["sources"] = {
                "documents_used": processing_metadata.get('documents_processed', 0),
                "original_query": processing_metadata.get('original_query', '')
            }
        
        if include_confidence:
            # Calcola confidence score basico
            confidence = self._calculate_confidence_score(llm_response, processing_metadata)
            response["confidence_score"] = confidence
        
        return response
    
    def _format_markdown(self, content: str, llm_response: Dict[str, Any],
                        processing_metadata: Dict[str, Any],
                        include_metadata: bool, include_sources: bool,
                        include_confidence: bool) -> Dict[str, Any]:
        """Formato Markdown con sezioni strutturate."""
        markdown_content = f"# Risposta Ricerca Semantica\n\n{content}\n\n"
        
        if include_sources:
            docs_count = processing_metadata.get('documents_processed', 0)
            original_query = processing_metadata.get('original_query', '')
            markdown_content += f"## Fonti\n\n"
            markdown_content += f"- **Documenti analizzati**: {docs_count}\n"
            markdown_content += f"- **Query originale**: {original_query}\n\n"
        
        if include_metadata:
            model = llm_response.get('model', 'unknown')
            provider = llm_response.get('provider', 'unknown')
            tokens = llm_response.get('usage', {}).get('total_tokens', 0)
            
            markdown_content += f"## Dettagli Tecnici\n\n"
            markdown_content += f"- **Modello**: {provider}/{model}\n"
            markdown_content += f"- **Token utilizzati**: {tokens}\n"
            markdown_content += f"- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if include_confidence:
            confidence = self._calculate_confidence_score(llm_response, processing_metadata)
            markdown_content += f"## Affidabilità\n\n"
            markdown_content += f"- **Score di confidenza**: {confidence:.2f}/1.00\n\n"
        
        return {
            "content": markdown_content,
            "format": "markdown"
        }
    
    def _format_detailed(self, content: str, llm_response: Dict[str, Any],
                        processing_metadata: Dict[str, Any],
                        include_metadata: bool, include_sources: bool,
                        include_confidence: bool) -> Dict[str, Any]:
        """Formato dettagliato con tutte le informazioni."""
        response = {
            "content": content,
            "format": "detailed"
        }
        
        # Sezione principale
        response["answer"] = content
        
        # Informazioni LLM
        response["llm_info"] = {
            "model": llm_response.get('model', 'unknown'),
            "provider": llm_response.get('provider', 'unknown'),
            "usage": llm_response.get('usage', {})
        }
        
        # Informazioni processing se richieste
        if include_metadata:
            response["processing_info"] = {
                "documents_processed": processing_metadata.get('documents_processed', 0),
                "original_query": processing_metadata.get('original_query', ''),
                "response_length": processing_metadata.get('response_length', 0),
                "processed_at": datetime.now().isoformat()
            }
        
        # Informazioni fonti se richieste
        if include_sources:
            response["source_info"] = {
                "total_documents": processing_metadata.get('documents_processed', 0),
                "query_used": processing_metadata.get('original_query', ''),
                "retrieval_method": "semantic_similarity"
            }
        
        # Score di confidenza se richiesto
        if include_confidence:
            confidence = self._calculate_confidence_score(llm_response, processing_metadata)
            response["confidence_info"] = {
                "confidence_score": confidence,
                "confidence_level": self._get_confidence_level(confidence),
                "factors": self._get_confidence_factors(llm_response, processing_metadata)
            }
        
        return response
    
    def _calculate_confidence_score(self, llm_response: Dict[str, Any], 
                                  processing_metadata: Dict[str, Any]) -> float:
        """
        Calcola un score di confidenza basico.
        
        Args:
            llm_response: Risposta LLM
            processing_metadata: Metadati processing
            
        Returns:
            Score di confidenza tra 0 e 1
        """
        confidence_factors = []
        
        # Fattore 1: Numero di documenti processati
        docs_processed = processing_metadata.get('documents_processed', 0)
        if docs_processed > 0:
            doc_factor = min(docs_processed / 5.0, 1.0)  # Max confidence at 5+ docs
            confidence_factors.append(doc_factor)
        
        # Fattore 2: Lunghezza risposta (risposte più lunghe potrebbero essere più complete)
        response_length = len(llm_response.get('content', ''))
        if response_length > 0:
            length_factor = min(response_length / 500.0, 1.0)  # Max at 500+ chars
            confidence_factors.append(length_factor)
        
        # Fattore 3: Provider del modello (alcuni sono più affidabili)
        provider = llm_response.get('provider', '')
        if provider in ['openai', 'anthropic']:
            confidence_factors.append(0.9)
        elif provider == 'mock':
            confidence_factors.append(0.3)
        else:
            confidence_factors.append(0.7)
        
        # Media dei fattori
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5  # Default
    
    def _get_confidence_level(self, score: float) -> str:
        """Converte score numerico in livello testuale."""
        if score >= 0.8:
            return "Alta"
        elif score >= 0.6:
            return "Media"
        elif score >= 0.4:
            return "Bassa"
        else:
            return "Molto Bassa"
    
    def _get_confidence_factors(self, llm_response: Dict[str, Any],
                              processing_metadata: Dict[str, Any]) -> List[str]:
        """Restituisce lista dei fattori che influenzano la confidenza."""
        factors = []
        
        docs_count = processing_metadata.get('documents_processed', 0)
        if docs_count > 3:
            factors.append(f"Buon numero di documenti analizzati ({docs_count})")
        elif docs_count > 0:
            factors.append(f"Documenti limitati analizzati ({docs_count})")
        else:
            factors.append("Nessun documento analizzato")
        
        provider = llm_response.get('provider', '')
        if provider in ['openai', 'anthropic']:
            factors.append(f"Modello affidabile utilizzato ({provider})")
        elif provider == 'mock':
            factors.append("Sistema in modalità test")
        
        response_length = len(llm_response.get('content', ''))
        if response_length > 200:
            factors.append("Risposta dettagliata fornita")
        elif response_length < 50:
            factors.append("Risposta molto breve")
        
        return factors
    
    def _create_default_response(self, message: str) -> Dict[str, Any]:
        """Crea una risposta di default."""
        return {
            "content": message,
            "format": "default",
            "answer": message,
            "llm_info": {"model": "none", "provider": "none"}
        }
    
    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Crea una risposta di errore."""
        return {
            "content": f"Errore nella formattazione: {error}",
            "format": "error",
            "answer": f"Si è verificato un errore: {error}",
            "error": error
        }


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il nodo Response Formatter."""
    processor = ResponseFormatterProcessor()
    return await processor.process(context)
