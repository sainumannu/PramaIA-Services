# Webhook Event Source

Event source per ricevere webhook HTTP e triggerare workflow automaticamente.

## Caratteristiche

- **Server HTTP asincrono** con supporto multi-endpoint
- **Autenticazione** con signature verification (GitHub-style)
- **Rate limiting** per IP per prevenire abusi
- **Content-Type filtering** per validazione payload
- **Logging configurabile** per debugging e monitoring
- **Gestione errori robusta** con retry e fallback

## Configurazione

### Endpoint Base
```json
{
  "port": 8080,
  "host": "0.0.0.0",
  "endpoints": [
    {
      "path": "/webhook",
      "methods": ["POST"],
      "auth_required": false
    }
  ]
}
```

### Endpoint con Autenticazione (GitHub-style)
```json
{
  "path": "/github/webhook",
  "methods": ["POST"],
  "auth_required": true,
  "secret_token": "your_secret_token",
  "signature_header": "X-Hub-Signature-256"
}
```

### Rate Limiting
```json
{
  "rate_limiting": {
    "enabled": true,
    "requests_per_minute": 60,
    "burst_size": 10
  }
}
```

## Eventi Generati

### webhook_received
Generato quando un webhook valido viene ricevuto.

**Output**:
- `webhook_id`: ID univoco del webhook
- `method`: Metodo HTTP utilizzato
- `url_path`: Percorso URL chiamato
- `headers`: Headers HTTP ricevuti
- `payload`: Payload JSON del webhook
- `query_params`: Parametri query URL
- `source_ip`: IP del mittente
- `received_at`: Timestamp ISO ricezione
- `signature_valid`: Validità signature (se abilitata)

### webhook_validation_failed
Generato quando un webhook fallisce la validazione.

**Output**:
- `webhook_id`: ID del tentativo
- `failure_reason`: Motivo del fallimento
- `source_ip`: IP del mittente
- `failed_at`: Timestamp del fallimento
- `headers`: Headers della richiesta fallita

## Testing

### Avvio Standalone
```bash
cd webhook-event-source
pip install -r requirements.txt
python src/event_source.py
```

### Test con curl
```bash
# Test endpoint base
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "timestamp": "2025-08-03T10:30:00Z"}'

# Test endpoint con signature
curl -X POST http://localhost:8080/github/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=<calculated_signature>" \
  -d '{"action": "push", "repository": {"name": "test-repo"}}'
```

## Use Cases

1. **GitHub Webhooks**: Triggera workflow su push, PR, issues
2. **Stripe Webhooks**: Processa eventi di pagamento
3. **Slack/Discord**: Risposta a comandi e eventi
4. **CI/CD Integration**: Deploy automatici e notifiche
5. **Monitoring Alerts**: Processa alert da sistemi esterni

## Sicurezza

- Signature verification con HMAC-SHA256
- Rate limiting per IP
- Content-Type validation
- Request size limits
- Logging per audit trail
