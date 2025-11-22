# Event Sources, Trigger & Workflows - Architettura di Automazione

## 1. Panoramica Concettuale

Il sistema event-driven di PramaIA permette di automatizzare workflow in risposta a eventi del sistema. Il flusso logico è:

```
Event Source
     ↓
Event Generation
     ↓
Trigger Matching
     ↓
Workflow Execution
     ↓
Result Storage
```

## 2. Event Source - Sorgenti di Eventi

### 2.1 Cos'è un Event Source

Un Event Source è un componente che monitora una condizione e genera eventi quando questa cambia. Esempi:
- File system (creazione, modifica, eliminazione file)
- Timer/Scheduler (orari specifici)
- API Webhook (richieste HTTP esterne)
- Database trigger (cambiamenti dati)

### 2.2 Event Source Disponibili

#### PDF Monitor Event Source
**Origine**: Folder Monitor Agent monitora cartelle file system

**Eventi Generati**:
- `pdf_file_added` - Nuovo file PDF rilevato
- `pdf_file_modified` - File PDF modificato
- `pdf_file_deleted` - File PDF eliminato
- `pdf_any_change` - Evento composito: qualsiasi modifica (add/modify/delete)

**Dati Evento**:
```json
{
  "event_type": "pdf_file_added",
  "source": "pdf-monitor-event-source",
  "data": {
    "filename": "documento.pdf",
    "file_path": "/monitored/folder/documento.pdf",
    "file_size": 102400,
    "content_type": "application/pdf",
    "file_hash": "abc123def456"
  },
  "metadata": {
    "timestamp": "2025-11-18T10:30:00Z",
    "source_folder": "/monitored/folder",
    "agent_id": "monitor-1"
  }
}
```

#### Webhook Event Source
**Origine**: API HTTP esterna

**Dati Evento**:
```json
{
  "event_type": "webhook_received",
  "source": "webhook-event-source",
  "data": {
    "payload": {...},
    "headers": {...}
  }
}
```

#### Scheduler Event Source
**Origine**: Timing interno

**Eventi**: Orari configurati (cron-like)

### 2.3 Come Registrare un Nuovo Event Source

I nuovi event source devono:

1. **Generare eventi** nel formato standardizzato
2. **Inviare a Backend** tramite endpoint `/api/events/process`
3. **Implementare retry** e buffering locale

Esempio di invio evento:
```python
import requests

event = {
    "event_type": "my_event_type",
    "source": "my-event-source",
    "data": {
        "key": "value"
    },
    "metadata": {
        "timestamp": "2025-11-18T10:30:00Z"
    }
}

response = requests.post(
    "http://127.0.0.1:8000/api/events/process",
    json=event
)
```

## 3. Trigger - Collegamento tra Eventi e Workflow

### 3.1 Cos'è un Trigger

Un Trigger è una regola che dice: "Quando accade questo evento, esegui questo workflow".

**Componenti di un Trigger**:
- `event_type`: Tipo di evento da ascoltare
- `source`: Quale event source lo genera
- `workflow_id`: Quale workflow eseguire
- `target_node_id`: A quale nodo del workflow collegare l'input evento (opzionale)
- `conditions`: Filtri aggiuntivi (opzionale)
- `active`: Flag abilitazione

### 3.2 Database Schema (Trigger)

```sql
CREATE TABLE workflow_triggers (
    id TEXT PRIMARY KEY,
    name TEXT,
    event_type TEXT,          -- es. "pdf_file_added"
    source TEXT,              -- es. "pdf-monitor-event-source"
    workflow_id TEXT,         -- ID workflow da eseguire
    target_node_id TEXT,      -- Nodo input workflow
    conditions JSON,          -- Filtri opzionali
    active BOOLEAN,
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
);
```

### 3.3 Logica di Matching dei Trigger

Quando un evento è ricevuto:

```python
# 1. Backend riceve evento
event = {
    "event_type": "pdf_file_added",
    "source": "pdf-monitor-event-source",
    "data": {...}
}

# 2. Backend cerca trigger corrispondenti
triggers = db.query(Trigger).filter(
    Trigger.event_type == event["event_type"],
    Trigger.source == event["source"],
    Trigger.active == True
)

# 3. Per ogni trigger, valuta condizioni
for trigger in triggers:
    if evaluate_conditions(event, trigger.conditions):
        # 4. Esegui workflow collegato
        execute_workflow(trigger.workflow_id, event)
```

### 3.4 Condizioni su Trigger

Le condizioni permettono di filtrare ulteriormente gli eventi. Esempi:

```json
{
  "filename_pattern": "*.pdf",
  "min_size": 1024,
  "max_size": 10485760,
  "metadata_contains": {
    "source_folder": "/important"
  }
}
```

**Matching**:
- `filename_pattern`: Pattern filename (glob-like)
- `min_size`, `max_size`: Vincoli dimensione file
- `metadata_contains`: Filtri su metadata

## 4. Workflows - Pipeline di Elaborazione

### 4.1 Cos'è un Workflow

Un Workflow è una pipeline di elaborazione composta da nodi collegati tra loro. Ogni nodo esegue una specifica operazione e passa i risultati al nodo successivo.

**Struttura**:
```json
{
  "workflow_id": "pdf_processing_pipeline",
  "name": "Elaborazione PDF",
  "is_active": true,
  "nodes": [
    { "node_id": "input_node", "node_type": "pdf_input_node", ... },
    { "node_id": "extract_node", "node_type": "pdf_extractor", ... },
    { "node_id": "store_node", "node_type": "database_storage", ... }
  ],
  "connections": [
    { "from": "input_node", "to": "extract_node", ... },
    { "from": "extract_node", "to": "store_node", ... }
  ]
}
```

### 4.2 Nodi - Unità Computazionali

Ogni nodo ha:

**Inputs**: Porte tipizzate in ingresso
```json
{
  "port_name": "document",
  "type": "pdf_document",
  "required": true
}
```

**Outputs**: Porte tipizzate in uscita
```json
{
  "port_name": "extracted_text",
  "type": "text"
}
```

**Resolver Function**: Logica che elabora input e genera output
```javascript
async function resolvePdfExtractor(inputs) {
  const doc = inputs.document;
  const text = await pdf.extract(doc);
  return { extracted_text: text };
}
```

**Config**: Parametri di configurazione
```json
{
  "max_pages": 100,
  "extract_metadata": true
}
```

### 4.3 Esecuzione del Workflow - DAG Engine

Il WorkflowEngine esegue il workflow come un DAG (Directed Acyclic Graph):

```python
class WorkflowEngine:
    def execute(self, workflow, input_data):
        # 1. Valida DAG (no cicli)
        validate_dag(workflow)
        
        # 2. Topological sort dei nodi
        sorted_nodes = topological_sort(workflow.nodes)
        
        # 3. Esegui nodi in ordine
        node_results = {}
        for node in sorted_nodes:
            # Raccogliere input dal nodo precedente
            node_inputs = collect_inputs(node, node_results)
            
            # Eseguire nodo tramite PDK
            result = execute_node_via_pdk(node, node_inputs)
            
            # Salvare risultato per nodi successivi
            node_results[node.id] = result
        
        # 4. Ritorna risultati finali
        return node_results
```

### 4.4 Type Checking nei Nodi

Il sistema valida che gli output di un nodo corrispondano agli input del nodo successivo:

```python
# Definizione nodi
nodes = [
    {
        "node_id": "node1",
        "outputs": [{"port_name": "result", "type": "text"}]
    },
    {
        "node_id": "node2",
        "inputs": [{"port_name": "input", "type": "text"}]
    }
]

# Validazione
if node1.outputs[0].type != node2.inputs[0].type:
    raise ValidationError("Type mismatch")
```

## 5. Integrazione: Event → Trigger → Workflow

### 5.1 Flusso Completo

```
1. Evento generato (es. file creato)
   ↓
2. Event Source invia a Backend: POST /api/events/process
   ↓
3. Backend riceve evento
   ↓
4. TriggerService trova trigger corrispondenti
   ↓
5. Valuta condizioni trigger
   ↓
6. Se matchato, chiama WorkflowEngine.execute()
   ↓
7. WorkflowEngine orchestrar nodi tramite PDK
   ↓
8. PDK esegue resolver function di ogni nodo
   ↓
9. Risultati salvati in database/vectorstore
```

### 5.2 Dati Disponibili in Workflow

Quando un workflow viene eseguito da un trigger, i dati dell'evento sono disponibili come input al nodo designato (target_node_id):

```python
# Trigger configuration
trigger = {
    "event_type": "pdf_file_added",
    "source": "pdf-monitor-event-source",
    "workflow_id": "pdf_pipeline",
    "target_node_id": "pdf_input_node",  # Nodo dove collegare l'evento
    "conditions": {...}
}

# Workflow execution
workflow = {
    "nodes": [
        {
            "node_id": "pdf_input_node",
            "node_type": "input_node",
            "outputs": [{"port_name": "document", "type": "pdf"}]
        },
        {...}
    ]
}

# Esecuzione
# Event data → pdf_input_node → successive nodes
```

## 6. Operazioni Comuni

### 6.1 Creare un Trigger

```python
from backend.crud import TriggerCRUD

trigger_crud = TriggerCRUD(session)
trigger_crud.create({
    "name": "Process PDF Upload",
    "event_type": "pdf_file_added",
    "source": "pdf-monitor-event-source",
    "workflow_id": "pdf_processing_pipeline",
    "target_node_id": "pdf_input_node",
    "conditions": {
        "filename_pattern": "*.pdf",
        "max_size": 10485760  # 10MB
    },
    "active": True
})
```

### 6.2 Elencare Trigger per Evento

```python
triggers = trigger_crud.get_by_event_and_source(
    event_type="pdf_file_added",
    source="pdf-monitor-event-source"
)
```

### 6.3 Disattivare un Trigger

```python
trigger_crud.deactivate(trigger_id)
```

### 6.4 Eseguire un Workflow Manualmente

```python
from backend.engine.workflow_engine import WorkflowEngine

engine = WorkflowEngine(pdk_client)
result = engine.execute(
    workflow_id="pdf_processing_pipeline",
    input_data={
        "pdf_input_node": {
            "document": {
                "filename": "test.pdf",
                "content": b"..."
            }
        }
    }
)
```

## 7. Debugging & Troubleshooting

### 7.1 Trigger Non Viene Eseguito

**Checklist**:
1. Verificare che trigger sia `active = True`
2. Verificare che `event_type` e `source` corrispondano all'evento
3. Verificare che il workflow esista e sia `is_active = True`
4. Verificare le condizioni (pattern, size, etc.)
5. Controllare i log del backend

```bash
# Cercare trigger nel database
sqlite3 database.db "SELECT * FROM workflow_triggers WHERE active=1;"

# Cercare evento nei log
curl http://127.0.0.1:8081/api/logs?level=ERROR
```

### 7.2 Workflow Non Esegue Correttamente

**Checklist**:
1. Verificare che il nodo sia disponibile in PDK: `GET /api/nodes`
2. Verificare i type dei nodi (input/output type matching)
3. Controllare che il target_node_id esista nel workflow
4. Controllare i log del PDK Server

```bash
# Test manuale nodo
curl -X POST http://127.0.0.1:3001/api/nodes/pdf_extractor/execute \
  -H "Content-Type: application/json" \
  -d '{"document": {...}}'
```

### 7.3 Logging Dettagliato

Configurare livello debug:

```bash
# Backend
export LOGLEVEL=DEBUG

# PDK
export PDK_LOG_LEVEL=DEBUG
```

## 8. Schema di Riferimento Rapido

| Componente | Definisce | Risultato |
|-----------|----------|----------|
| **Event Source** | Quando generiamo gli eventi | Eventi specifici (pdf_added, etc.) |
| **Event** | Cosa accade | Dati + timestamp |
| **Trigger** | Collegamento evento→workflow | Automazione |
| **Workflow** | Come elaborare dati | DAG di nodi |
| **Nodo** | Singolo step elaborazione | Trasformazione dati |
| **Connection** | Link tra nodi | Flusso dati nel workflow |

## 9. Limiti Attuali & Future Directions

### Attuali Limitazioni
- Un trigger per workflow (futura: multiple triggers → same workflow)
- Esecuzione workflow sequenziale (futura: parallelizzazione nodi)
- Nessun scheduling a livello workflow (usa Scheduler Event Source per workaround)

### Planned Features
- Visual workflow builder
- Conditional branching in workflow
- Loop e retry logic
- Webhook per notifiche post-workflow

---

**Ultimo Aggiornamento**: 18 Novembre 2025  
**Versione**: 1.0
