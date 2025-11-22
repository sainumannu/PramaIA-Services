# Core API Plugin

Questo plugin fornisce i nodi per interagire con API esterne nei workflow PramaIA. I nodi consentono di effettuare richieste HTTP, gestire chiavi API e ricevere webhook.

## Nodi Inclusi

### HTTP Request
Effettua richieste HTTP verso API esterne.

**Input:**
- `url` (obbligatorio): URL dell'endpoint API
- `headers` (opzionale): Headers HTTP
- `params` (opzionale): Parametri query string
- `body` (opzionale): Corpo della richiesta

**Output:**
- `response`: Risposta completa dell'API
- `data`: Dati estratti dalla risposta
- `status`: Status code HTTP

**Configurazione:**
- `method`: Metodo HTTP da utilizzare (GET, POST, PUT, DELETE, ecc.)
- `timeout`: Timeout della richiesta in secondi
- `retry_count`: Numero di tentativi in caso di errore
- `follow_redirects`: Segui automaticamente i redirect HTTP
- `content_type`: Content-Type per la richiesta
- `error_on_failure`: Genera un errore se la richiesta fallisce
- `default_headers`: Headers HTTP di default
- `authentication`: Configurazione per l'autenticazione

### API Key Manager
Gestisce e fornisce chiavi API in modo sicuro.

**Input:**
- `key_name` (opzionale): Nome della chiave API da utilizzare

**Output:**
- `api_key`: Chiave API richiesta
- `headers`: Headers HTTP preconfigurati con la chiave API
- `auth_config`: Configurazione completa per l'autenticazione

**Configurazione:**
- `api_service`: Nome del servizio API
- `default_key_name`: Nome della chiave API di default
- `key_location`: Dove inserire la chiave API (header, query, ecc.)
- `header_name`: Nome dell'header HTTP
- `header_prefix`: Prefisso per il valore dell'header
- `query_param_name`: Nome del parametro query
- `body_field_name`: Nome del campo nel body
- `store_keys`: Mappa di nomi di chiavi e valori

### Webhook Handler
Riceve e gestisce webhook da sistemi esterni.

**Input:**
- Nessun input richiesto (viene attivato dalle richieste webhook)

**Output:**
- `payload`: Payload ricevuto dal webhook
- `headers`: Headers HTTP ricevuti
- `method`: Metodo HTTP utilizzato
- `timestamp`: Timestamp di ricezione

**Configurazione:**
- `endpoint_path`: Percorso dell'endpoint webhook
- `allowed_methods`: Metodi HTTP consentiti
- `secret_token`: Token segreto per validare il webhook
- `token_header_name`: Nome dell'header HTTP per il token
- `response_code`: Codice HTTP da restituire
- `response_body`: Corpo della risposta da restituire

## Installazione

Questo plugin è parte della suite di plugin core di PramaIA e viene installato automaticamente con il PDK.

Per garantire il corretto funzionamento, sono richieste le seguenti dipendenze:
```
pip install aiohttp pydantic
```

## Utilizzo

I nodi possono essere aggiunti ai workflow tramite l'interfaccia di PramaIA. Per ogni nodo, configurare i parametri necessari in base alle proprie esigenze.

### Esempi

#### Richiesta HTTP
```json
{
  "nodes": {
    "1": {
      "id": "1",
      "type": "http_request",
      "config": {
        "method": "GET",
        "timeout": 30,
        "retry_count": 1,
        "error_on_failure": true
      }
    }
  },
  "edges": {
    "1": {
      "source": "altroNodo",
      "sourceHandle": "output",
      "target": "1",
      "targetHandle": "url"
    }
  }
}
```

#### Gestione Chiavi API
```json
{
  "nodes": {
    "1": {
      "id": "1",
      "type": "api_key_manager",
      "config": {
        "api_service": "OpenAI",
        "key_location": "header",
        "header_name": "Authorization",
        "header_prefix": "Bearer ",
        "store_keys": {
          "default": "sk-XXXXXXXXXX"
        }
      }
    },
    "2": {
      "id": "2",
      "type": "http_request",
      "config": {
        "method": "POST",
        "content_type": "application/json"
      }
    }
  },
  "edges": [
    {
      "source": "1",
      "sourceHandle": "headers",
      "target": "2",
      "targetHandle": "headers"
    }
  ]
}
```

#### Configurazione Webhook
```json
{
  "nodes": {
    "1": {
      "id": "1",
      "type": "webhook_handler",
      "config": {
        "endpoint_path": "/webhook/github",
        "allowed_methods": ["POST"],
        "secret_token": "my-secret-token",
        "token_header_name": "X-Hub-Signature"
      }
    }
  }
}
```

## Dipendenze

- Python 3.8+
- aiohttp: per le richieste HTTP asincrone
- pydantic: per la validazione dei dati

## Sviluppo

Per estendere la funzionalità di un nodo:

1. Modifica il file del processore corrispondente in `src/`
2. Aggiorna il file `plugin.json` se necessario
3. Ricarica il plugin nel PDK

---

&copy; 2023-2024 PramaIA Team
