# Tutorial: Creazione e Configurazione di un Workflow in PramaIA PDK

Questo tutorial pratico mostra passo dopo passo come creare un nuovo workflow per l'elaborazione di documenti, importarlo nel database e configurare i trigger per l'automazione.

> **Nota**: Questo tutorial utilizza un workflow di esempio (`pdf_metadata_analysis_pipeline.json`) che è disponibile nella cartella `workflows/`. Il workflow è incluso come esempio didattico e può essere importato nel database utilizzando gli script `insert_optimized_workflows.py` o `insert_workflows_simple.py`.

## Indice
1. [Panoramica del Progetto](#1-panoramica-del-progetto)
2. [Creazione del Template del Workflow](#2-creazione-del-template-del-workflow)
3. [Importazione del Workflow](#3-importazione-del-workflow)
4. [Configurazione dei Trigger](#4-configurazione-dei-trigger)
5. [Test e Debugging](#5-test-e-debugging)

---

## 1. Panoramica del Progetto

In questo tutorial, creeremo un workflow per l'analisi dei metadati dei documenti PDF. Il workflow eseguirà le seguenti operazioni:

1. Ricevere un documento PDF come input
2. Estrarre i metadati dal documento
3. Analizzare i metadati per estrarre informazioni rilevanti
4. Salvare le informazioni estratte nel database

## 2. Creazione del Template del Workflow

### 2.1. Definizione dei Metadati del Workflow

Creiamo un nuovo file JSON nella cartella `workflows/` chiamato `pdf_metadata_analysis_pipeline.json`:

```json
{
  "workflow_id": "pdf_metadata_analysis_pipeline",
  "name": "Pipeline Analisi Metadati PDF",
  "description": "Analizza i metadati dei documenti PDF e salva le informazioni rilevanti",
  "is_active": true,
  "is_public": true,
  "category": "pdf_processing",
  "tags": ["pdf", "metadata", "analysis"],
  "nodes": [],
  "connections": []
}
```

### 2.2. Definizione dei Nodi

Ora aggiungiamo i nodi necessari per il nostro workflow:

```json
"nodes": [
  {
    "node_id": "pdf_input_node",
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
    "node_id": "metadata_extractor_node",
    "node_type": "pdf_metadata_extractor",
    "name": "Estrattore Metadati",
    "description": "Estrae i metadati dal documento PDF",
    "config": {
      "inputPorts": ["document"],
      "outputPorts": ["metadata"]
    },
    "position": { "x": 400, "y": 100 },
    "width": 180,
    "height": 80
  },
  {
    "node_id": "metadata_analyzer_node",
    "node_type": "metadata_analyzer",
    "name": "Analizzatore Metadati",
    "description": "Analizza i metadati per estrarre informazioni rilevanti",
    "config": {
      "inputPorts": ["metadata"],
      "outputPorts": ["analyzed_data"],
      "extractFields": ["author", "title", "subject", "keywords", "creationDate"]
    },
    "position": { "x": 700, "y": 100 },
    "width": 180,
    "height": 80
  },
  {
    "node_id": "db_storage_node",
    "node_type": "database_storage",
    "name": "Storage Database",
    "description": "Salva le informazioni estratte nel database",
    "config": {
      "inputPorts": ["analyzed_data"],
      "outputPorts": ["result"],
      "tableName": "pdf_metadata",
      "createIfNotExists": true
    },
    "position": { "x": 1000, "y": 100 },
    "width": 180,
    "height": 80
  }
]
```

### 2.3. Definizione delle Connessioni

Infine, definiamo le connessioni tra i nodi:

```json
"connections": [
  {
    "from_node_id": "pdf_input_node",
    "to_node_id": "metadata_extractor_node",
    "from_port": "document",
    "to_port": "document"
  },
  {
    "from_node_id": "metadata_extractor_node",
    "to_node_id": "metadata_analyzer_node",
    "from_port": "metadata",
    "to_port": "metadata"
  },
  {
    "from_node_id": "metadata_analyzer_node",
    "to_node_id": "db_storage_node",
    "from_port": "analyzed_data",
    "to_port": "analyzed_data"
  }
]
```

Il file JSON completo sarà:

```json
{
  "workflow_id": "pdf_metadata_analysis_pipeline",
  "name": "Pipeline Analisi Metadati PDF",
  "description": "Analizza i metadati dei documenti PDF e salva le informazioni rilevanti",
  "is_active": true,
  "is_public": true,
  "category": "pdf_processing",
  "tags": ["pdf", "metadata", "analysis"],
  "nodes": [
    {
      "node_id": "pdf_input_node",
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
      "node_id": "metadata_extractor_node",
      "node_type": "pdf_metadata_extractor",
      "name": "Estrattore Metadati",
      "description": "Estrae i metadati dal documento PDF",
      "config": {
        "inputPorts": ["document"],
        "outputPorts": ["metadata"]
      },
      "position": { "x": 400, "y": 100 },
      "width": 180,
      "height": 80
    },
    {
      "node_id": "metadata_analyzer_node",
      "node_type": "metadata_analyzer",
      "name": "Analizzatore Metadati",
      "description": "Analizza i metadati per estrarre informazioni rilevanti",
      "config": {
        "inputPorts": ["metadata"],
        "outputPorts": ["analyzed_data"],
        "extractFields": ["author", "title", "subject", "keywords", "creationDate"]
      },
      "position": { "x": 700, "y": 100 },
      "width": 180,
      "height": 80
    },
    {
      "node_id": "db_storage_node",
      "node_type": "database_storage",
      "name": "Storage Database",
      "description": "Salva le informazioni estratte nel database",
      "config": {
        "inputPorts": ["analyzed_data"],
        "outputPorts": ["result"],
        "tableName": "pdf_metadata",
        "createIfNotExists": true
      },
      "position": { "x": 1000, "y": 100 },
      "width": 180,
      "height": 80
    }
  ],
  "connections": [
    {
      "from_node_id": "pdf_input_node",
      "to_node_id": "metadata_extractor_node",
      "from_port": "document",
      "to_port": "document"
    },
    {
      "from_node_id": "metadata_extractor_node",
      "to_node_id": "metadata_analyzer_node",
      "from_port": "metadata",
      "to_port": "metadata"
    },
    {
      "from_node_id": "metadata_analyzer_node",
      "to_node_id": "db_storage_node",
      "from_port": "analyzed_data",
      "to_port": "analyzed_data"
    }
  ]
}
```

## 3. Importazione del Workflow

### 3.1. Salvataggio del Template

Salviamo il file JSON nella cartella `workflows/`:

```
C:\PramaIA\PramaIA-PDK\workflows\pdf_metadata_analysis_pipeline.json
```

### 3.2. Modifica dello Script di Importazione

Assicuriamoci che il nostro workflow sia incluso nello script `insert_optimized_workflows.py`:

```python
# Lista dei workflow da importare
workflow_files = [
    "pdf_ingest_optimized_pipeline.json",
    "pdf_semantic_query_optimized_pipeline.json",
    "pdf_metadata_analysis_pipeline.json"  # Aggiungiamo il nostro nuovo workflow
]
```

### 3.3. Esecuzione dell'Importazione

Eseguiamo lo script di importazione:

```bash
python insert_optimized_workflows.py
```

### 3.4. Verifica dell'Importazione

Verifichiamo che il workflow sia stato importato correttamente:

```bash
cd ..\PramaIAServer
python list_workflows.py
```

Dovremmo vedere il nostro nuovo workflow nella lista dei workflow attivi.

## 4. Configurazione dei Trigger

### 4.1. Creazione dello Script per i Trigger

Creiamo un nuovo script per configurare i trigger specifici per il nostro workflow:

```python
#!/usr/bin/env python3
"""
Script per configurare i trigger per il workflow di analisi dei metadati PDF.
"""

import json
import sqlite3
import os
import uuid
from datetime import datetime

def setup_metadata_triggers(db_path):
    """Configura i trigger per il workflow di analisi dei metadati PDF"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Definizione dei trigger da configurare
    trigger_mappings = [
        {
            "workflow_id": "pdf_metadata_analysis_pipeline",
            "source": "pdf-monitor-event-source",
            "event_type": "pdf_file_added",
            "name": "Trigger Analisi Metadati per Nuovi PDF",
            "description": "Trigger per analizzare i metadati dei nuovi documenti PDF",
            "conditions": json.dumps({
                "fileSize": {
                    "operator": "greaterThan",
                    "value": 0
                }
            }),
            "target_node_id": "pdf_input_node"
        },
        {
            "workflow_id": "pdf_metadata_analysis_pipeline",
            "source": "pdf-monitor-event-source",
            "event_type": "pdf_file_modified",
            "name": "Trigger Analisi Metadati per PDF Modificati",
            "description": "Trigger per analizzare i metadati dei documenti PDF modificati",
            "conditions": json.dumps({
                "fileSize": {
                    "operator": "greaterThan",
                    "value": 0
                }
            }),
            "target_node_id": "pdf_input_node"
        }
    ]
    
    triggers_created = 0
    triggers_updated = 0
    
    try:
        # Per ogni trigger nella configurazione
        for trigger_config in trigger_mappings:
            workflow_id = trigger_config["workflow_id"]
            source = trigger_config["source"]
            event_type = trigger_config["event_type"]
            
            # Verifica che il workflow esista
            cursor.execute("SELECT id FROM workflows WHERE workflow_id = ?", (workflow_id,))
            workflow = cursor.fetchone()
            
            if not workflow:
                print(f"⚠️ Workflow '{workflow_id}' non trovato nel database, salto configurazione trigger...")
                continue
            
            # Verifica se il trigger esiste già
            cursor.execute("""
                SELECT id FROM workflow_triggers 
                WHERE workflow_id = ? AND source = ? AND event_type = ?
            """, (workflow_id, source, event_type))
            existing_trigger = cursor.fetchone()
            
            # Prepara i dati per il trigger
            name = trigger_config.get("name", f"Trigger {event_type}")
            description = trigger_config.get("description", "Trigger automatico")
            conditions = trigger_config.get("conditions", "{}")
            target_node_id = trigger_config.get("target_node_id", "")
            
            # Genera un ID univoco per il trigger
            trigger_id = str(uuid.uuid4())
            
            if existing_trigger:
                # Aggiorna il trigger esistente
                cursor.execute("""
                    UPDATE workflow_triggers 
                    SET name = ?, conditions = ?, active = 1, updated_at = ?, target_node_id = ?
                    WHERE id = ?
                """, (
                    name, 
                    conditions,
                    datetime.now().isoformat(), 
                    target_node_id,
                    existing_trigger[0]
                ))
                triggers_updated += 1
                print(f"🔄 Aggiornato trigger per {workflow_id} → {event_type}")
            else:
                # Crea un nuovo trigger
                cursor.execute("""
                    INSERT INTO workflow_triggers 
                    (id, name, event_type, source, workflow_id, conditions, 
                     active, created_at, updated_at, target_node_id)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """, (
                    trigger_id,
                    name,
                    event_type,
                    source,
                    workflow_id,
                    conditions,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    target_node_id
                ))
                triggers_created += 1
                print(f"✨ Creato nuovo trigger ID:{trigger_id} per {workflow_id} → {event_type}")
        
        conn.commit()
        print(f"\n✅ Configurazione completata: {triggers_created} trigger creati, {triggers_updated} trigger aggiornati")
        
    except Exception as e:
        print(f"❌ Errore durante la configurazione dei trigger: {str(e)}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def main():
    """Funzione principale"""
    print("🚀 Configurazione dei trigger per il workflow di analisi dei metadati PDF...")
    
    # Path al database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'PramaIAServer', 'backend', 'data', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return
    
    print(f"📂 Database trovato: {db_path}")
    
    # Configura i trigger
    setup_metadata_triggers(db_path)
    
    print("\n✨ Configurazione completata! Il workflow è ora collegato agli event source.")

if __name__ == "__main__":
    main()
```

### 4.2. Esecuzione dello Script per i Trigger

Eseguiamo lo script per configurare i trigger:

```bash
python setup_metadata_triggers.py
```

### 4.3. Verifica dei Trigger

Verifichiamo che i trigger siano stati configurati correttamente:

```bash
cd ..\PramaIAServer
python list_workflows.py
```

Dovremmo vedere i nuovi trigger associati al nostro workflow.

## 5. Test e Debugging

### 5.1. Test del Workflow

Per testare il workflow:

1. Aggiungi un nuovo file PDF in una cartella monitorata
2. Verifica che il workflow venga avviato automaticamente
3. Controlla nel database la tabella `pdf_metadata` per verificare che i dati siano stati salvati correttamente

### 5.2. Debugging

Se il workflow non funziona come previsto, possiamo verificare:

1. I log del sistema per eventuali errori
2. La configurazione dei nodi e delle connessioni
3. La configurazione dei trigger
4. Lo stato dei file di input

### 5.3. Monitoraggio degli Eventi

Per monitorare gli eventi PDF registrati:

```sql
SELECT * FROM pdf_monitor_events ORDER BY timestamp DESC LIMIT 10;
```

### 5.4. Monitoraggio delle Esecuzioni del Workflow

Per monitorare le esecuzioni del workflow:

```sql
SELECT * FROM workflow_executions WHERE workflow_id = 'pdf_metadata_analysis_pipeline' ORDER BY started_at DESC LIMIT 10;
```

---

Seguendo questo tutorial, hai imparato a creare un workflow completo, importarlo nel database e configurare i trigger per automatizzare la sua esecuzione in risposta a eventi specifici.

Per ulteriori informazioni, consulta la documentazione completa di PramaIA PDK nella cartella `docs/`.
