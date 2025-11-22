from typing import Dict, Any, Optional, List, Union
import json
import time
from datetime import datetime
import logging
import logging
# Logger adapter: prefer local .logger, fallback to PramaIA LogService client, else stdlib
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

class WebhookHandlerProcessor:
    """
    Processore per ricevere e gestire webhook da sistemi esterni.
    Questo nodo è diverso dagli altri perché non viene eseguito in risposta a un input,
    ma viene attivato quando viene ricevuto un webhook. Il sistema PDK crea un'istanza
    di questo processore per ogni endpoint webhook configurato.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Estrai parametri di configurazione
        self.endpoint_path = config.get("endpoint_path", "/webhook/custom")
        self.allowed_methods = config.get("allowed_methods", ["POST"])
        self.secret_token = config.get("secret_token", "")
        self.token_header_name = config.get("token_header_name", "X-Webhook-Token")
        self.response_code = config.get("response_code", 200)
        self.response_body = config.get("response_body", "{\"status\":\"success\"}")
        
        # Stato interno
        self.last_received = None
        self.received_count = 0
        
        # Registra l'endpoint webhook nel sistema PDK
        self._register_webhook_endpoint()
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Questo metodo è una particolarità di questo nodo: non viene chiamato
        con inputs esterni, ma viene utilizzato per produrre output
        quando viene ricevuto un webhook.
        
        Args:
            inputs: Per questo nodo, gli inputs sono i dati del webhook ricevuto
                   dal sistema PDK (non dagli altri nodi)
            
        Returns:
            Dizionario con il payload, gli headers e altre informazioni del webhook
        """
        # Nota: per questo nodo, gli input vengono forniti dal sistema PDK
        # quando riceve una richiesta webhook all'endpoint configurato
        
        # Estrai i dati del webhook
        payload = inputs.get("payload", {})
        headers = inputs.get("headers", {})
        method = inputs.get("method", "")
        query_params = inputs.get("query_params", {})
        
        # Aggiorna lo stato interno
        self.last_received = datetime.now().isoformat()
        self.received_count += 1
        
        # Verifica il token segreto se configurato
        if self.secret_token and self.token_header_name:
            received_token = headers.get(self.token_header_name, "")
            if received_token != self.secret_token:
                self._log_warning(f"Token webhook non valido ricevuto. Atteso: {self.secret_token}, Ricevuto: {received_token}")
                # Nota: in una implementazione reale, potremmo restituire un errore
                # ma per ora elaboriamo comunque il webhook
        
        # Registra la ricezione del webhook
        self._log_info(f"Webhook ricevuto all'endpoint {self.endpoint_path} con metodo {method}")
        self._log_info(f"Headers: {json.dumps(headers)}")
        self._log_info(f"Payload: {json.dumps(payload) if isinstance(payload, dict) else str(payload)}")
        
        # Determina la risposta da inviare
        response = {
            "status_code": self.response_code,
            "body": self.response_body,
            "headers": {"Content-Type": "application/json"}
        }
        
        # Imposta la risposta nel sistema PDK
        self._set_webhook_response(response)
        
        # Genera l'output per il nodo
        timestamp = datetime.now().isoformat()
        return {
            "payload": payload,
            "headers": headers,
            "method": method,
            "timestamp": timestamp
        }
    
    def _register_webhook_endpoint(self) -> None:
        """
        Registra l'endpoint webhook nel sistema PDK.
        In una implementazione reale, questa funzione comunicherà con il sistema PDK
        per registrare l'endpoint webhook.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema PDK
        endpoint_info = {
            "path": self.endpoint_path,
            "methods": self.allowed_methods,
            "node_id": self.node_id
        }
        self._log_info(f"Registrazione endpoint webhook: {json.dumps(endpoint_info)}")
        # In una implementazione reale, chiameremmo una funzione del sistema PDK
    
    def _set_webhook_response(self, response: Dict[str, Any]) -> None:
        """
        Imposta la risposta da inviare al client che ha inviato il webhook.
        In una implementazione reale, questa funzione comunicherà con il sistema PDK
        per impostare la risposta.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema PDK
        self._log_info(f"Impostazione risposta webhook: {json.dumps(response)}")
        # In una implementazione reale, chiameremmo una funzione del sistema PDK
    
    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        try:
            log_warning(f"[WebhookHandlerProcessor] ATTENZIONE: {message}")
        except Exception:
            pass
    
    def _log_info(self, message: str) -> None:
        """
        Registra un messaggio informativo.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        try:
            log_info(f"[WebhookHandlerProcessor] INFO: {message}")
        except Exception:
            pass
