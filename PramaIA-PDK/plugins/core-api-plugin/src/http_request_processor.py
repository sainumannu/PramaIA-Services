import json
import aiohttp
import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlencode

class HttpRequestProcessor:
    """
    Processore per effettuare richieste HTTP verso API esterne.
    Supporta vari metodi HTTP, autenticazione e gestione delle risposte.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Estrai parametri di configurazione
        self.method = config.get("method", "GET")
        self.timeout = config.get("timeout", 30)
        self.retry_count = config.get("retry_count", 0)
        self.follow_redirects = config.get("follow_redirects", True)
        self.content_type = config.get("content_type", "application/json")
        self.error_on_failure = config.get("error_on_failure", True)
        self.default_headers = config.get("default_headers", {})
        self.authentication = config.get("authentication", {"type": "none"})
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora l'input ed effettua una richiesta HTTP.
        
        Args:
            inputs: Dizionario con url, headers, params e body opzionali
            
        Returns:
            Dizionario con la risposta, i dati e lo status code
        """
        if "url" not in inputs:
            raise ValueError("Input 'url' richiesto ma non fornito")
        
        url = inputs["url"]
        headers = inputs.get("headers", {})
        params = inputs.get("params", {})
        body = inputs.get("body", None)
        
        # Unisci gli headers di default con quelli forniti nell'input
        merged_headers = {**self.default_headers, **headers}
        
        # Aggiungi headers di autenticazione se necessario
        auth_headers = self._get_auth_headers()
        if auth_headers:
            merged_headers.update(auth_headers)
        
        # Aggiungi Content-Type se non presente e c'è un body
        if body is not None and "Content-Type" not in merged_headers:
            merged_headers["Content-Type"] = self.content_type
        
        # Prepara il corpo della richiesta in base al content type
        prepared_body = self._prepare_body(body)
        
        # Parametri per la query string
        # Aggiungi parametri di autenticazione se necessario
        auth_params = self._get_auth_params()
        if auth_params:
            params.update(auth_params)
        
        # Effettua la richiesta HTTP con retry
        response_data = await self._make_request_with_retry(
            url, 
            method=self.method, 
            headers=merged_headers, 
            params=params, 
            data=prepared_body
        )
        
        return response_data
    
    def _prepare_body(self, body: Any) -> Any:
        """
        Prepara il corpo della richiesta in base al content type.
        
        Args:
            body: Corpo della richiesta
            
        Returns:
            Corpo preparato per la richiesta
        """
        if body is None:
            return None
        
        if self.content_type == "application/json":
            if isinstance(body, str):
                # Verifica se è già una stringa JSON
                try:
                    json.loads(body)
                    return body
                except json.JSONDecodeError:
                    # Non è JSON, lo converte
                    return json.dumps({"data": body})
            else:
                # Converte oggetti Python in JSON
                return json.dumps(body)
        
        elif self.content_type == "application/x-www-form-urlencoded":
            if isinstance(body, dict):
                return urlencode(body)
            elif isinstance(body, str):
                return body
            else:
                return urlencode({"data": str(body)})
        
        # Per altri content type, restituisci il body così com'è
        return body
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Genera gli headers per l'autenticazione in base alla configurazione.
        
        Returns:
            Dizionario con gli headers di autenticazione
        """
        auth_type = self.authentication.get("type", "none")
        headers = {}
        
        if auth_type == "none":
            return {}
        
        elif auth_type == "basic":
            username = self.authentication.get("username", "")
            password = self.authentication.get("password", "")
            
            if username and password:
                import base64
                auth_string = f"{username}:{password}"
                encoded = base64.b64encode(auth_string.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
        
        elif auth_type == "bearer":
            token = self.authentication.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        elif auth_type == "api_key":
            api_key = self.authentication.get("api_key", "")
            api_key_name = self.authentication.get("api_key_name", "api_key")
            api_key_location = self.authentication.get("api_key_location", "header")
            
            if api_key and api_key_location == "header":
                headers[api_key_name] = api_key
        
        return headers
    
    def _get_auth_params(self) -> Dict[str, str]:
        """
        Genera i parametri query per l'autenticazione in base alla configurazione.
        
        Returns:
            Dizionario con i parametri di autenticazione
        """
        auth_type = self.authentication.get("type", "none")
        params = {}
        
        if auth_type == "api_key":
            api_key = self.authentication.get("api_key", "")
            api_key_name = self.authentication.get("api_key_name", "api_key")
            api_key_location = self.authentication.get("api_key_location", "header")
            
            if api_key and api_key_location == "query":
                params[api_key_name] = api_key
        
        return params
    
    async def _make_request_with_retry(self, url: str, method: str, headers: Dict, params: Dict, data: Any) -> Dict[str, Any]:
        """
        Effettua una richiesta HTTP con gestione dei retry.
        
        Args:
            url: URL della richiesta
            method: Metodo HTTP
            headers: Headers HTTP
            params: Parametri query string
            data: Corpo della richiesta
            
        Returns:
            Dizionario con la risposta, i dati e lo status code
        """
        retry_count = self.retry_count
        last_error = None
        
        # Timeout in secondi
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        for attempt in range(retry_count + 1):
            if attempt > 0:
                self._log_warning(f"Tentativo {attempt}/{retry_count} dopo errore: {str(last_error)}")
                # Backoff esponenziale: 1s, 2s, 4s, 8s, ...
                await asyncio.sleep(2 ** (attempt - 1))
            
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # Prepara la richiesta in base al metodo
                    if method == "GET":
                        async with session.get(url, headers=headers, params=params, allow_redirects=self.follow_redirects) as response:
                            return await self._process_response(response)
                    
                    elif method == "POST":
                        async with session.post(url, headers=headers, params=params, data=data, allow_redirects=self.follow_redirects) as response:
                            return await self._process_response(response)
                    
                    elif method == "PUT":
                        async with session.put(url, headers=headers, params=params, data=data, allow_redirects=self.follow_redirects) as response:
                            return await self._process_response(response)
                    
                    elif method == "DELETE":
                        async with session.delete(url, headers=headers, params=params, data=data, allow_redirects=self.follow_redirects) as response:
                            return await self._process_response(response)
                    
                    elif method == "PATCH":
                        async with session.patch(url, headers=headers, params=params, data=data, allow_redirects=self.follow_redirects) as response:
                            return await self._process_response(response)
                    
                    elif method == "HEAD":
                        async with session.head(url, headers=headers, params=params, allow_redirects=self.follow_redirects) as response:
                            return await self._process_response(response)
                    
                    elif method == "OPTIONS":
                        async with session.options(url, headers=headers, params=params, allow_redirects=self.follow_redirects) as response:
                            return await self._process_response(response)
                    
                    else:
                        raise ValueError(f"Metodo HTTP non supportato: {method}")
            
            except aiohttp.ClientError as e:
                last_error = e
                if attempt == retry_count:
                    if self.error_on_failure:
                        raise
                    else:
                        return {
                            "response": {
                                "error": str(e),
                                "timestamp": time.time()
                            },
                            "data": None,
                            "status": 0
                        }
    
    async def _process_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """
        Elabora la risposta HTTP.
        
        Args:
            response: Risposta HTTP
            
        Returns:
            Dizionario con la risposta, i dati e lo status code
        """
        status_code = response.status
        
        # Ottieni gli headers
        headers = dict(response.headers)
        
        # Ottieni il contenuto
        try:
            if "application/json" in response.headers.get("Content-Type", "").lower():
                # Risposta JSON
                data = await response.json()
            else:
                # Risposta testuale
                text = await response.text()
                
                # Prova a convertire in JSON, se possibile
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    # Non è JSON, usa il testo
                    data = text
        except Exception as e:
            self._log_error(f"Errore nell'elaborazione della risposta: {e}")
            data = None
        
        # Verifica se la risposta è un errore
        is_error = status_code >= 400
        
        # Se la risposta è un errore e error_on_failure è True, solleva un'eccezione
        if is_error and self.error_on_failure:
            error_message = f"Errore HTTP {status_code}"
            if isinstance(data, dict) and "error" in data:
                error_message += f": {data['error']}"
            elif isinstance(data, str):
                error_message += f": {data}"
            
            self._log_error(error_message)
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=status_code,
                message=error_message,
                headers=response.headers
            )
        
        # Costruisci l'oggetto risposta
        response_obj = {
            "status_code": status_code,
            "headers": headers,
            "is_error": is_error,
            "url": str(response.url),
            "timestamp": time.time()
        }
        
        return {
            "response": response_obj,
            "data": data,
            "status": status_code
        }
    
    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
    logging.getLogger(__name__).warning(f"[HttpRequestProcessor] ATTENZIONE: {message}")
    
    def _log_error(self, message: str) -> None:
        """
        Registra un messaggio di errore.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
    logging.getLogger(__name__).error(f"[HttpRequestProcessor] ERRORE: {message}")
