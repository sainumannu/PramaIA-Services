# PramaIA Ecosistema - Panoramica Generale

## 1. Introduzione

**PramaIA** è una piattaforma modulare per l'elaborazione intelligente di documenti, basata su un'architettura a plugin (PDK) e automazione event-driven. Il sistema è composto da più microservizi che comunicano tramite API REST.

## 2. Architettura dei Microservizi

```
┌──────────────────────────────────────────────────────────────┐
│                     Frontend (React)                          │
│                   http://localhost:3000                       │
└──────────────────────────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│         PramaIAServer (FastAPI) - port 8000                   │
│  • Document Management                                        │
│  • Trigger & Event Processing                                │
│  • Workflow Orchestration                                     │
│  • Microservice Orchestration                                 │
└──────────────────────────────────────────────────────────────┘
             ↓                    ↓                    ↓
    ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐
    │     PDK        │  │  LogService    │  │ VectorstoreService│
    │  port 3001     │  │   port 8081    │  │    port 8090      │
    └────────────────┘  └────────────────┘  └──────────────────┘
             ↓                                      ↓
    ┌────────────────┐                  ┌──────────────────┐
    │   Plugins      │                  │    ChromaDB      │
    │   (Nodes)      │                  │  + SQLite        │
    └────────────────┘                  └──────────────────┘
             ↓
    ┌────────────────┐
    │  Event Sources │
    └────────────────┘
             ↓
    ┌────────────────────────────┐
    │ Document Folder Monitor    │
    │ Agent (port 8001)          │
    └────────────────────────────┘
```

## 3. Componenti Principali

### 3.1 PramaIAServer (Backend FastAPI - port 8000)

**Responsabilità**:
- API REST per gestione documenti
- Orchestrazione dei workflow
- Sistema di trigger (event → workflow)
- Coordinamento tra microservizi

**Struttura**:
```
PramaIAServer/
├── backend/
│   ├── main.py                    # App FastAPI
│   ├── routers/                   # Endpoint organizzati per resource
│   ├── services/                  # Business logic (WorkflowEngine, TriggerService)
│   ├── crud/                      # Database operations
│   ├── models/                    # SQLAlchemy models (Workflow, Trigger, Document, User)
│   ├── db/                        # Database configuration
│   └── utils/                     # Helper functions
└── frontend/
    └── client/                    # React app
```

**Endpoint Critici**:
- `POST /api/documents/upload-with-visibility/` - Upload documenti
- `POST /api/events/process` - Processa eventi generici
- `POST /api/workflows/triggers` - Crea/aggiorna trigger
- `GET /api/workflows` - Lista workflow disponibili
- `POST /api/workflows/execute` - Esegue workflow manualmente

### 3.2 PramaIA-PDK (Plugin Development Kit - port 3001)

**Responsabilità**:
- Server API per nodi di workflow
- API dei plugin disponibili
- Esecuzione dei nodi tramite resolver function

**Componenti**:
```
PramaIA-PDK/
├── server/
│   └── plugin-api-server.js       # Express server espone API plugin
├── plugins/                       # Directory dei plugin
│   ├── core-input-plugin/
│   ├── core-output-plugin/
│   ├── core-llm-plugin/
│   ├── core-rag-plugin/
│   ├── pdf-semantic-complete-plugin/
│   └── [custom-plugins]/
└── src/                           # Core PDK TypeScript
```

**Endpoint API PDK**:
- `GET /api/plugins` - Lista plugin disponibili
- `GET /api/nodes` - Lista nodi con schema (inputs/outputs)
- `POST /api/nodes/:nodeId/execute` - Esegue nodo
- `GET /api/tags` - Statistiche tag system

### 3.3 PramaIA-LogService (Logging Centralizzato - port 8081)

**Responsabilità**:
- Raccolta log centralizzata da tutti i servizi
- API per inviare log strutturati
- Dashboard web per visualizzare log

**Database**: SQLite per log persistenti

### 3.4 PramaIA-VectorstoreService (Ricerca Semantica - port 8090)

**Responsabilità**:
- Gestione embedding dei documenti
- Ricerca semantica su vettori
- Sincronizzazione metadati

**Componenti Dati**:
- **ChromaDB**: Database vettoriale persistente
- **SQLite**: Metadati e tracciamento documenti

### 3.5 Document Folder Monitor Agent (port 8001)

**Responsabilità**:
- Monitoraggio cartelle file system
- Rilevamento cambiamenti (create/modify/delete)
- Sincronizzazione con VectorstoreService
- Event buffering e recovery

**Sincronizzazione Multi-Layer**:
1. **Layer 1 (Event Buffering)**: Buffer locale SQLite per eventi
2. **Layer 2 (Periodic Reconciliation)**: Riconciliazione oraria del file system
3. **Layer 3 (Connection Recovery)**: Sync al ripristino connessione

## 4. Flussi di Dati Principali

### 4.1 Upload e Trigger di Workflow

```
File → REST API Upload
     ↓
Backend salva documento in DB
     ↓
Backend invia a VectorstoreService
     ↓
VectorstoreService vettorizza e salva
     ↓
Backend cerca trigger configurati per evento "file_upload"
     ↓
Trova workflow collegato
     ↓
WorkflowEngine esegue workflow (DAG di nodi)
     ↓
Nodi leggono da input, elaborano, scrivono output
     ↓
Risultati salvati in DB/VectorstoreService
```

### 4.2 Monitoraggio Cartella (Folder Monitor Agent)

```
File System Event (watchdog)
     ↓
SmartFileHandler detecta event
     ↓
AgentFilterClient valuta se processare
     ↓
Se sì: crea event buffer, invia al Backend
     ↓
Backend processa come evento normale
     ↓
Se fallisce: evento rimane in buffer locale
     ↓
ReconciliationService (ogni ora) sincronizza tutto
```

### 4.3 Ricerca Semantica

```
Query testuale
     ↓
Frontend invia a Backend
     ↓
Backend invia a VectorstoreService
     ↓
VectorstoreService embedding della query
     ↓
Ricerca vettoriale in ChromaDB
     ↓
Calcolo similarity score
     ↓
Ritorna risultati ordinati per similarità
```

## 5. Stack Tecnologico

| Componente | Tecnologia | Linguaggio |
|-----------|-----------|-----------|
| Backend API | FastAPI | Python |
| Frontend | React | JavaScript/TypeScript |
| Plugin System | Express.js | TypeScript/JavaScript |
| Logging | FastAPI | Python |
| Vector DB | ChromaDB | Python |
| Metadati | SQLite | SQL |
| Agent Monitor | Watchdog + FastAPI | Python |
| Orchestrazione | Docker Compose | - |

## 6. Database Models Principali

### Workflow
- `workflow_id`: Identificatore univoco
- `name`, `description`: Metadati
- `nodes`: Array di nodi con config
- `connections`: Array di connessioni tra nodi
- `is_active`: Flag abilitazione

### Trigger
- `id`: Identificatore univoco
- `event_type`: Tipo di evento (file_upload, pdf_modified, etc.)
- `source`: Origine evento (pdf-monitor-event-source, etc.)
- `workflow_id`: Workflow da eseguire
- `conditions`: Filtri opzionali (pattern file, size, metadata)
- `target_node_id`: Nodo specifico dove collegare l'input evento
- `active`: Flag abilitazione

### Document
- `id`: Identificatore univoco
- `filename`: Nome file originale
- `content`: Contenuto testuale
- `vectorstore_id`: Riferimento a ChromaDB
- `file_hash`: Hash per deduplicazione
- `created_at`, `last_updated`: Timestamp

### PDFMonitorEvent
- Traccia eventi file system per auditing

## 7. Pattern di Comunicazione Inter-Servizi

### Backend → PDK
```
GET /api/nodes          # Fetch schema nodi
POST /api/nodes/:id/execute   # Esegui nodo con dati
```

### Backend → VectorstoreService
```
POST /documents/add     # Aggiungi documento
GET /documents/search   # Ricerca semantica
DELETE /documents/:id   # Rimuovi documento
```

### Backend → LogService
```
POST /api/logs          # Invia log strutturato
POST /api/logs/batch    # Batch di log
```

### Folder Monitor Agent → Backend
```
POST /api/events/process        # Invia evento file system
POST /monitor/force-sync        # Forza sincronizzazione
GET /monitor/sync-status        # Stato sincronizzazione
```

## 8. Variabili d'Ambiente Critiche

```bash
# Backend
BACKEND_URL=http://127.0.0.1:8000
DATABASE_URL=sqlite:///./database.db
PDK_SERVER_BASE_URL=http://127.0.0.1:3001

# PDK Server
PDK_SERVER_PORT=3001
PDK_LOG_LEVEL=INFO

# VectorstoreService
VECTORSTORE_SERVICE_URL=http://127.0.0.1:8090
CHROMA_DB_PATH=./data/chroma_db

# LogService
PRAMAIALOG_HOST=127.0.0.1
PRAMAIALOG_PORT=8081

# Folder Monitor Agent
MONITOR_AGENT_PORT=8001
BACKEND_URL=http://127.0.0.1:8000
RECONCILIATION_INTERVAL=3600
```

## 9. Startup Sequence

1. **PramaIA-LogService** (port 8081) - Deve essere pronto prima degli altri
2. **PramaIA-PDK** (port 3001) - Plugin system deve essere disponibile
3. **PramaIA-VectorstoreService** (port 8090) - Database vettoriale
4. **PramaIAServer** (port 8000) - Backend (dipende da 3, 8081, 8090)
5. **Frontend** (port 3000) - React app
6. **Document Folder Monitor Agent** (port 8001) - Monitoraggio cartelle

**Script d'avvio**: `start-all.ps1` avvia tutti i servizi nell'ordine corretto

## 10. Debug e Troubleshooting

### Health Checks
```bash
# Verificare servizi attivi
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:3001/health
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8090/health
curl http://127.0.0.1:8001/health
```

### Log Debugging
- **Backend logs**: Console output
- **PDK logs**: Console output (configurabile con PDK_LOG_LEVEL=DEBUG)
- **Centralized logs**: `http://127.0.0.1:8081/dashboard`

### Database Inspection
```bash
# SQLite database (Backend)
sqlite3 PramaIAServer/backend/data/database.db

# ChromaDB (VectorstoreService)
cd PramaIA-VectorstoreService
python -c "from chromadb import Client; c = Client(); print(c.list_collections())"
```

### Common Issues
- **Port already in use**: Termina il processo o cambia porta
- **PDK nodes not found**: Verifica che PDK_SERVER_BASE_URL sia corretto
- **Trigger not executing**: Controlla event_type e source nei trigger
- **Vectorstore sync issues**: Leggi SINCRONIZZAZIONE_MULTI_LAYER.md

## 11. Performance & Scalability

### Ottimizzazioni Implementate
- **Event buffering**: Evita perdita eventi durante disconnessioni
- **Cache tag system**: Cache intelligente nel PDK
- **Lazy loading**: Nodi caricati su demand
- **ChromaDB persistence**: Database persistente per vettori

### Limiti Attuali
- DB relazionale SQLite (→ PostgreSQL per produzione)
- Single-threaded workflow execution
- VectorstoreService in-process

## 12. Concetti Chiave per Sviluppatori

### Nodi Workflow
Ogni nodo è un'unità di computazione con:
- **Input ports**: Porte tipizzate in ingresso
- **Output ports**: Porte tipizzate in uscita
- **Resolver function**: Logica di elaborazione
- **Config**: Parametri di configurazione

### Event Sources
Sorgenti di eventi (file system, webhook, scheduler, etc.) che generano eventi che triggherano workflow.

### Trigger
Collegamento tra un event source (evento) e un workflow specifico con condizioni opzionali.

### Tag System
Sistema gerarchico di tag (plugin-level, node-level) per organizzazione e filtering di componenti.

---

**Ultimo Aggiornamento**: 18 Novembre 2025  
**Versione**: 1.0
