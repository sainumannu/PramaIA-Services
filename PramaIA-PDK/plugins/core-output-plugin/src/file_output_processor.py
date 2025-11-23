import os
import json
import logging
from typing import Dict, Any, Optional

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

class FileOutputProcessor:
    """
    Processore per il nodo di output su file.
    Salva il contenuto in un file specificato.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        self.default_filename = config.get("default_filename", "output.txt")
        self.directory = config.get("directory", "outputs")
        self.overwrite = config.get("overwrite", True)
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora l'input e salva il contenuto in un file.
        """
        log_info("[FileOutputProcessor] INGRESSO nodo: process")
        try:
            if "content" not in inputs:
                raise ValueError("Input 'content' richiesto ma non fornito")
            content = inputs["content"]
            filename = inputs.get("filename", self.default_filename)
            os.makedirs(self.directory, exist_ok=True)
            filepath = os.path.join(self.directory, filename)
            if os.path.exists(filepath) and not self.overwrite:
                base_name, extension = os.path.splitext(filename)
                counter = 1
                while os.path.exists(filepath):
                    new_filename = f"{base_name}_{counter}{extension}"
                    filepath = os.path.join(self.directory, new_filename)
                    counter += 1
            write_mode = "w"
            if isinstance(content, bytes):
                write_mode = "wb"
            elif not isinstance(content, str):
                content = json.dumps(content, indent=2)
            with open(filepath, write_mode) as f:
                f.write(content)
            abs_filepath = os.path.abspath(filepath)
            log_info(f"[FileOutputProcessor] USCITA nodo (successo): File salvato in {abs_filepath}")
            return {
                "path": abs_filepath
            }
        except Exception as e:
            log_error(f"[FileOutputProcessor] USCITA nodo (errore): {str(e)}")
            raise
    
    def _log_debug(self, message: str) -> None:
        """
        Registra un messaggio di debug.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
    log_debug(f"[FileOutputProcessor] {message}")
