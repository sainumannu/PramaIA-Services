# Template di Workflow per PramaIA PDK

Questa directory contiene i template di workflow in formato JSON che possono essere importati nel sistema PramaIA PDK. Questi template definiscono la struttura e il comportamento dei workflow che verranno poi eseguiti dal sistema.

## Importante: Importazione Necessaria

**Nota importante**: I file JSON presenti in questa directory sono solo template e non vengono utilizzati direttamente dal sistema PDK. Per essere utilizzati, devono essere importati nel database del sistema tramite gli script di utilità forniti. I trigger per l'automazione vengono configurati separatamente.

## Scopo dei File di Workflow

I file JSON in questa directory servono diversi scopi:

1. **Template per l'Importazione**: Questi file contengono la struttura completa dei workflow che possono essere importati nel database del sistema PDK tramite gli script di utilità.

2. **Esempi di Riferimento**: Forniscono esempi completi di workflow funzionanti che possono essere utilizzati come riferimento per la creazione di nuovi workflow.

3. **Configurazioni Predefinite**: Definiscono configurazioni standard ottimizzate per casi d'uso comuni, come l'ingestione di PDF o le query semantiche.

4. **Backup e Versionamento**: Permettono di mantenere un backup e un versionamento dei workflow al di fuori del database.

## Importazione dei Workflow

I workflow contenuti in questi file non vengono utilizzati direttamente dal sistema PDK, ma devono essere importati nel database. Per importare i workflow, utilizzare gli script forniti:

```powershell
# Per un'importazione semplice
python insert_workflows_simple.py

# Per un'importazione ottimizzata
python insert_optimized_workflows.py
```

## Configurazione dei Trigger

Dopo aver importato i workflow, è possibile configurare i trigger per farli avviare automaticamente in risposta a determinati eventi:

```powershell
# Per configurare i trigger di monitoraggio PDF (aggiunti, modificati, eliminati)
python setup_pdf_monitor_triggers.py
```

Questo script configura i trigger necessari per collegare gli eventi generati dal monitoraggio dei file PDF (aggiunti, modificati, eliminati) ai workflow appropriati nel database.

## Struttura dei File di Workflow

Ogni file JSON di workflow segue questa struttura generale:

```json
{
  "workflow_id": "workflow_id",
  "name": "Nome del Workflow",
  "description": "Descrizione dettagliata del workflow",
  "is_active": true,
  "is_public": true,
  "category": "categoria",
  "tags": ["tag1", "tag2"],
  "nodes": [
    {
      "node_id": "node_1",
      "node_type": "processor_type",
      "name": "Nome del Nodo",
      "description": "Descrizione del nodo",
      "config": {
        "inputPorts": ["input_1"],
        "outputPorts": ["output_1"],
        "additionalConfig": {}
      },
      "position": { "x": 100, "y": 200 },
      "width": 180,
      "height": 80
    },
    // Altri nodi...
  ],
  "connections": [
    {
      "from_node_id": "node_1",
      "to_node_id": "node_2",
      "from_port": "output_1",
      "to_port": "input_1"
    },
    // Altri collegamenti...
  ]
}
```

## Tipi di Workflow Disponibili

In questa directory sono presenti i seguenti workflow:

1. **PDF Ingest Pipelines**: 
   - `pdf_ingest_complete_pipeline.json`: Pipeline completa per l'ingestione di PDF
   - `pdf_ingest_optimized_pipeline.json`: Versione ottimizzata della pipeline di ingestione

2. **Semantic Query Pipelines**:
   - `pdf_semantic_query_pipeline.json`: Pipeline standard per query semantiche su PDF
   - `pdf_semantic_query_optimized_pipeline.json`: Versione ottimizzata per query semantiche
   - `pdf_semantic_query_pipeline_test.json`: Versione per testing delle query semantiche

3. **Funzionalità di Monitoraggio**:
   - Nota: I vecchi workflow separati per il monitoraggio (`pdf_modified_document_update_pipeline.json`, `metadata_synchronization_pipeline.json`, `pdf_deleted_document_cleanup_pipeline.json`) sono stati rimossi e sostituiti da trigger configurati sul workflow `pdf_ingest_optimized_pipeline.json` esistente, che ora gestisce tutti gli eventi di monitoraggio (aggiunta, modifica, eliminazione di file).

4. **Esempi e Tutorial**:
   - `pdf_metadata_analysis_pipeline.json`: Esempio di workflow per l'analisi dei metadati PDF (usato nel tutorial)

5. **Public Workflows**:
   - `ingest_pdf_to_chroma_public.json`: Workflow pubblico per ingestione in Chroma DB
   - `query_chroma_semantic_public.json`: Workflow pubblico per query semantiche in Chroma DB

## Modifica e Creazione di Nuovi Workflow

Per creare nuovi workflow, è consigliabile:

1. Duplicare un workflow esistente simile a quello desiderato
2. Modificare l'ID, il nome e la descrizione
3. Modificare i nodi e i collegamenti secondo necessità
4. Importare il nuovo workflow utilizzando gli script di utilità
5. Configurare i trigger appropriati se necessario

## Note Importanti

- I workflow vengono memorizzati nel database e questi file servono principalmente come template
- Modifiche ai file in questa directory non influenzano i workflow già importati nel database
- Per aggiornare un workflow esistente nel database, è necessario reimportarlo
- Assicurarsi che tutti i plugin e i nodi riferiti nei workflow siano correttamente installati nel sistema PDK prima dell'importazione

---

## Documentazione Aggiuntiva

Per ulteriori informazioni sulla creazione e configurazione dei workflow, consultare:

- [Guida alla Creazione e Gestione di Workflow](../docs/WORKFLOW_CREATION_GUIDE.md)
- [Tutorial: Creazione e Configurazione di un Workflow](../docs/WORKFLOW_TUTORIAL.md)
- [Documentazione Event Sources PDK](../docs/PDK-EVENT-SOURCES-DOCUMENTATION.md)
