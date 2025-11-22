import logging
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

class RagPromptBuilderProcessor:
    """
    Processore per costruire un prompt per LLM arricchito con contesto recuperato.
    Supporta vari formati di output e personalizzazione del prompt.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Estrai parametri di configurazione
        self.prompt_template = config.get("prompt_template", 
            "Usa solo le seguenti informazioni per rispondere alla domanda. "
            "Se non conosci la risposta, dì semplicemente che non lo sai.\n\n"
            "Contesto:\n{{context}}\n\n"
            "Domanda: {{query}}\n"
            "Risposta:"
        )
        
        self.system_message_template = config.get("system_message_template", 
            "Sei un assistente AI utile che risponde alle domande basandosi esclusivamente sul contesto fornito."
        )
        
        self.context_format = config.get("context_format", "numbered")
        self.max_context_length = config.get("max_context_length", 4000)
        self.include_metadata = config.get("include_metadata", False)
        self.output_format = config.get("output_format", "both")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora l'input e costruisce un prompt arricchito con contesto.
        
        Args:
            inputs: Dizionario con query, documenti di contesto e messaggio di sistema opzionale
            
        Returns:
            Dizionario con il prompt e/o i messaggi formattati
        """
        if "query" not in inputs:
            raise ValueError("Input 'query' richiesto ma non fornito")
        
        if "context_documents" not in inputs:
            raise ValueError("Input 'context_documents' richiesto ma non fornito")
        
        query = inputs["query"]
        context_documents = inputs["context_documents"]
        system_message = inputs.get("system_message", self.system_message_template)
        
        # Verifica che i documenti di contesto siano validi
        if not isinstance(context_documents, list):
            raise ValueError("L'input 'context_documents' deve essere una lista")
        
        # Formatta il contesto
        formatted_context = self._format_context(context_documents)
        
        # Tronca il contesto se necessario
        if len(formatted_context) > self.max_context_length:
            self._log_warning(f"Contesto troppo lungo ({len(formatted_context)} caratteri), troncato a {self.max_context_length} caratteri")
            formatted_context = formatted_context[:self.max_context_length] + "..."
        
        # Costruisci il prompt
        prompt = self.prompt_template
        prompt = prompt.replace("{{context}}", formatted_context)
        prompt = prompt.replace("{{query}}", query)
        
        # Costruisci i messaggi
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        # Prepara l'output in base al formato richiesto
        result = {}
        
        if self.output_format in ["text", "both"]:
            result["prompt"] = prompt
        
        if self.output_format in ["messages", "both"]:
            result["messages"] = messages
        
        return result
    
    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Formatta i documenti di contesto in base al formato selezionato.
        
        Args:
            documents: Lista di documenti di contesto
            
        Returns:
            Stringa formattata con il contesto
        """
        if not documents:
            return "Nessun documento di contesto disponibile."
        
        formatted_texts = []
        
        for i, doc in enumerate(documents):
            # Estrai il testo dal documento
            if isinstance(doc, dict) and "text" in doc:
                text = doc["text"]
            elif isinstance(doc, dict) and "content" in doc:
                text = doc["content"]
            elif isinstance(doc, str):
                text = doc
            else:
                self._log_warning(f"Formato documento non supportato: {type(doc)}")
                continue
            
            # Formatta il testo in base al formato selezionato
            if self.context_format == "numbered":
                formatted_text = f"{i+1}. {text}"
            elif self.context_format == "newline":
                formatted_text = text
            elif self.context_format == "bullet":
                formatted_text = f"• {text}"
            elif self.context_format == "paragraph":
                formatted_text = text
            else:
                # Default: numerato
                formatted_text = f"{i+1}. {text}"
            
            # Aggiungi metadati se richiesto
            if self.include_metadata and isinstance(doc, dict) and "metadata" in doc:
                metadata = doc["metadata"]
                if isinstance(metadata, dict):
                    # Formatta i metadati come testo
                    metadata_text = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
                    formatted_text += f" [Fonte: {metadata_text}]"
            
            formatted_texts.append(formatted_text)
        
        # Unisci i testi formattati
        if self.context_format == "paragraph":
            # Per il formato paragrafo, unisci con doppi newline
            return "\n\n".join(formatted_texts)
        elif self.context_format == "newline":
            # Per il formato newline, unisci con singoli newline
            return "\n".join(formatted_texts)
        else:
            # Per altri formati (numerato, bullet), unisci con newline
            return "\n".join(formatted_texts)
    
    def _log_info(self, message: str) -> None:
        """
        Registra un messaggio informativo.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema di logging
        try:
            log_info(f"[RagPromptBuilderProcessor] INFO: {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema di logging
        try:
            log_warning(f"[RagPromptBuilderProcessor] ATTENZIONE: {message}")
        except Exception:
            pass
