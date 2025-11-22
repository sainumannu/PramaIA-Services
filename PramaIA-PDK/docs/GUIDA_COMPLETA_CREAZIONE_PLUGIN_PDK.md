# Guida Completa alla Creazione di Plugin PDK

> **Nota**: Questo è il documento principale di riferimento per la creazione di plugin PDK. Per un indice completo di tutta la documentazione, vedere [README.md](./README.md).

## Indice
1. [Introduzione](#introduzione)
2. [Struttura di un Plugin](#struttura-di-un-plugin)
3. [Configurazione del Plugin (plugin.json)](#configurazione-del-plugin-pluginjson)
4. [Implementazione dei Processori di Nodo](#implementazione-dei-processori-di-nodo)
5. [Event Sources](#event-sources)
6. [Icone e UI](#icone-e-ui)
7. [Installazione e Deployment](#installazione-e-deployment)
8. [Testing e Debugging](#testing-e-debugging)
9. [Best Practices](#best-practices)
10. [FAQ e Risoluzione Problemi](#faq-e-risoluzione-problemi)

## Introduzione

PramaIA-PDK (Plugin Development Kit) è un framework per la creazione di plugin modulari che estendono le funzionalità del sistema PDK. Ogni plugin può contenere uno o più nodi che eseguono operazioni specifiche all'interno di un workflow.

Questa guida fornisce tutte le informazioni necessarie per creare, implementare e testare un plugin PDK funzionante.

## Struttura di un Plugin

Un plugin PDK richiede una struttura specifica di directory e file:

```
nome-plugin/                  # Directory principale del plugin
├── plugin.json               # Configurazione principale del plugin
├── README.md                 # Documentazione generale (opzionale ma consigliato)
├── requirements.txt          # Dipendenze Python (se applicabile)
└── src/                      # Directory per i file di implementazione
    ├── plugin.py             # Punto di ingresso opzionale (utilizzato in alcuni casi)
    ├── nome_processore1.py   # Implementazione del primo processore
    ├── nome_processore2.py   # Implementazione del secondo processore
    └── ...                   # Altri file di implementazione
```

> **IMPORTANTE**: La struttura esatta delle directory è cruciale. Il plugin deve essere collocato nella directory `plugins/` del PDK e deve seguire questo formato.

### Posizione Corretta dei Plugin

I plugin devono essere posizionati nella directory `plugins` della root del PDK:

```
PramaIA-PDK/
├── plugins/                  # TUTTI I PLUGIN DEVONO ESSERE QUI
│   ├── plugin-1/
│   ├── plugin-2/
│   └── il-tuo-nuovo-plugin/  # Crea qui il tuo plugin
├── server/
├── src/
└── ...
```

## Configurazione del Plugin (plugin.json)

Il file `plugin.json` è il manifesto del plugin e definisce tutte le sue proprietà, inclusi i nodi che il plugin fornisce.

### Esempio Completo di plugin.json

```json
{
  "name": "pdf-monitor-plugin",
  "version": "1.0.0",
  "description": "Plugin per il monitoraggio e la gestione dei documenti PDF",
  "author": "PramaIA Team",
  "license": "MIT",
  "pdk_version": "^1.0.0",
  "engine_compatibility": "^1.0.0",
  "nodes": [
    {
      "id": "metadata_manager",
      "name": "MetadataManager",
      "type": "processing",
      "category": "PDF Monitor",
      "description": "Gestisce i metadati dei documenti",
      "icon": "📋",
      "color": "#4CAF50",
      "entry": "src/metadata_manager_processor.py"
    },
    {
      "id": "event_logger",
      "name": "EventLogger",
      "type": "processing",
      "category": "PDF Monitor",
      "description": "Registra eventi e attività del sistema",
      "icon": "📊",
      "color": "#2196F3",
      "entry": "src/event_logger_processor.py"
    }
  ],
  "dependencies": {
    "pymupdf": "^1.21.0",
    "pyyaml": "^6.0.0"
  }
}
```

### Proprietà Principali del plugin.json

| Proprietà | Descrizione | Obbligatorio |
|-----------|-------------|--------------|
| `name` | Nome identificativo del plugin | Sì |
| `version` | Versione del plugin (formato semver) | Sì |
| `description` | Breve descrizione delle funzionalità | Sì |
| `author` | Nome dell'autore o dell'organizzazione | No |
| `license` | Tipo di licenza del plugin | No |
| `pdk_version` | Versione del PDK compatibile | Sì |
| `nodes` | Array di definizioni dei nodi forniti dal plugin | Sì |
| `dependencies` | Dipendenze Python richieste | No |

### Definizione dei Nodi nel plugin.json

Ogni nodo definito nell'array `nodes` deve avere le seguenti proprietà:

| Proprietà | Descrizione | Obbligatorio |
|-----------|-------------|--------------|
| `id` | Identificativo unico del nodo | Sì |
| `name` | Nome visualizzato nell'interfaccia | Sì |
| `type` | Tipo di nodo (processing, input, output) | Sì |
| `category` | Categoria per raggruppamento nell'UI | Sì |
| `description` | Descrizione delle funzionalità | Sì |
| `icon` | Emoji Unicode per rappresentare il nodo | Sì |
| `color` | Colore esadecimale del nodo nell'UI | Sì |
| `entry` | Percorso al file di implementazione | Sì |
| `inputs` | Array di definizioni degli input (opzionale) | No |
| `outputs` | Array di definizioni degli output (opzionale) | No |
| `configSchema` | Schema per la configurazione del nodo | No |

## Implementazione dei Processori di Nodo

Ogni nodo definito nel `plugin.json` deve avere un corrispondente file di implementazione in Python che gestisce la logica del nodo.

### Esempio di Implementazione Base di un Processore

```python
"""
Metadata Manager Processor per PDK.
Gestisce operazioni sui metadati dei documenti.
"""

import logging
from typing import Dict, Any

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process(inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Elabora le operazioni sui metadati in base all'operazione specificata.
    
    Args:
        inputs: Dizionario contenente i parametri dell'operazione
        config: Configurazione del nodo
        
    Returns:
        Dizionario con i risultati dell'operazione
    """
    try:
        # Estrai parametri operazione
        operation = inputs.get("operation", "update")
        current_metadata = inputs.get("current_metadata", {})
        
        # Logica del processore
        # ...
        
        # Risultato
        return {
            "status": "success",
            "metadata": current_metadata,
            "operation": operation
        }
            
    except Exception as e:
        logger.error(f"Errore in MetadataManager: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }
```

### Struttura della Funzione `process`

La funzione `process` è il punto di ingresso principale per l'elaborazione del nodo:

```python
async def process(inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    # Implementazione...
```

- `inputs`: Dizionario contenente i dati di input al nodo
- `config`: Dizionario contenente la configurazione del nodo
- Valore di ritorno: Dizionario con i risultati dell'elaborazione

## Event Sources

Gli Event Sources sono plugin speciali che generano eventi per avviare workflow automaticamente, a differenza dei nodi di processing standard che elaborano dati all'interno di un workflow.

### Tipi di Plugin nel PDK

Il PDK supporta principalmente due tipi di plugin, definiti dal campo `type` nel file `plugin.json`:

1. **Plugin di elaborazione (processing)** - Il valore predefinito, se non specificato
   - Forniscono nodi per l'elaborazione all'interno dei workflow
   - Esempi: pdf-semantic-complete-plugin, internal-processors-plugin

2. **Plugin event-source** - Specificato come `"type": "event-source"`
   - Generano eventi che possono avviare workflow
   - Funzionano in modo autonomo e continuo
   - Esempi: pdf-monitor-event-source, scheduler-event-source

### Struttura di un Event Source

Un plugin di tipo event-source ha una struttura simile a un plugin normale:

```
my-custom-event-source/
├── plugin.json              # Manifesto del plugin
├── src/
│   └── event_source.py     # Implementazione Python
├── requirements.txt         # Dipendenze Python
└── README.md               # Documentazione
```

### Esempio di plugin.json per Event Source

```json
{
  "id": "my-custom-event-source",
  "name": "My Custom Event Source",
  "version": "1.0.0",
  "description": "Custom event source per [scopo specifico]",
  "type": "event-source",
  "lifecycle": "persistent",
  "entryPoint": "src/event_source.py",
  "eventTypes": [
    {
      "id": "custom_event",
      "name": "Custom Event",
      "description": "Evento personalizzato",
      "outputs": [
        {
          "name": "event_data",
          "type": "object",
          "description": "Dati dell'evento"
        },
        {
          "name": "timestamp",
          "type": "string",
          "description": "Timestamp ISO dell'evento"
        }
      ]
    }
  ],
  "configSchema": {
    "title": "Custom Event Source Configuration",
    "type": "object",
    "properties": {
      "interval_seconds": {
        "type": "number",
        "title": "Intervallo (secondi)",
        "description": "Intervallo di polling in secondi",
        "default": 60
      },
      "custom_param": {
        "type": "string",
        "title": "Parametro Personalizzato",
        "description": "Descrizione del parametro",
        "default": "default_value"
      }
    },
    "required": ["interval_seconds"]
  }
}
```

### Implementazione Python di un Event Source

L'implementazione di un event source richiede una classe con metodi specifici:

```python
"""
Event Source personalizzato per il PDK.
"""
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyCustomEventSource:
    """
    Event Source personalizzato che genera eventi in base a criteri specifici.
    """
    
    def __init__(self, config: Dict[str, Any], event_callback):
        """
        Inizializza l'event source.
        
        Args:
            config: Configurazione dell'event source
            event_callback: Funzione di callback per inviare eventi
        """
        self.config = config
        self.event_callback = event_callback
        self.running = False
        self.interval = config.get("interval_seconds", 60)
        self.custom_param = config.get("custom_param", "default_value")
        logger.info(f"Event source inizializzato con intervallo {self.interval}s")
        
    async def start(self):
        """Avvia l'event source."""
        if self.running:
            logger.warning("Event source già in esecuzione")
            return
            
        self.running = True
        logger.info("Event source avviato")
        
        try:
            while self.running:
                # Logica per generare eventi
                await self.check_for_events()
                
                # Attesa prima del prossimo ciclo
                await asyncio.sleep(self.interval)
        except Exception as e:
            logger.error(f"Errore nell'event source: {str(e)}")
            self.running = False
    
    async def stop(self):
        """Ferma l'event source."""
        logger.info("Arresto event source")
        self.running = False
    
    async def check_for_events(self):
        """
        Controlla se ci sono eventi da generare e li invia tramite callback.
        Questo metodo contiene la logica principale dell'event source.
        """
        try:
            # Esempio: genera un evento di esempio
            current_time = time.time()
            
            # Logica per decidere se generare un evento
            # Ad esempio, ogni 5 esecuzioni
            if int(current_time) % (self.interval * 5) < self.interval:
                # Crea l'evento
                event_data = {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "source": "my_custom_event_source",
                    "data": {
                        "value": current_time,
                        "custom_param": self.custom_param
                    }
                }
                
                # Invia l'evento tramite callback
                await self.event_callback("custom_event", event_data)
                logger.info(f"Evento generato: {event_data}")
                
        except Exception as e:
            logger.error(f"Errore durante il controllo eventi: {str(e)}")

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
    return MyCustomEventSource(config, callback)
```

### Integrazione di Event Sources con Workflow

Gli event sources possono avviare workflow in diversi modi:

1. **Trigger automatico**: Un workflow può essere configurato per avviarsi automaticamente quando viene generato un evento specifico
2. **Associazione esplicita**: Nella configurazione del workflow, è possibile specificare quale event source e quale tipo di evento deve avviarlo
3. **Filtri di eventi**: È possibile filtrare gli eventi in base a criteri specifici prima di avviare un workflow

### Sistema di Tag per Event Sources

Il sistema PDK supporta tag configurabili per organizzare e filtrare gli event sources:

- **Event Source Level**: Tag per identificare categorie di event sources (`["pdf", "monitoring", "file-system"]`)
- **Event Type Level**: Tag per identificare tipi di eventi (`["file-added", "trigger", "ingest"]`)

## Icone e UI

### Formato delle Icone

Le icone dei nodi devono essere specificate come emoji Unicode nel campo `icon` del nodo nel file `plugin.json`. **Non utilizzare nomi di icone testuali** (come "tag", "database", ecc.) poiché non verranno riconosciuti dal sistema.

### Esempi di Emoji Corrette

| Descrizione | Emoji | Codice da Usare |
|-------------|-------|-----------------|
| Documento | 📄 | `"icon": "📄"` |
| Database | 🗃️ | `"icon": "🗃️"` |
| Grafico | 📊 | `"icon": "📊"` |
| Appunti | 📋 | `"icon": "📋"` |
| Forbici (split) | ✂️ | `"icon": "✂️"` |
| Cervello (AI) | 🧠 | `"icon": "🧠"` |
| Lente d'ingrandimento | 🔍 | `"icon": "🔍"` |
| Salvataggio | 💾 | `"icon": "💾"` |
| Robot (LLM) | 🤖 | `"icon": "🤖"` |

> **IMPORTANTE**: Usa sempre emoji Unicode e non testo descrittivo. Utilizza emoji semplici e largamente supportate per garantire la compatibilità.

## Installazione e Deployment

### Procedura di Installazione

1. Crea la struttura delle directory del plugin nella cartella `plugins` del PDK:

   ```powershell
   # Esempio in PowerShell
   $pluginName = "nome-plugin"
   $pluginPath = "C:\PramaIA\PramaIA-PDK\plugins\$pluginName"
   
   # Crea la struttura base
   New-Item -Path $pluginPath -ItemType Directory
   New-Item -Path "$pluginPath\src" -ItemType Directory
   ```

2. Crea il file `plugin.json` nella root del plugin con la configurazione appropriata

3. Implementa i file dei processori nella directory `src/`

4. Se necessario, crea un file `requirements.txt` con le dipendenze Python

5. Riavvia il server PDK per caricare il nuovo plugin

### Verificare l'Installazione

Per verificare che il plugin sia stato caricato correttamente:

1. Controlla i log del server PDK per eventuali errori di caricamento
2. Verifica che i nodi siano visibili nell'interfaccia utente del PDK
3. Testa la funzionalità dei nodi in un workflow semplice

## Testing e Debugging

### Debugging dei Nodi

Per debuggare problemi con i nodi:

1. Aggiungi log dettagliati nel codice del processore:

   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   logger.info(f"Elaborazione iniziata con input: {inputs}")
   ```

2. Controlla i log del server PDK per messaggi di errore o avvisi

3. Usa un workflow di test semplice per verificare il funzionamento del nodo

### Problemi Comuni e Soluzioni

| Problema | Possibile Causa | Soluzione |
|----------|-----------------|-----------|
| Nodo non visibile nell'UI | Plugin non caricato correttamente | Verifica la struttura delle directory e il formato del plugin.json |
| Icona non visualizzata | Formato icona non valido | Usa emoji Unicode invece di nomi testuali |
| Errore durante l'esecuzione | Problema nell'implementazione del processore | Controlla i log per messaggi di errore specifici |
| Dipendenze mancanti | Pacchetti Python non installati | Aggiungi le dipendenze al file requirements.txt |

## Best Practices

1. **Struttura Coerente**: Segui sempre la struttura standard del plugin
2. **Nomi Descrittivi**: Usa nomi chiari e descrittivi per i nodi e i plugin
3. **Gestione Errori**: Implementa una gestione degli errori robusta nei processori
4. **Logging Appropriato**: Aggiungi log informativi per facilitare il debugging
5. **Documenta**: Crea documentazione chiara per gli utenti del plugin
6. **Tipi di Dati**: Usa type hints in Python per migliorare la manutenibilità

## FAQ e Risoluzione Problemi

### Quali sono i tipi di nodi supportati?
I tipi principali sono `processing`, `input`, e `output`. La maggior parte dei nodi personalizzati sarà di tipo `processing`.

### Come posso aggiungere parametri di configurazione a un nodo?
Usa il campo `configSchema` nella definizione del nodo per specificare lo schema di configurazione secondo lo standard JSON Schema.

### Perché non vedo il mio nodo nell'interfaccia?
Verifica che:
1. Il plugin sia nella directory corretta (`plugins/`)
2. Il file `plugin.json` sia formattato correttamente
3. L'implementazione del processore esista nel percorso specificato nel campo `entry`
4. Il server PDK sia stato riavviato dopo l'installazione del plugin

### Come posso testare un nodo senza creare un workflow completo?
Crea un workflow minimo con solo il nodo da testare e nodi di input/output necessari per fornire dati e visualizzare i risultati.

### Posso usare librerie Python esterne nei miei processori?
Sì, puoi usare qualsiasi libreria Python. Assicurati di specificarle nel file `requirements.txt` del plugin.

---

## Esempi di Plugin Funzionanti

Per riferimento, puoi esaminare i seguenti plugin esistenti:

- `pdf-semantic-complete-plugin`: Plugin completo per elaborazione semantica PDF
- `internal-processors-plugin`: Plugin con processori di base per manipolazione testo

---

Per assistenza o segnalazione di problemi, contatta il team PramaIA.
