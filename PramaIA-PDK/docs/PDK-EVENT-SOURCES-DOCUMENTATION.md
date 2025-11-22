# Documentazione Completa sugli Event Sources PDK

## Indice
1. [Introduzione](#introduzione)
2. [Concetti Fondamentali](#concetti-fondamentali)
3. [Struttura di un Event Source](#struttura-di-un-event-source)
4. [Configurazione nel Plugin.json](#configurazione-nel-pluginjson)
5. [Implementazione in Python](#implementazione-in-python)
6. [Sistema di Tag e Filtri](#sistema-di-tag-e-filtri)
7. [Integrazione con i Workflow](#integrazione-con-i-workflow)
8. [Best Practices](#best-practices)
9. [Esempi Completi](#esempi-completi)
10. [Risoluzione Problemi](#risoluzione-problemi)

## Introduzione

Gli Event Sources sono un tipo speciale di plugin nel PDK che generano eventi per avviare workflow automaticamente. A differenza dei nodi di processing standard che elaborano dati all'interno di un workflow esistente, gli Event Sources funzionano in modo autonomo e continuo, monitorando cambiamenti o condizioni specifiche per generare eventi che possono innescare l'esecuzione di workflow.

## Concetti Fondamentali

### Differenza tra Plugin di Processing e Event Sources

| Caratteristica | Plugin di Processing | Event Sources |
|----------------|---------------------|---------------|
| **Scopo principale** | Elaborare dati all'interno di workflow | Generare eventi per avviare workflow |
| **Attivazione** | Viene attivato quando eseguito in un workflow | Funziona autonomamente in background |
| **Ciclo di vita** | Esecuzione singola per ogni invocazione | Persistente, monitoraggio continuo |
| **Tipo nel plugin.json** | `"type": "processing"` (o non specificato) | `"type": "event-source"` |
| **Implementazione** | Funzione `process()` | Classe con metodi `start()`, `stop()`, etc. |

### Tipi di Event Sources

1. **Event Sources basati su File System** - Monitorano directory per nuovi file o modifiche
2. **Event Sources basati su Timer** - Generano eventi a intervalli regolari
3. **Event Sources basati su API** - Interrogano API esterne periodicamente
4. **Event Sources basati su Database** - Monitorano cambiamenti nei database
5. **Event Sources personalizzati** - Implementazioni custom per esigenze specifiche

## Struttura di un Event Source

Un plugin di tipo event-source ha una struttura di directory simile a un plugin standard:

```
my-custom-event-source/
├── plugin.json              # Manifesto del plugin
├── src/
│   └── event_source.py     # Implementazione Python
├── requirements.txt         # Dipendenze Python
└── README.md               # Documentazione
```

### Posizionamento Corretto

Gli Event Sources devono essere collocati nella directory principale dei plugin:

```
PramaIA-PDK/
├── plugins/                     
│   ├── pdf-monitor-event-source/    # Un event source
│   ├── scheduler-event-source/      # Un altro event source
│   └── altri-plugin/
├── server/
├── src/
└── ...
```

## Configurazione nel Plugin.json

La configurazione di un Event Source nel file `plugin.json` differisce da quella di un normale plugin di processing:

```json
{
  "id": "pdf-monitor-event-source",
  "name": "PDF Monitor Event Source",
  "version": "1.0.0",
  "description": "Monitora directory per nuovi file PDF",
  "type": "event-source",
  "lifecycle": "persistent",
  "entryPoint": "src/event_source.py",
  "eventTypes": [
    {
      "id": "pdf_added",
      "name": "PDF Added",
      "description": "Rilevato nuovo file PDF",
      "outputs": [
        {
          "name": "file_path",
          "type": "string",
          "description": "Percorso del file PDF"
        },
        {
          "name": "file_size",
          "type": "number",
          "description": "Dimensione del file in bytes"
        },
        {
          "name": "timestamp",
          "type": "string",
          "description": "Timestamp di rilevamento"
        }
      ]
    },
    {
      "id": "pdf_modified",
      "name": "PDF Modified",
      "description": "File PDF modificato",
      "outputs": [
        {
          "name": "file_path",
          "type": "string",
          "description": "Percorso del file PDF"
        },
        {
          "name": "modification_time",
          "type": "string",
          "description": "Timestamp di modifica"
        }
      ]
    }
  ],
  "configSchema": {
    "title": "PDF Monitor Configuration",
    "type": "object",
    "properties": {
      "monitored_directories": {
        "type": "array",
        "title": "Directory Monitorate",
        "description": "Lista di directory da monitorare",
        "items": {
          "type": "string"
        },
        "default": ["C:/Documenti/PDF"]
      },
      "polling_interval": {
        "type": "number",
        "title": "Intervallo di Polling (secondi)",
        "description": "Frequenza di controllo delle directory",
        "default": 30
      },
      "file_extensions": {
        "type": "array",
        "title": "Estensioni File",
        "description": "Estensioni dei file da monitorare",
        "items": {
          "type": "string"
        },
        "default": [".pdf"]
      }
    },
    "required": ["monitored_directories"]
  },
  "tags": ["pdf", "monitoring", "file-system"]
}
```

### Proprietà Specifiche degli Event Sources

| Proprietà | Descrizione | Obbligatorio |
|-----------|-------------|--------------|
| `type` | Deve essere impostato a `"event-source"` | Sì |
| `lifecycle` | Tipicamente `"persistent"` per event sources continui | Sì |
| `entryPoint` | Percorso al file di implementazione | Sì |
| `eventTypes` | Array di tipi di eventi che questo event source può generare | Sì |
| `configSchema` | Schema per la configurazione dell'event source | Sì |
| `tags` | Array di tag per categorizzare l'event source | No |

### Definizione degli Event Types

Ogni tipo di evento nell'array `eventTypes` deve specificare:

- `id`: Identificativo unico del tipo di evento
- `name`: Nome leggibile del tipo di evento
- `description`: Descrizione dello scopo dell'evento
- `outputs`: Definizione dei dati forniti dall'evento

## Implementazione in Python

L'implementazione di un event source richiede una struttura più complessa rispetto a un processore standard:

```python
"""
PDF Monitor Event Source
Monitora le directory specificate per nuovi file PDF e modifiche.
"""
import logging
import asyncio
import os
import time
import glob
import json
from typing import Dict, Any, List, Callable

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFMonitorEventSource:
    """
    Event Source che monitora le directory per nuovi file PDF.
    """
    
    def __init__(self, config: Dict[str, Any], event_callback: Callable):
        """
        Inizializza l'event source.
        
        Args:
            config: Configurazione dell'event source
            event_callback: Funzione di callback per inviare eventi
        """
        self.config = config
        self.event_callback = event_callback
        self.running = False
        
        # Estrazione parametri di configurazione
        self.monitored_dirs = config.get("monitored_directories", [])
        self.polling_interval = config.get("polling_interval", 30)
        self.file_extensions = config.get("file_extensions", [".pdf"])
        
        # Stato interno per tracciare i file già processati
        self.known_files = {}
        
        logger.info(f"PDF Monitor inizializzato: {len(self.monitored_dirs)} directory, "
                   f"intervallo {self.polling_interval}s")
        
    async def start(self):
        """Avvia l'event source."""
        if self.running:
            logger.warning("Event source già in esecuzione")
            return
            
        self.running = True
        logger.info(f"PDF Monitor avviato. Monitoraggio directory: {self.monitored_dirs}")
        
        # Scansione iniziale per costruire lo stato di base
        await self._scan_directories(initial=True)
        
        try:
            while self.running:
                # Controllo periodico delle directory
                await self._scan_directories(initial=False)
                
                # Attesa prima del prossimo ciclo
                await asyncio.sleep(self.polling_interval)
        except Exception as e:
            logger.error(f"Errore nel PDF Monitor: {str(e)}")
            self.running = False
    
    async def stop(self):
        """Ferma l'event source."""
        logger.info("Arresto PDF Monitor")
        self.running = False
    
    async def _scan_directories(self, initial: bool = False):
        """
        Scansiona le directory monitorate per rilevare nuovi file o modifiche.
        
        Args:
            initial: Se True, è la scansione iniziale e non genera eventi
        """
        try:
            current_files = {}
            
            # Scansiona tutte le directory configurate
            for directory in self.monitored_dirs:
                if not os.path.exists(directory):
                    logger.warning(f"Directory non esistente: {directory}")
                    continue
                
                # Cerca file con le estensioni specificate
                for ext in self.file_extensions:
                    pattern = os.path.join(directory, f"*{ext}")
                    for file_path in glob.glob(pattern):
                        # Raccogli info sul file
                        stat_info = os.stat(file_path)
                        current_files[file_path] = {
                            "size": stat_info.st_size,
                            "mtime": stat_info.st_mtime
                        }
            
            # Se non è la scansione iniziale, genera eventi per nuovi file/modifiche
            if not initial:
                # Controlla nuovi file
                for file_path, info in current_files.items():
                    if file_path not in self.known_files:
                        # Nuovo file rilevato
                        await self._generate_new_file_event(file_path, info)
                    elif info["mtime"] > self.known_files[file_path]["mtime"]:
                        # File modificato
                        await self._generate_modified_file_event(file_path, info)
            
            # Aggiorna lo stato interno
            self.known_files = current_files
            
        except Exception as e:
            logger.error(f"Errore durante la scansione directory: {str(e)}")
    
    async def _generate_new_file_event(self, file_path: str, info: Dict[str, Any]):
        """
        Genera un evento pdf_added per un nuovo file.
        
        Args:
            file_path: Percorso del file PDF
            info: Informazioni sul file
        """
        try:
            event_data = {
                "file_path": file_path,
                "file_size": info["size"],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            # Invia l'evento tramite callback
            await self.event_callback("pdf_added", event_data)
            logger.info(f"Evento pdf_added generato: {file_path}")
            
        except Exception as e:
            logger.error(f"Errore durante la generazione dell'evento pdf_added: {str(e)}")
    
    async def _generate_modified_file_event(self, file_path: str, info: Dict[str, Any]):
        """
        Genera un evento pdf_modified per un file modificato.
        
        Args:
            file_path: Percorso del file PDF
            info: Informazioni sul file
        """
        try:
            event_data = {
                "file_path": file_path,
                "modification_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", 
                                                 time.localtime(info["mtime"]))
            }
            
            # Invia l'evento tramite callback
            await self.event_callback("pdf_modified", event_data)
            logger.info(f"Evento pdf_modified generato: {file_path}")
            
        except Exception as e:
            logger.error(f"Errore durante la generazione dell'evento pdf_modified: {str(e)}")

# Funzione factory per l'inizializzazione
def create_event_source(config, callback):
    """
    Crea e restituisce un'istanza dell'event source.
    
    Args:
        config: Configurazione dell'event source
        callback: Funzione per inviare eventi al sistema
        
    Returns:
        Istanza dell'event source
    """
    return PDFMonitorEventSource(config, callback)
```

### Metodi Richiesti nell'Implementazione

| Metodo | Descrizione | Obbligatorio |
|--------|-------------|--------------|
| `__init__(config, event_callback)` | Inizializza l'event source con configurazione e callback | Sì |
| `start()` | Avvia l'event source | Sì |
| `stop()` | Arresta l'event source | Sì |
| `create_event_source(config, callback)` | Funzione factory a livello di modulo | Sì |

## Sistema di Tag e Filtri

Il PDK supporta un sistema di tag per organizzare e filtrare gli event sources e i loro eventi:

### Tag a Livello di Event Source

I tag a livello di event source aiutano a categorizzare gli event sources per tipo, scopo o dominio:

```json
"tags": ["pdf", "monitoring", "file-system"]
```

### Tag a Livello di Event Type

I tag possono essere aggiunti anche ai singoli tipi di evento:

```json
"eventTypes": [
  {
    "id": "pdf_added",
    "name": "PDF Added",
    "description": "Rilevato nuovo file PDF",
    "tags": ["file-added", "trigger", "ingest"],
    "outputs": [...]
  }
]
```

### Filtri di Eventi

I filtri permettono di associare selettivamente workflow a eventi specifici basati su:

1. **Tag**: Filtrare eventi per tag specifici
2. **Proprietà dell'evento**: Filtrare in base a valori di proprietà dell'evento
3. **Espressioni condizionali**: Combinazioni logiche di condizioni

Esempio di configurazione di filtro in un workflow:

```json
"triggers": [
  {
    "eventSourceId": "pdf-monitor-event-source",
    "eventTypeId": "pdf_added",
    "filters": [
      {
        "field": "file_path",
        "operator": "contains",
        "value": "invoices"
      },
      {
        "field": "file_size",
        "operator": "greaterThan",
        "value": 1024
      }
    ],
    "filterLogic": "AND"
  }
]
```

## Integrazione con i Workflow

Gli event sources possono essere integrati con i workflow in diversi modi:

### Configurazione Automatica

I workflow possono essere configurati per avviarsi automaticamente quando viene generato un evento specifico:

```json
{
  "id": "pdf-processing-workflow",
  "name": "PDF Processing Workflow",
  "description": "Elabora automaticamente nuovi PDF",
  "triggers": [
    {
      "eventSourceId": "pdf-monitor-event-source",
      "eventTypeId": "pdf_added"
    }
  ],
  "nodes": [...]
}
```

### Mappatura dei Dati dell'Evento

I dati dell'evento possono essere mappati a input specifici dei nodi nel workflow:

```json
"triggers": [
  {
    "eventSourceId": "pdf-monitor-event-source",
    "eventTypeId": "pdf_added",
    "mapping": {
      "pdf_parser.input_file": "event.file_path",
      "metadata.timestamp": "event.timestamp"
    }
  }
]
```

### Priorità e Gestione delle Code

È possibile configurare priorità per diversi tipi di eventi:

```json
"triggers": [
  {
    "eventSourceId": "pdf-monitor-event-source",
    "eventTypeId": "pdf_added",
    "priority": "high"
  }
]
```

## Best Practices

1. **Gestione Risorse**: Implementa correttamente i metodi `start()` e `stop()` per garantire una gestione appropriata delle risorse
2. **Gestione Errori**: Usa try-except in tutte le operazioni che potrebbero fallire
3. **Logging**: Aggiungi log dettagliati per facilitare il debugging
4. **Idempotenza**: Assicurati che gli eventi non vengano generati più volte per lo stesso cambiamento
5. **Configurazione Flessibile**: Rendi configurabili tutti i parametri rilevanti
6. **Parallelismo**: Gestisci correttamente l'esecuzione asincrona con `asyncio`
7. **Persistenza Stato**: Implementa meccanismi per persistere lo stato in caso di riavvio
8. **Backoff Esponenziale**: Usa strategie di backoff per gestire errori transitori

## Esempi Completi

### PDF Monitor Event Source

L'esempio sopra rappresenta un event source completo per il monitoraggio di file PDF. Altri esempi comuni includono:

### Scheduler Event Source

```python
"""
Scheduler Event Source
Genera eventi a intervalli pianificati secondo una configurazione cron-like.
"""
import logging
import asyncio
import time
import croniter
import datetime
from typing import Dict, Any, Callable

# [Implementazione completa...]
```

### API Monitor Event Source

```python
"""
API Monitor Event Source
Monitora endpoint API esterni per cambiamenti o nuovi dati.
"""
import logging
import asyncio
import aiohttp
import json
import hashlib
from typing import Dict, Any, Callable

# [Implementazione completa...]
```

## Risoluzione Problemi

### Problemi Comuni e Soluzioni

| Problema | Possibile Causa | Soluzione |
|----------|-----------------|-----------|
| Event source non avviato | Errore nella configurazione | Verifica il file plugin.json e i log del server |
| Eventi non generati | Problema nell'implementazione | Controlla i log per errori nel ciclo di monitoraggio |
| Workflow non avviati | Configurazione trigger errata | Verifica la configurazione dei trigger nel workflow |
| Uso eccessivo CPU/memoria | Polling troppo frequente | Aumenta l'intervallo di polling, ottimizza l'algoritmo |
| Eventi duplicati | Logica di rilevamento incompleta | Implementa un meccanismo di deduplicazione |

### Debugging degli Event Sources

1. **Logging Avanzato**: Aggiungi livelli di logging dettagliati
2. **Modalità Debug**: Implementa una modalità debug che fornisce più informazioni
3. **Verifica Eventi**: Controlla che gli eventi vengano correttamente generati tramite callback
4. **Isolamento**: Testa l'event source in isolamento prima dell'integrazione

---

Per qualsiasi domanda o chiarimento, contatta il team PramaIA.
