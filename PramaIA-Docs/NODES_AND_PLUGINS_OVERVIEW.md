# PramaIA Nodes and Plugins Overview

## Introduzione

Il sistema PramaIA PDK (Plugin Development Kit) fornisce un framework modulare per la creazione e gestione di nodi e plugin nei workflow di intelligenza artificiale. Ogni plugin contiene una collezione di nodi che possono essere collegati per creare pipeline di elaborazione complesse.

## Architettura dei Plugin

### Struttura Plugin
```
plugin-name/
├── plugin.json          # Definizione del plugin e dei nodi
├── README.md           # Documentazione del plugin
├── requirements.txt    # Dipendenze Python
└── src/               # Processori dei nodi
    ├── node1_processor.py
    ├── node2_processor.py
    └── ...
```

### File plugin.json
Il file `plugin.json` contiene:
- **Metadati del plugin**: nome, versione, descrizione, autore
- **Definizioni dei nodi**: configurazioni, input/output, schema
- **Dipendenze**: librerie Python richieste
- **Compatibilità**: versioni PDK ed engine supportate

### Processori Nodi
Ogni nodo ha un processore Python che:
- Implementa la logica di elaborazione
- Gestisce input e output
- Integra logging per monitoraggio
- Gestisce errori e stati

## Categorizzazione Nodi

### Tipi di Nodi
1. **Input Nodes**: Ricevono dati dall'esterno
2. **Processing Nodes**: Elaborano e trasformano dati
3. **Output Nodes**: Producono output finali
4. **Storage Nodes**: Gestiscono persistenza dati

### Categorie Funzionali
- **Document Processing**: Gestione documenti
- **RAG (Retrieval Augmented Generation)**: Sistemi di ricerca semantica
- **LLM Integration**: Integrazione modelli linguistici
- **Vector Operations**: Operazioni su vettori/embeddings
- **Data Processing**: Elaborazione dati generica

## Standard di Implementazione

### Logging Requirements
Ogni nodo deve implementare:
```python
# Log di ingresso
logger.info(f"[{node_name}] INGRESSO nodo: {method_name}")

# Log di uscita successo
logger.info(f"[{node_name}] USCITA nodo (successo): {result_summary}")

# Log di uscita errore
logger.error(f"[{node_name}] USCITA nodo (errore): {error_message}")
```

### Struttura Processore Standard
```python
class NodeProcessor:
    def __init__(self):
        # Inizializzazione
    
    async def process(self, context) -> Dict[str, Any]:
        logger.info("[NodeName] INGRESSO nodo: process")
        try:
            # Elaborazione
            result = self._process_logic(context)
            logger.info(f"[NodeName] USCITA nodo (successo): {summary}")
            return result
        except Exception as e:
            logger.error(f"[NodeName] USCITA nodo (errore): {str(e)}")
            return {"status": "error", "error": str(e)}

# Entry point
async def process_node(context):
    processor = NodeProcessor()
    return await processor.process(context)
```

### Schema di Configurazione
Ogni nodo definisce un JSON Schema per la configurazione:
```json
{
  "configSchema": {
    "type": "object",
    "title": "Configurazione Nodo",
    "properties": {
      "parameter1": {
        "type": "string",
        "title": "Parametro 1",
        "default": "valore_default"
      }
    },
    "required": ["parameter1"]
  }
}
```

## Plugin Disponibili

### Core Plugins
1. **core-data-plugin**: Gestione dati base
2. **core-rag-plugin**: Sistema RAG core
3. **core-llm-plugin**: Integrazione LLM
4. **internal-processors-plugin**: Processori interni

### Specialized Plugins
1. **document-semantic-complete-plugin**: Pipeline semantica documenti
2. **pdf-monitor-plugin**: Monitoraggio file PDF

## Linee Guida Sviluppo

### Best Practices
1. **Modularità**: Un nodo = una funzione specifica
2. **Riusabilità**: Nodi configurabili per diversi use case
3. **Robustezza**: Gestione errori completa
4. **Monitorabilità**: Logging strutturato
5. **Testabilità**: Unit test per ogni processore

### Convenzioni Naming
- Plugin: `category-purpose-plugin` (es. `document-semantic-plugin`)
- Nodi: `action_target` (es. `text_embedder`, `pdf_extractor`)
- Processori: `{node_id}_processor.py`

### Error Handling
```python
try:
    # Logica principale
    pass
except SpecificException as e:
    logger.error(f"Errore specifico: {e}")
    return {"status": "error", "error": str(e), "error_type": "specific"}
except Exception as e:
    logger.error(f"Errore generico: {e}")
    return {"status": "error", "error": str(e), "error_type": "generic"}
```

## Integrazione con Servizi

### LogService
I nodi integrano automaticamente il LogService per:
- Logging centralizzato
- Monitoraggio performance
- Debug distribuito
- Analisi workflow

### VectorstoreService
Per nodi che gestiscono embeddings:
- API REST standardizzate per scrittura e lettura
- Gestione collezioni unificate
- Operazioni batch per performance
- Fallback locali per resilienza
- Query vettoriali per ricerca semantica

### Altri Servizi
- **MetadataService**: Gestione metadati documenti
- **WorkflowEngine**: Orchestrazione workflow
- **EventSystem**: Eventi e trigger

## Documentazione Nodi

Per ogni nodo è necessaria documentazione che include:

1. **Panoramica Funzionale**
2. **Configurazione Dettagliata**  
3. **Input/Output Specifications**
4. **Esempi di Utilizzo**
5. **Error Handling**
6. **Performance Considerations**
7. **Integration Notes**

---

*Questa documentazione è in continua evoluzione. Per contribuire o segnalare problemi, consultare il repository PramaIA-Services.*