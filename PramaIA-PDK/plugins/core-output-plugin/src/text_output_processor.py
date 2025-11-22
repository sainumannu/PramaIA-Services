import os
import json
import logging
from typing import Dict, Any

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

        def log_flush():
            try:
                _pl.flush()
            except Exception:
                pass

        def log_close():
            try:
                _pl.close()
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

        def log_flush():
            for h in _logger.handlers:
                try:
                    h.flush()
                except Exception:
                    pass

        def log_close():
            for h in _logger.handlers:
                try:
                    h.close()
                except Exception:
                    pass

class TextOutputProcessor:
    """
    Processore per il nodo di output testuale.
    Visualizza il testo all'utente nel formato specificato.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        self.format = config.get("format", "markdown")
        self.template = config.get("template", "")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora l'input e genera l'output testuale formattato.
        
        Args:
            inputs: Dizionario contenente l'input 'text' e opzionalmente 'title'
            
        Returns:
            Dizionario vuoto dato che questo nodo non ha output
        """
        if "text" not in inputs:
            raise ValueError("Input 'text' richiesto ma non fornito")
        
        text = inputs["text"]
        title = inputs.get("title", "")
        
        # Applica il template se specificato
        if self.template:
            formatted_text = self.template.replace("{{text}}", str(text))
            if "{{title}}" in self.template and title:
                formatted_text = formatted_text.replace("{{title}}", str(title))
        else:
            formatted_text = str(text)
            if title:
                formatted_text = f"{title}\n\n{formatted_text}"
        
        # Prepara l'output per il sistema
        output_data = {
            "type": "text_output",
            "format": self.format,
            "content": formatted_text,
            "title": title if title else None
        }
        
        # Questo output è destinato al sistema per la visualizzazione
        # e non viene passato ad altri nodi
        self._send_output_to_system(output_data)
        
        # Ritorna un dizionario vuoto poiché questo nodo non ha output
        # connettibili ad altri nodi
        return {}
    
    def _send_output_to_system(self, output_data: Dict[str, Any]) -> None:
        """
        Invia l'output al sistema per la visualizzazione.
        In una implementazione reale, questo comunicherà con il sistema PDK
        per visualizzare l'output all'utente.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema PDK
        try:
            log_info(f"[TextOutputProcessor] Output generato: {json.dumps(output_data, indent=2)}")
        except Exception:
            # non bloccare l'esecuzione se il logger fallisce
            pass

        # Qui in una implementazione reale, ci sarebbe una chiamata
        # al sistema PDK per registrare l'output e visualizzarlo all'utente
