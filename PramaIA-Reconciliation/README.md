# PramaIA-Reconciliation

Servizio di riconciliazione vectorstore per l'ecosistema PramaIA.

## Funzionalità

- **Riconciliazione automatica**: Sincronizzazione pianificata tra filesystem e vectorstore
- **Riconciliazione manuale**: Avvio on-demand tramite API
- **Configurazione flessibile**: Impostazioni personalizzabili per scheduler e performance
- **Monitoraggio**: Status e cronologia delle riconciliazioni
- **API REST**: Endpoint completi per integrazione

## Avvio

```bash
# Installa dipendenze
pip install -r requirements.txt

# Avvia il servizio
python main.py
```

Il servizio sarà disponibile su http://localhost:8091

## API Endpoints

- `GET /health` - Health check
- `GET /reconciliation/status` - Status riconciliazione
- `POST /reconciliation/start` - Avvia riconciliazione
- `GET /settings` - Ottieni impostazioni
- `POST /settings` - Aggiorna impostazioni

## Configurazione

Modifica il file `.env` per personalizzare:
- Porta del servizio
- Orario riconciliazione pianificata
- Thread workers e batch size