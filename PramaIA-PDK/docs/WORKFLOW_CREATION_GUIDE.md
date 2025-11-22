# Guida alla Creazione e Gestione di Workflow in PramaIA PDK

Questa guida fornisce istruzioni dettagliate su come creare template di workflow, importarli nel database e collegarli con i trigger degli eventi per automatizzare i processi.

## Indice
1. [Struttura dei Workflow](#1-struttura-dei-workflow)
2. [Creazione di un Template di Workflow](#2-creazione-di-un-template-di-workflow)
3. [Importazione di un Workflow nel Database](#3-importazione-di-un-workflow-nel-database)
4. [Configurazione dei Trigger degli Eventi](#4-configurazione-dei-trigger-degli-eventi)
5. [Test e Verifica](#5-test-e-verifica)
6. [Esempi e Best Practice](#6-esempi-e-best-practice)

---

## 1. Struttura dei Workflow

Un workflow in PramaIA PDK è composto da:

- **Metadati del workflow**: ID, nome, descrizione, ecc.
- **Nodi**: Elementi funzionali che eseguono specifiche operazioni (es. input, elaborazione, output)
- **Connessioni**: Collegamenti tra i nodi che definiscono il flusso dei dati
- **Trigger**: Eventi che possono avviare automaticamente l'esecuzione del workflow

Il sistema utilizza il database SQLite per memorizzare queste informazioni nelle seguenti tabelle:

- `workflows`: Metadati generali del workflow
- `workflow_nodes`: Definizione dei nodi
- `workflow_connections`: Collegamenti tra i nodi
- `workflow_triggers`: Configurazione dei trigger degli eventi

## 2. Creazione di un Template di Workflow

I template di workflow sono file JSON che definiscono la struttura e il comportamento di un workflow. Questi file vengono utilizzati per importare nuovi workflow nel sistema.

### Struttura Base di un Template

```json
{
  "workflow_id": "example_workflow_template",
  "name": "Esempio di Workflow",
  "description": "Descrizione dettagliata del workflow",
  "is_active": true,
  "is_public": true,
  "category": "pdf_processing",
  "tags": ["pdf", "automation"],
  "nodes": [
    {
      "node_id": "input_node",
      "node_type": "pdf_input_node",
      "name": "Input PDF",
      "description": "Nodo per l'input di documenti PDF",
      "config": {
        "requiresInput": false,
        "outputPorts": ["document"]
      },
      "position": { "x": 100, "y": 100 },
      "width": 180,
      "height": 80
    },
    {
      "node_id": "process_node",
      "node_type": "pdf_text_extractor",
      "name": "Estrattore Testo",
      "description": "Estrae il testo dal documento PDF",
      "config": {
        "inputPorts": ["document"],
        "outputPorts": ["text"]
      },
      "position": { "x": 400, "y": 100 },
      "width": 180,
      "height": 80
    }
  ],
  "connections": [
    {
      "from_node_id": "input_node",
      "to_node_id": "process_node",
      "from_port": "document",
      "to_port": "document"
    }
  ]
}
```

### Parametri Principali

- **workflow_id**: Identificatore univoco del workflow (alfanumerico)
- **name**: Nome leggibile del workflow
- **description**: Descrizione dettagliata dello scopo e del funzionamento del workflow
- **is_active**: Stato di attivazione del workflow (true/false)
- **is_public**: Indica se il workflow è pubblicamente accessibile (true/false)
- **category**: Categoria del workflow per la classificazione
- **tags**: Array di tag per la categorizzazione

#### Nodi

Ogni nodo deve avere:
- **node_id**: Identificatore univoco del nodo all'interno del workflow
- **node_type**: Tipo di nodo (deve corrispondere a un tipo di nodo registrato nel sistema)
- **name**: Nome leggibile del nodo
- **description**: Descrizione della funzione del nodo
- **config**: Configurazione specifica del nodo, incluse porte di input e output
- **position**: Coordinate x,y per il posizionamento nell'interfaccia grafica

#### Connessioni

Ogni connessione deve definire:
- **from_node_id**: ID del nodo di origine
- **to_node_id**: ID del nodo di destinazione
- **from_port**: Nome della porta di output del nodo di origine
- **to_port**: Nome della porta di input del nodo di destinazione

## 3. Importazione di un Workflow nel Database

Per importare un template di workflow nel database, è possibile utilizzare gli script forniti:

- **insert_optimized_workflows.py**: Per importare workflow ottimizzati con configurazione avanzata
  - Supporta l'importazione selettiva di un solo workflow con `--workflow nome_file.json`
  - Controlla automaticamente se il workflow è cambiato prima di aggiornarlo
  - Supporta l'opzione `--force` per forzare l'aggiornamento anche senza modifiche
  
- **insert_workflows_simple.py**: Per importare workflow più semplici
  - Importa tutti i workflow nella cartella `workflows/`
  - Più semplice da utilizzare ma con meno opzioni

### Utilizzo degli Script di Importazione

1. Salvare il template JSON nella cartella `workflows/`
2. Eseguire lo script di importazione appropriato:

```bash
python insert_optimized_workflows.py
```

oppure

```bash
python insert_workflows_simple.py
```

> **Nota importante:** Il database di PramaIA si trova in `PramaIAServer/backend/db/database.db`. Gli script di importazione sono configurati per utilizzare questo percorso. Se il database è stato spostato, sarà necessario aggiornare il percorso `DATABASE_PATH` negli script.

### Processo di Importazione

Il processo di importazione esegue le seguenti operazioni:

1. Analisi del file JSON del template
2. Verifica se il workflow esiste già nel database (in base all'ID)
3. Inserimento o aggiornamento dei metadati del workflow
4. Inserimento o aggiornamento dei nodi
5. Inserimento o aggiornamento delle connessioni

## 4. Configurazione dei Trigger degli Eventi

I trigger permettono di avviare automaticamente un workflow in risposta a specifici eventi. Per configurare i trigger, è possibile utilizzare lo script `setup_pdf_monitor_triggers.py`.

### Struttura di un Trigger

Un trigger è definito dai seguenti parametri:

- **workflow_id**: ID del workflow da avviare
- **source**: Fonte dell'evento (es. "pdf-monitor-event-source")
- **event_type**: Tipo di evento (es. "pdf_file_added", "pdf_file_modified", "pdf_file_deleted")
- **name**: Nome descrittivo del trigger
- **conditions**: Condizioni che devono essere soddisfatte per attivare il trigger (formato JSON)
- **target_node_id**: ID del nodo a cui passare i dati dell'evento

### Configurazione Manuale dei Trigger

Per configurare manualmente i trigger, è possibile modificare lo script `setup_pdf_monitor_triggers.py`:

```python
trigger_mappings = [
    {
        "workflow_id": "example_workflow_template",
        "source": "pdf-monitor-event-source",
        "event_type": "pdf_file_added",
        "name": "Trigger per nuovi PDF",
        "description": "Trigger per elaborare nuovi documenti PDF",
        "conditions": json.dumps({
            "fileSize": {
                "operator": "greaterThan",
                "value": 0
            }
        }),
        "target_node_id": "input_node"
    }
]
```

Quindi eseguire lo script:

```bash
python setup_pdf_monitor_triggers.py
```

## 5. Test e Verifica

Dopo aver importato un workflow e configurato i trigger, è importante verificare che tutto funzioni correttamente.

### Verifica dei Workflow

Per verificare i workflow presenti nel database:

```bash
python list_workflows.py
```

### Verifica dei Trigger

I trigger configurati verranno mostrati nel risultato di `list_workflows.py` sotto ciascun workflow.

### Test del Workflow

Per testare un workflow con trigger:

1. Generare l'evento corrispondente (es. aggiungere un file PDF in una cartella monitorata)
2. Verificare che il workflow venga avviato automaticamente
3. Controllare i log per eventuali errori

## 6. Esempi e Best Practice

### Esempio di Workflow Completo

Nella cartella `workflows/` sono presenti esempi di workflow che possono essere utilizzati come riferimento:

- `pdf_ingest_optimized_pipeline.json`: Workflow per l'importazione e l'elaborazione di documenti PDF
- `pdf_semantic_query_optimized_pipeline.json`: Workflow per l'esecuzione di query semantiche su documenti PDF

### Best Practice

- **Naming Consistente**: Utilizzare nomi descrittivi e coerenti per workflow, nodi e porte
- **Documentazione**: Fornire descrizioni dettagliate per ogni componente
- **Modularità**: Progettare workflow modulari che possono essere riutilizzati
- **Test Incrementali**: Testare ciascun nodo separatamente prima di collegare l'intero workflow
- **Gestione degli Errori**: Considerare come il workflow gestirà gli errori e le eccezioni

---

Per ulteriori informazioni, consultare la documentazione completa di PramaIA PDK nella cartella `docs/`.
