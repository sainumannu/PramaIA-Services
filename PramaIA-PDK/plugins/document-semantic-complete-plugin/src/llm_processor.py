"""
LLM Processor

Elabora documenti recuperati usando Large Language Models (OpenAI, Anthropic, etc.).
"""

import logging
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

# Import condizionali per le librerie LLM
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False


class LLMProcessor:
    """Processore per elaborare documenti con Large Language Models."""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Elabora documenti recuperati usando LLM.
        """
        logger.info("[LLMProcessor] INGRESSO nodo: process")
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            retrieved_docs = inputs.get('retrieved_documents', [])
            query_metadata = inputs.get('retrieval_metadata', {})
            original_query = query_metadata.get('query_text', '')
            if not retrieved_docs:
                logger.warning("[LLMProcessor] Nessun documento fornito per l'elaborazione LLM")
                return self._create_empty_response("Nessun documento trovato per elaborare la query.")
            if not original_query:
                logger.warning("[LLMProcessor] Query originale mancante")
                original_query = "Riassumi e analizza i documenti forniti."
            provider = config.get('provider', 'openai')
            model = config.get('model', 'gpt-3.5-turbo')
            max_tokens = config.get('max_tokens', 1000)
            temperature = config.get('temperature', 0.7)
            system_prompt = config.get('system_prompt', self._get_default_system_prompt())
            await self._initialize_llm_client(provider, config)
            documents_context = self._prepare_documents_context(retrieved_docs)
            user_prompt = self._create_user_prompt(original_query, documents_context, query_metadata)
            llm_response = await self._generate_llm_response(
                provider=provider,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            logger.info(f"[LLMProcessor] USCITA nodo (successo): Risposta LLM generata usando {provider}/{model}")
            return {
                "status": "success",
                "llm_response": llm_response,
                "processing_metadata": {
                    "provider": provider,
                    "model": model,
                    "original_query": original_query,
                    "documents_processed": len(retrieved_docs),
                    "response_length": len(llm_response.get('content', '')),
                    "total_tokens": llm_response.get('usage', {}).get('total_tokens', 0)
                }
            }
        except Exception as e:
            logger.error(f"[LLMProcessor] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "llm_response": self._create_error_response(str(e)),
                "processing_metadata": {
                    "provider": "error",
                    "model": "none",
                    "original_query": "",
                    "documents_processed": 0
                }
            }
    
    async def _initialize_llm_client(self, provider: str, config: Dict[str, Any]):
        """Inizializza il client LLM specifico."""
        if provider == "openai" and OPENAI_AVAILABLE and openai:
            api_key = config.get('openai_api_key', '')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("✅ Client OpenAI inizializzato")
            else:
                logger.warning("⚠️ OpenAI API key mancante")
                
        elif provider == "anthropic" and ANTHROPIC_AVAILABLE and anthropic:
            api_key = config.get('anthropic_api_key', '')
            if api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                logger.info("✅ Client Anthropic inizializzato")
            else:
                logger.warning("⚠️ Anthropic API key mancante")
                
        elif provider == "mock":
            logger.info("🔄 Usando mock LLM per testing")
        else:
            logger.warning(f"⚠️ Provider {provider} non supportato o non disponibile")
    
    def _prepare_documents_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Prepara il contesto dai documenti recuperati.
        
        Args:
            retrieved_docs: Lista di documenti recuperati
            
        Returns:
            Stringa con il contesto formattato
        """
        if not retrieved_docs:
            return "Nessun documento disponibile."
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            similarity_score = doc.get('similarity_score', 0)
            document_text = doc.get('document', '')
            
            # Limita lunghezza del documento per evitare token overflow
            if len(document_text) > 1000:
                document_text = document_text[:1000] + "..."
            
            context_parts.append(
                f"DOCUMENTO {i} (Rilevanza: {similarity_score:.2f}):\n{document_text}\n"
            )
        
        return "\n".join(context_parts)
    
    def _create_user_prompt(self, query: str, documents_context: str, 
                          query_metadata: Dict[str, Any]) -> str:
        """
        Crea il prompt utente completo.
        
        Args:
            query: Query originale dell'utente
            documents_context: Contesto dai documenti
            query_metadata: Metadati della query
            
        Returns:
            Prompt formattato per il LLM
        """
        prompt = f"""Basandoti sui seguenti documenti, rispondi alla domanda dell'utente.

DOMANDA DELL'UTENTE:
{query}

DOCUMENTI DI RIFERIMENTO:
{documents_context}

ISTRUZIONI:
- Rispondi in modo accurato basandoti solo sui documenti forniti
- Se la risposta non è presente nei documenti, indica chiaramente questa limitazione
- Cita i documenti più rilevanti quando possibile
- Fornisci una risposta chiara e ben strutturata
- Se richiesto, fornisci dettagli aggiuntivi o esempi dai documenti

RISPOSTA:"""
        
        return prompt
    
    async def _generate_llm_response(self, provider: str, model: str, 
                                   system_prompt: str, user_prompt: str,
                                   max_tokens: int, temperature: float) -> Dict[str, Any]:
        """
        Genera risposta usando il provider LLM specificato.
        
        Args:
            provider: Provider LLM (openai, anthropic, mock)
            model: Nome del modello
            system_prompt: Prompt di sistema
            user_prompt: Prompt utente
            max_tokens: Numero massimo di token
            temperature: Temperatura per la generazione
            
        Returns:
            Risposta del LLM con metadati
        """
        if provider == "openai" and self.openai_client:
            return await self._generate_openai_response(
                model, system_prompt, user_prompt, max_tokens, temperature
            )
        elif provider == "anthropic" and self.anthropic_client:
            return await self._generate_anthropic_response(
                model, system_prompt, user_prompt, max_tokens, temperature
            )
        else:
            return self._generate_mock_response(user_prompt)
    
    async def _generate_openai_response(self, model: str, system_prompt: str,
                                      user_prompt: str, max_tokens: int, 
                                      temperature: float) -> Dict[str, Any]:
        """Genera risposta usando OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": model,
                "provider": "openai",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Errore OpenAI: {str(e)}")
            return self._generate_mock_response(user_prompt, f"Errore OpenAI: {str(e)}")
    
    async def _generate_anthropic_response(self, model: str, system_prompt: str,
                                         user_prompt: str, max_tokens: int,
                                         temperature: float) -> Dict[str, Any]:
        """Genera risposta usando Anthropic."""
        try:
            response = self.anthropic_client.messages.create(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "content": response.content[0].text,
                "model": model,
                "provider": "anthropic",
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Errore Anthropic: {str(e)}")
            return self._generate_mock_response(user_prompt, f"Errore Anthropic: {str(e)}")
    
    def _generate_mock_response(self, user_prompt: str, error_msg: str = "") -> Dict[str, Any]:
        """Genera una risposta mock per testing."""
        if error_msg:
            content = f"Mock LLM Response (Errore: {error_msg})\n\n"
        else:
            content = "Mock LLM Response\n\n"
            
        content += f"""Basandoti sui documenti forniti, posso rispondere alla tua domanda.

Questa è una risposta generata dal sistema mock per scopi di testing. 
In un ambiente di produzione, questa risposta sarebbe generata da un vero modello di linguaggio (OpenAI GPT, Anthropic Claude, etc.).

I documenti analizzati contengono informazioni rilevanti per la tua query, e questa risposta dovrebbe:
1. Essere accurata e basata sui contenuti forniti
2. Citare le fonti quando appropriato
3. Fornire una struttura chiara e comprensibile
4. Indicare eventuali limitazioni delle informazioni disponibili

Prompt ricevuto: {user_prompt[:200]}{'...' if len(user_prompt) > 200 else ''}
"""
        
        return {
            "content": content,
            "model": "mock-llm",
            "provider": "mock",
            "usage": {
                "prompt_tokens": len(user_prompt.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(user_prompt.split()) + len(content.split())
            }
        }
    
    def _get_default_system_prompt(self) -> str:
        """Restituisce il prompt di sistema predefinito."""
        return """Sei un assistente AI specializzato nell'analisi di documenti. 
Il tuo compito è rispondere alle domande degli utenti basandoti esclusivamente sui documenti forniti.

REGOLE:
- Rispondi solo basandoti sui documenti forniti
- Se le informazioni non sono disponibili, dillo chiaramente
- Cita i documenti quando possibile
- Fornisci risposte accurate e ben strutturate
- Se richiesto, fornisci dettagli o esempi dai documenti
- Mantieni un tono professionale e utile"""
    
    def _create_empty_response(self, message: str) -> Dict[str, Any]:
        """Crea una risposta vuota con messaggio."""
        return {
            "content": message,
            "model": "none",
            "provider": "none",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }
    
    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Crea una risposta di errore."""
        return {
            "content": f"Errore nell'elaborazione: {error}",
            "model": "error",
            "provider": "error",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il nodo LLM Processor."""
    processor = LLMProcessor()
    return await processor.process(context)
