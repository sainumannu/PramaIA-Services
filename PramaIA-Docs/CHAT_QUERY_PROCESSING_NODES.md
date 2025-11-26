# Chat Query Processing - Nuovi Nodi RAG

## Overview

Questo documento descrive i nuovi nodi implementati per il sistema di chat query processing di PramaIA. I nodi permettono di elaborare domande degli utenti utilizzando una combinazione intelligente di ricerca semantica e sui metadati.

## Nodi Implementati

### 1. Chat Query Analyzer
**ID**: `chat_query_analyzer`  
**Plugin**: `core-rag-plugin`

Analizza le domande degli utenti per determinare automaticamente la strategia di ricerca ottimale.

**Caratteristiche principali:**
- Identifica parole chiave semantiche vs metadati
- Classifica il tipo di domanda (informational, temporal, procedural, causal, search)
- Valuta la complessità della query
- Determina se serve ricerca semantica, sui metadati, o entrambe
- Calcola punteggi di confidenza per ogni strategia

**Input:**
- `question` (string, required): Domanda dell'utente
- `user_id` (integer, optional): ID dell'utente  
- `session_id` (string, optional): ID della sessione
- `mode` (string, optional): Modalità di elaborazione

**Output:**
- `analysis` (object): Analisi dettagliata della query
- `search_strategy` (object): Strategia di ricerca consigliata

**Configurazione:**
```json
{
  "semantic_keywords": ["contenuto", "parla di", "spiega", "cos'è"],
  "metadata_keywords": ["quando", "creato", "data", "autore"],
  "confidence_threshold_semantic": 0.3,
  "confidence_threshold_metadata": 0.2,
  "default_strategy": "both"
}
```

### 2. Semantic Search
**ID**: `semantic_search`  
**Plugin**: `core-rag-plugin`

Esegue ricerche semantiche interfacciandosi con il VectorstoreService.

**Caratteristiche principali:**
- Connessione diretta al VectorstoreService (localhost:8090)
- Ricerca per similarità semantica del contenuto
- Filtri per punteggio minimo di similarità
- Sistema di fallback per maggiore affidabilità
- Estrazione automatica di snippet rilevanti

**Input:**
- `question` (string, required): Domanda per la ricerca
- `collection` (string, optional): Nome della collezione
- `max_results` (integer, optional): Numero massimo risultati
- `user_id` (integer, optional): ID dell'utente
- `session_id` (string, optional): ID della sessione

**Output:**
- `results` (array): Risultati della ricerca semantica
- `total_found` (integer): Numero totale risultati

**Configurazione:**
```json
{
  "vectorstore_base_url": "http://localhost:8090",
  "default_collection": "documents", 
  "max_results": 5,
  "min_similarity_score": 0.1,
  "timeout": 30,
  "enable_fallback_search": true
}
```

### 3. Metadata Search  
**ID**: `metadata_search`  
**Plugin**: `core-rag-plugin`

Esegue ricerche basate sui metadati dei documenti.

**Caratteristiche principali:**
- Estrazione automatica criteri temporali (date, periodi relativi)
- Riconoscimento tipi di file (PDF, DOC, immagini, etc.)
- Ricerca per autore/creatore
- Filtri per dimensione file
- Filtri per collezione/cartella
- Scoring basato su corrispondenza criteri multipli

**Input:**
- `question` (string, required): Domanda per la ricerca
- `max_results` (integer, optional): Numero massimo risultati
- `user_id` (integer, optional): ID dell'utente
- `session_id` (string, optional): ID della sessione

**Output:**
- `results` (array): Risultati della ricerca sui metadati
- `total_found` (integer): Numero totale risultati
- `criteria` (object): Criteri di ricerca estratti

**Configurazione:**
```json
{
  "vectorstore_base_url": "http://localhost:8090",
  "max_results": 10,
  "timeout": 30,
  "temporal_keywords": {
    "oggi": 0, "ieri": -1, "settimana": -7
  },
  "file_type_mapping": {
    "pdf": [".pdf"], 
    "documento": [".doc", ".docx", ".txt"]
  }
}
```

### 4. Response Aggregator
**ID**: `response_aggregator`  
**Plugin**: `core-rag-plugin`

Combina risultati da ricerche multiple in una risposta coerente.

**Caratteristiche principali:**
- Deduplicazione intelligente dei risultati
- Scoring combinato pesato (semantico + metadati)
- Generazione response in formato detailed o summary
- Template personalizzabili per diversi tipi di risposta
- Estrazione automatica fonti e snippet

**Input:**
- `question` (string, required): Domanda originale
- `search_strategy` (object, optional): Strategia utilizzata
- `semantic_results` (object, optional): Risultati ricerca semantica  
- `metadata_results` (object, optional): Risultati ricerca metadati
- `user_id` (integer, optional): ID dell'utente
- `session_id` (string, optional): ID della sessione

**Output:**
- `response` (string): Risposta finale aggregata
- `documents` (array): Documenti ordinati per rilevanza
- `sources` (array): Informazioni sulle fonti

**Configurazione:**
```json
{
  "max_total_results": 10,
  "semantic_weight": 0.7,
  "metadata_weight": 0.3,
  "enable_deduplication": true,
  "response_format": "detailed",
  "include_sources": true,
  "include_snippets": true
}
```

## Workflow Chat Query Analyzer

Il workflow `chat_query_analyzer_workflow` coordina l'esecuzione di tutti i nodi per processare le domande degli utenti.

**Flusso di esecuzione:**

```
Input → Query Analyzer → [Semantic Search] → Response Aggregator → Output
                      → [Metadata Search] →
```

**Esecuzione condizionale:**
- Semantic Search si attiva solo se `search_strategy.needs_semantic = true`
- Metadata Search si attiva solo se `search_strategy.needs_metadata = true` 
- Response Aggregator aspetta i risultati disponibili (execution parallela)

**Configurazione timeout:**
- Timeout totale: 30 secondi
- Timeout Response Aggregator: 25 secondi
- Retry automatico: 2 tentativi

## Esempi di Utilizzo

### 1. Domanda Semantica
**Input**: "Dimmi tutto sui servizi PramaIA"
**Strategia**: Semantic only
**Risultato**: Ricerca solo semantic search, focus su contenuto

### 2. Domanda Metadati  
**Input**: "Quali documenti sono stati creati oggi?"
**Strategia**: Metadata only
**Risultato**: Ricerca solo sui metadati, filtro per data

### 3. Domanda Ibrida
**Input**: "Trova documenti PDF sui progetti creati questa settimana"  
**Strategia**: Both
**Risultato**: Ricerca semantica ("progetti") + metadata (PDF, settimana)

### 4. Domanda Complessa
**Input**: "Chi ha scritto documenti su intelligenza artificiale nel 2024?"
**Strategia**: Both  
**Risultato**: Semantic ("intelligenza artificiale") + metadata (autore, 2024)

## Testing e Debugging

### Test dei Singoli Nodi

```bash
# Test Chat Query Analyzer
curl -X POST http://localhost:3000/api/nodes/chat_query_analyzer/test \
  -H "Content-Type: application/json" \
  -d '{"question": "Dimmi quando sono stati creati i documenti PDF"}'

# Test Semantic Search  
curl -X POST http://localhost:3000/api/nodes/semantic_search/test \
  -H "Content-Type: application/json" \
  -d '{"question": "servizi PramaIA", "max_results": 3}'

# Test Metadata Search
curl -X POST http://localhost:3000/api/nodes/metadata_search/test \
  -H "Content-Type: application/json" \
  -d '{"question": "documenti creati oggi"}'
```

### Test del Workflow Completo

```bash
# Test workflow chat query
curl -X POST http://localhost:3000/api/workflows/chat_query_analyzer_workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Trova documenti PDF sui progetti PramaIA creati questa settimana",
    "user_id": 1,
    "session_id": "test-session-123"
  }'
```

### Monitoring e Logs

I nodi generano logs strutturati per debugging:

```
[ChatQueryAnalyzer] Strategia determinata: both (semantic: true, metadata: true)
[SemanticSearch] Ricerca completata: 5 risultati trovati
[MetadataSearch] Ricerca metadati completata: 3 risultati trovati  
[ResponseAggregator] Risposta generata con 7 documenti
```

## Integrazione con Chat Server

Per integrare con il chat server, il trigger `chat_query` deve essere configurato per utilizzare il workflow:

```json
{
  "name": "Chat Query Processing",
  "event_type": "chat_query", 
  "linked_workflow_id": "chat_query_analyzer_workflow",
  "execution_mode": "synchronous",
  "timeout_seconds": 30
}
```

Il server chat invocherà il workflow tramite l'EventSource:

```python
# Nel chat server
result = await chat_event_source.emit_chat_query_event(
    user_id=user.id,
    session_id=session.id, 
    question=user_question
)

response = result.get("response", "")
sources = result.get("sources", [])
```

## Troubleshooting

### Problemi Comuni

1. **VectorstoreService non raggiungibile**
   - Verificare che sia attivo su localhost:8090
   - Controllare configurazione `vectorstore_base_url`

2. **Nessun risultato trovato**
   - Ridurre `min_similarity_score` per semantic search
   - Verificare che esistano documenti nel VectorstoreService
   - Controllare criteri metadata estratti

3. **Timeout del workflow**  
   - Aumentare `timeout_seconds` nel workflow
   - Ottimizzare configurazione nodi (max_results più bassi)

4. **Risultati di bassa qualità**
   - Aggiustare pesi in Response Aggregator
   - Migliorare keywords in Query Analyzer
   - Abilitare deduplicazione

### Debug Avanzato

Per debug dettagliato, abilitare logging debug:

```json
{
  "logging": {
    "level": "DEBUG",
    "include_node_outputs": true,
    "trace_execution": true
  }
}
```

Questo genererà logs completi dell'esecuzione per ogni nodo e permetterà di identificare bottleneck o problemi di configurazione.