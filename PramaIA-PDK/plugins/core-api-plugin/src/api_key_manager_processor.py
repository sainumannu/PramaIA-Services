from typing import Dict, Any, Optional, List, Union
import json
import logging

class ApiKeyManagerProcessor:
    """
    Processore per gestire e fornire chiavi API in modo sicuro.
    Fornisce chiavi API e configurazioni di autenticazione per altri nodi.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Estrai parametri di configurazione
        self.api_service = config.get("api_service", "")
        self.default_key_name = config.get("default_key_name", "")
        self.key_location = config.get("key_location", "header")
        self.header_name = config.get("header_name", "Authorization")
        self.header_prefix = config.get("header_prefix", "")
        self.query_param_name = config.get("query_param_name", "api_key")
        self.body_field_name = config.get("body_field_name", "api_key")
        self.store_keys = config.get("store_keys", {})
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora l'input e fornisce la chiave API e la configurazione di autenticazione.
        
        Args:
            inputs: Dizionario con il nome della chiave API (opzionale)
            
        Returns:
            Dizionario con la chiave API, gli headers e la configurazione di autenticazione
        """
        # Determina quale chiave API utilizzare
        key_name = inputs.get("key_name", self.default_key_name)
        
        if not key_name:
            if len(self.store_keys) == 1:
                # Se c'è solo una chiave, usala
                key_name = list(self.store_keys.keys())[0]
            else:
                raise ValueError("Nome chiave API non specificato e nessuna chiave predefinita configurata")
        
        # Ottieni la chiave API
        if key_name not in self.store_keys:
            raise ValueError(f"Chiave API '{key_name}' non trovata nella configurazione")
        
        api_key = self.store_keys[key_name]
        
        # Crea gli headers in base alla configurazione
        headers = {}
        if self.key_location == "header":
            header_value = api_key
            if self.header_prefix:
                header_value = f"{self.header_prefix}{api_key}"
            headers[self.header_name] = header_value
        
        # Crea la configurazione di autenticazione per altri nodi
        auth_config = {
            "type": self._get_auth_type(),
            "api_service": self.api_service,
            "key_name": key_name
        }
        
        # Aggiungi parametri specifici in base al tipo di autenticazione
        if self.key_location == "header":
            auth_config["header_name"] = self.header_name
            auth_config["header_value"] = headers[self.header_name]
        elif self.key_location == "query":
            auth_config["query_param_name"] = self.query_param_name
            auth_config["query_param_value"] = api_key
        elif self.key_location == "body":
            auth_config["body_field_name"] = self.body_field_name
            auth_config["body_field_value"] = api_key
        elif self.key_location == "basic_auth":
            auth_config["username"] = key_name
            auth_config["password"] = api_key
        elif self.key_location == "bearer_token":
            auth_config["token"] = api_key
        
        # Prepara l'output
        return {
            "api_key": api_key,
            "headers": headers,
            "auth_config": auth_config
        }
    
    def _get_auth_type(self) -> str:
        """
        Determina il tipo di autenticazione in base alla configurazione.
        
        Returns:
            Stringa con il tipo di autenticazione
        """
        if self.key_location == "header":
            if self.header_name.lower() == "authorization":
                if self.header_prefix.lower().startswith("bearer"):
                    return "bearer"
                elif self.header_prefix.lower().startswith("basic"):
                    return "basic"
            return "api_key"
        elif self.key_location == "query":
            return "api_key"
        elif self.key_location == "body":
            return "api_key"
        elif self.key_location == "basic_auth":
            return "basic"
        elif self.key_location == "bearer_token":
            return "bearer"
        else:
            return "custom"
    
    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
    logging.getLogger(__name__).warning(f"[ApiKeyManagerProcessor] ATTENZIONE: {message}")
    
    def _log_info(self, message: str) -> None:
        """
        Registra un messaggio informativo.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
    logging.getLogger(__name__).info(f"[ApiKeyManagerProcessor] INFO: {message}")
