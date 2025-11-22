import asyncio
import logging
import json
import hashlib
import hmac
import time
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict
import sys
import os
import uuid

# HTTP server dependencies
from aiohttp import web, web_request
from aiohttp.web_response import Response
import aiohttp

# Aggiungi il path del PDK per importare le utility
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

try:
    from core.event_source_base import BaseEventSourceProcessor
except ImportError:
    # Fallback per testing locale
    class BaseEventSourceProcessor:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
        
        async def emit_event(self, event_type, data):
            logging.getLogger(__name__).info(f"[EVENT] {event_type}: {json.dumps(data, indent=2)}")
        
        def log_info(self, msg): logging.getLogger(__name__).info(msg)
        def log_warning(self, msg): logging.getLogger(__name__).warning(msg)
        def log_error(self, msg): logging.getLogger(__name__).error(msg)
        def log_debug(self, msg): logging.getLogger(__name__).debug(msg)

    # Adapter logger: prefer local wrapper 'logger', then pramaialog client, otherwise std logging
    try:
        # Prefer relative logger wrapper provided by the PDK/plugin
        from .logger import debug, info, warning, error, flush, close
    except Exception:
        try:
            # Fallback: try the pramaialog client if available in environment
            from pramaialog import PramaIALogger

            _pramaialogger = PramaIALogger()

            def debug(msg, **kwargs):
                _pramaialogger.debug(msg, **kwargs)

            def info(msg, **kwargs):
                _pramaialogger.info(msg, **kwargs)

            def warning(msg, **kwargs):
                _pramaialogger.warning(msg, **kwargs)

            def error(msg, **kwargs):
                _pramaialogger.error(msg, **kwargs)

            def flush():
                try:
                    _pramaialogger.flush()
                except Exception:
                    pass

            def close():
                try:
                    _pramaialogger.close()
                except Exception:
                    pass

        except Exception:
            # Final fallback: use std logging
            import logging as _std_logging

            def debug(msg, **kwargs):
                _std_logging.getLogger(__name__).debug(msg)

            def info(msg, **kwargs):
                _std_logging.getLogger(__name__).info(msg)

            def warning(msg, **kwargs):
                _std_logging.getLogger(__name__).warning(msg)

            def error(msg, **kwargs):
                _std_logging.getLogger(__name__).error(msg)

            def flush():
                return

            def close():
                return

class WebhookEventSource(BaseEventSourceProcessor):
    def __init__(self):
        super().__init__()
        self.app = None
        self.runner = None
        self.site = None
        self.config = {}
        self.rate_limiter = defaultdict(list)  # IP -> list of timestamps
        self.running = False
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inizializza l'event source con la configurazione"""
        try:
            self.config = config
            self.log_info(f"Inizializzando webhook server su porta {config.get('port', 8080)}")
            
            # Crea l'app aiohttp
            self.app = web.Application()
            
            # Configura middleware
            self.app.middlewares.append(self._rate_limit_middleware)
            self.app.middlewares.append(self._logging_middleware)
            
            # Configura routes basati sulla configurazione
            await self._setup_routes()
            
            self.log_info("Webhook Event Source inizializzato correttamente")
            return True
            
        except Exception as e:
            self.log_error(f"Errore durante l'inizializzazione: {e}")
            return False
    
    async def start(self) -> bool:
        """Avvia il server webhook"""
        try:
            if self.running:
                return True
            
            # Avvia il server HTTP
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            host = self.config.get('host', '0.0.0.0')
            port = self.config.get('port', 8080)
            
            self.site = web.TCPSite(self.runner, host, port)
            await self.site.start()
            
            self.running = True
            self.log_info(f"Webhook server avviato su http://{host}:{port}")
            
            # Log degli endpoint disponibili
            for endpoint in self.config.get('endpoints', []):
                path = endpoint['path']
                methods = ', '.join(endpoint.get('methods', ['POST']))
                self.log_info(f"Endpoint disponibile: {methods} {path}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Errore durante l'avvio del server: {e}")
            return False
    
    async def stop(self) -> bool:
        """Ferma il server webhook"""
        try:
            if not self.running:
                return True
            
            self.running = False
            
            if self.site:
                await self.site.stop()
            
            if self.runner:
                await self.runner.cleanup()
            
            self.log_info("Webhook server fermato")
            return True
            
        except Exception as e:
            self.log_error(f"Errore durante lo stop del server: {e}")
            return False
    
    async def cleanup(self):
        """Pulizia risorse"""
        await self.stop()
    
    async def _setup_routes(self):
        """Configura le route basate sulla configurazione"""
        endpoints = self.config.get('endpoints', [])
        
        for endpoint_config in endpoints:
            path = endpoint_config['path']
            methods = endpoint_config.get('methods', ['POST'])
            
            # Crea handler per questo endpoint
            handler = self._create_endpoint_handler(endpoint_config)
            
            # Registra la route per ogni metodo HTTP
            for method in methods:
                self.app.router.add_route(method, path, handler)
    
    def _create_endpoint_handler(self, endpoint_config):
        """Crea un handler per un endpoint specifico"""
        async def handler(request: web_request.Request) -> Response:
            webhook_id = str(uuid.uuid4())
            received_at = datetime.utcnow().isoformat() + "Z"
            
            try:
                # Ottieni informazioni della richiesta
                method = request.method
                url_path = request.path
                headers = dict(request.headers)
                query_params = dict(request.query)
                source_ip = request.remote
                
                # Leggi payload
                payload = {}
                if method in ['POST', 'PUT', 'PATCH']:
                    content_type = request.headers.get('Content-Type', '')
                    
                    # Verifica content-type se configurato
                    if self._should_filter_content_type(endpoint_config, content_type):
                        await self._emit_validation_failed(
                            webhook_id, f"Content-Type non accettato: {content_type}",
                            source_ip, headers
                        )
                        return web.Response(
                            text=f"Content-Type '{content_type}' non accettato",
                            status=415
                        )
                    
                    try:
                        if 'application/json' in content_type:
                            payload = await request.json()
                        elif 'application/x-www-form-urlencoded' in content_type:
                            form_data = await request.post()
                            payload = dict(form_data)
                        else:
                            text_data = await request.text()
                            payload = {"raw_data": text_data}
                    except Exception as e:
                        self.log_warning(f"Errore nel parsing del payload: {e}")
                        payload = {"parse_error": str(e)}
                
                # Verifica autenticazione se richiesta
                signature_valid = True
                if endpoint_config.get('auth_required', False):
                    signature_valid = await self._verify_signature(
                        request, endpoint_config, payload
                    )
                    
                    if not signature_valid:
                        await self._emit_validation_failed(
                            webhook_id, "Signature validation failed",
                            source_ip, headers
                        )
                        return web.Response(text="Unauthorized", status=401)
                
                # Emetti evento webhook_received
                event_data = {
                    "webhook_id": webhook_id,
                    "method": method,
                    "url_path": url_path,
                    "headers": headers,
                    "payload": payload,
                    "query_params": query_params,
                    "source_ip": source_ip,
                    "received_at": received_at,
                    "signature_valid": signature_valid
                }
                
                await self.emit_event("webhook_received", event_data)
                
                return web.Response(
                    text=json.dumps({"status": "success", "webhook_id": webhook_id}),
                    content_type="application/json",
                    status=200
                )
                
            except Exception as e:
                self.log_error(f"Errore nel processing webhook {webhook_id}: {e}")
                return web.Response(text="Internal Server Error", status=500)
        
        return handler
    
    def _should_filter_content_type(self, endpoint_config, content_type):
        """Verifica se il content-type dovrebbe essere filtrato"""
        filters = endpoint_config.get('content_type_filter', [])
        if not filters:
            return False
        
        return not any(filter_type in content_type for filter_type in filters)
    
    async def _verify_signature(self, request, endpoint_config, payload) -> bool:
        """Verifica la signature del webhook"""
        try:
            secret_token = endpoint_config.get('secret_token', '')
            if not secret_token:
                return True  # Nessun token configurato, considera valido
            
            signature_header = endpoint_config.get('signature_header', 'X-Hub-Signature-256')
            signature = request.headers.get(signature_header, '')
            
            if not signature:
                return False
            
            # Calcola signature attesa
            payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
            expected_signature = hmac.new(
                secret_token.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Confronta signature (supporta formati GitHub-style)
            if signature.startswith('sha256='):
                return hmac.compare_digest(signature[7:], expected_signature)
            else:
                return hmac.compare_digest(signature, expected_signature)
                
        except Exception as e:
            self.log_error(f"Errore nella verifica signature: {e}")
            return False
    
    async def _emit_validation_failed(self, webhook_id, reason, source_ip, headers):
        """Emetti evento per validazione fallita"""
        event_data = {
            "webhook_id": webhook_id,
            "failure_reason": reason,
            "source_ip": source_ip,
            "failed_at": datetime.utcnow().isoformat() + "Z",
            "headers": headers
        }
        await self.emit_event("webhook_validation_failed", event_data)
    
    @web.middleware
    async def _rate_limit_middleware(self, request, handler):
        """Middleware per rate limiting"""
        rate_config = self.config.get('rate_limiting', {})
        if not rate_config.get('enabled', True):
            return await handler(request)
        
        client_ip = request.remote
        current_time = time.time()
        requests_per_minute = rate_config.get('requests_per_minute', 60)
        burst_size = rate_config.get('burst_size', 10)
        
        # Pulisci richieste vecchie (oltre 1 minuto)
        self.rate_limiter[client_ip] = [
            req_time for req_time in self.rate_limiter[client_ip]
            if current_time - req_time < 60
        ]
        
        # Verifica rate limit
        recent_requests = len(self.rate_limiter[client_ip])
        if recent_requests >= requests_per_minute:
            return web.Response(text="Rate limit exceeded", status=429)
        
        # Aggiungi questa richiesta al tracking
        self.rate_limiter[client_ip].append(current_time)
        
        return await handler(request)
    
    @web.middleware
    async def _logging_middleware(self, request, handler):
        """Middleware per logging richieste"""
        log_config = self.config.get('logging', {})
        if not log_config.get('log_requests', True):
            return await handler(request)
        
        start_time = time.time()
        
        try:
            response = await handler(request)
            duration = (time.time() - start_time) * 1000  # in millisecondi
            
            log_msg = f"{request.method} {request.path} - {response.status} - {duration:.2f}ms - {request.remote}"
            self.log_info(log_msg)
            
            return response
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_msg = f"{request.method} {request.path} - ERROR - {duration:.2f}ms - {request.remote} - {str(e)}"
            self.log_error(log_msg)
            raise

# Entry point per testing
if __name__ == "__main__":
    async def main():
        # Configurazione di test
        config = {
            "port": 8080,
            "host": "localhost",
            "endpoints": [
                {
                    "path": "/test/webhook",
                    "methods": ["POST", "GET"],
                    "auth_required": False,
                    "content_type_filter": ["application/json"]
                },
                {
                    "path": "/github/webhook",
                    "methods": ["POST"],
                    "auth_required": True,
                    "secret_token": "test_secret_123",
                    "signature_header": "X-Hub-Signature-256"
                }
            ],
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 30,
                "burst_size": 5
            },
            "logging": {
                "log_requests": True,
                "log_payloads": False,
                "log_level": "INFO"
            }
        }
        
        webhook_source = WebhookEventSource()
        
        try:
            await webhook_source.initialize(config)
            await webhook_source.start()
            
            logging.getLogger(__name__).info("Webhook server in esecuzione...")
            logging.getLogger(__name__).info("Test endpoints:")
            logging.getLogger(__name__).info("  POST http://localhost:8080/test/webhook")
            logging.getLogger(__name__).info("  POST http://localhost:8080/github/webhook")
            logging.getLogger(__name__).info("Premi Ctrl+C per fermare")
            
            # Mantieni attivo
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logging.getLogger(__name__).info("\nFermando server...")
        finally:
            await webhook_source.cleanup()
    
    asyncio.run(main())
