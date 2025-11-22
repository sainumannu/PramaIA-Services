# Changelog: PramaIA-LogService

Questo file contiene tutte le modifiche significative apportate al progetto PramaIA-LogService.

## [1.3.0] - 2025-09-05

### Aggiunto
- Migliorata la rilevazione dei log lifecycle con un algoritmo più flessibile
- Nuovo script di test `test_lifecycle_log_detection.py` per verificare la corretta rilevazione
- Documentazione aggiuntiva: `LIFECYCLE_LOG_DETECTION_UPDATE.md`

### Modificato
- Aggiornato `search_router.py` per cercare "lifecycle" in qualsiasi parte dei dettagli del log
- Migliorato l'algoritmo in `log_manager.py` per rilevare più efficacemente i log lifecycle
- Espansa la documentazione con esempi di come i log lifecycle vengono rilevati

## [1.2.0] - 2025-08-19

### Aggiunto
- Gestione migliorata dei valori null e undefined nei dettagli dei log
- Endpoint `/api/logs/{log_id}` per ottenere i dettagli completi di un log specifico
- Miglioramento della formattazione JSON nell'interfaccia web
- Script di test avanzati per verificare la gestione di vari tipi di dati nei dettagli
- Nuova documentazione completa: `LOGSERVICE_DOCUMENTAZIONE.md`
- Guida alla risoluzione del problema "undefined": `RISOLUZIONE_PROBLEMA_UNDEFINED.md`

### Modificato
- Migliorata la gestione degli errori durante la serializzazione/deserializzazione JSON in `log_manager.py`
- Aggiornata l'interfaccia web per includere l'API key nelle richieste per i dettagli dei log
- Migliorata la funzione `formatJsonDisplay()` in `search.html` per gestire meglio i valori speciali
- Aggiornato il README con nuove caratteristiche e documentazione

### Risolto
- Risolto il problema dei dettagli di log visualizzati come "undefined" nell'interfaccia web
- Corretti errori di autenticazione nelle richieste API dalla UI
- Risolti problemi di visualizzazione per oggetti vuoti o nulli

## [1.1.0] - 2025-06-15

### Aggiunto
- Funzionalità di compressione automatica dei log vecchi
- Nuova opzione di configurazione per il periodo di retention degli archivi compressi
- Endpoint `/api/logs/stats` per ottenere statistiche sui log
- Nuova pagina nella dashboard per visualizzare le statistiche

### Modificato
- Migliorata la performance della ricerca dei log
- Ottimizzata la struttura del database per ridurre l'uso di spazio

### Risolto
- Risolti problemi di performance con grandi volumi di log
- Corretti errori nella visualizzazione delle date nella dashboard

## [1.0.0] - 2025-03-10

### Aggiunto
- Prima versione stabile del servizio
- API REST per l'invio e la consultazione dei log
- Dashboard web per la visualizzazione e la ricerca dei log
- Sistema di autenticazione basato su API key
- Funzionalità di rotazione e pulizia automatica dei log
- Supporto per la categorizzazione dei log per progetto, livello e modulo
- Client di esempio per l'integrazione con altri servizi
- Documentazione di base
