# Development Guide - Creazione di Nodi e Event Source

## 1. Introduzione

Questo documento descrive come sviluppare:
1. **Nuovi nodi** per workflow (handler di elaborazione dati)
2. **Nuove sorgenti di evento** (event source) che generano eventi

## 2. Sviluppo di Nuovi Nodi

### 2.1 Cos'è un Nodo

Un nodo è un'unità di computazione con:
- **Input ports**: Ricevono dati
- **Output ports**: Generano dati
- **Config parameters**: Personalizzazione
- **Resolver function**: Logica di elaborazione

### 2.2 Architettura di un Plugin con Nodi

Un plugin è una cartella in `PramaIA-PDK/plugins/` con struttura:

```
my-plugin/
├── package.json              # Metadati plugin
├── nodes.json               # Definizione nodi (OBBLIGATORIO)
├── src/
│   ├── resolvers/
│   │   ├── nodeResolver1.js # Resolver del nodo 1
│   │   └── nodeResolver2.js # Resolver del nodo 2
│   └── utils/
│       └── helpers.js       # Helper functions
└── README.md               # Documentazione
```

### 2.3 Definire i Nodi - nodes.json

Il file `nodes.json` definisce i nodi e i loro schemi:

```json
{
  "pluginName": "my-text-plugin",
  "pluginId": "my-text-plugin-v1",
  "description": "Plugin per elaborazione testo",
  "version": "1.0.0",
  "nodes": [
    {
      "nodeId": "text_uppercase_node",
      "nodeType": "text_uppercase",
      "name": "Convert to Uppercase",
      "description": "Converte testo in maiuscole",
      "category": "text-processing",
      "tags": ["text", "transform", "uppercase"],
      "inputs": [
        {
          "name": "text_input",
          "type": "text",
          "required": true,
          "description": "Testo da convertire"
        }
      ],
      "outputs": [
        {
          "name": "text_output",
          "type": "text",
          "description": "Testo in maiuscole"
        }
      ],
      "config": {
        "properties": {
          "preserve_special": {
            "type": "boolean",
            "default": true,
            "description": "Preserva caratteri speciali"
          },
          "max_length": {
            "type": "number",
            "default": 10000,
            "description": "Lunghezza massima input"
          }
        }
      }
    }
  ]
}
```

**Dettagli chiave**:
- `nodeId`: Identificatore univoco del nodo (namespace plugin)
- `nodeType`: Tipo per esecuzione
- `inputs`: Array di porte input (tipo, required)
- `outputs`: Array di porte output (tipo)
- `config`: Schema JSON per parametri di configurazione
- `tags`: Per categorizzazione e filtering

### 2.4 Implementare il Resolver

Il resolver è la funzione che esegue la logica del nodo:

**File: `src/resolvers/textUppercaseResolver.js`**

```javascript
/**
 * Resolver per nodo Text Uppercase
 * Converte testo in maiuscole
 */
async function textUppercaseResolver(inputs, config) {
  // 1. Validazione input
  if (!inputs.text_input) {
    throw new Error("text_input è obbligatorio");
  }
  
  const text = String(inputs.text_input);
  
  // 2. Applicare config
  if (text.length > config.max_length) {
    throw new Error(`Input eccede max_length di ${config.max_length}`);
  }
  
  // 3. Elaborazione
  let result = text.toUpperCase();
  
  // 4. Returnare output
  return {
    text_output: result
  };
}

module.exports = { textUppercaseResolver };
```

**Signature Resolver**:
```javascript
async function resolver(inputs, config, context) {
  // inputs: {portName: value, ...}
  // config: {configKey: value, ...}
  // context: {workflowId, nodeId, executionId, ...}
  
  // Deve returnare: {outputPortName: value, ...}
  return outputs;
}
```

**Context Disponibile**:
- `workflowId`: ID del workflow in esecuzione
- `nodeId`: ID del nodo in esecuzione
- `executionId`: ID unico esecuzione
- `pdk`: Riferimento al server PDK per chiamate intra-nodo
- `logger`: Logger centralizzato

### 2.5 Registrare il Resolver nel Plugin

**File: `src/resolvers/index.js`**

```javascript
const { textUppercaseResolver } = require('./textUppercaseResolver');
const { textJoinResolver } = require('./textJoinResolver');

const resolvers = {
  'text_uppercase': textUppercaseResolver,
  'text_join': textJoinResolver
};

module.exports = { resolvers };
```

### 2.6 Integrare nel PDK Server

Il PDK Server scopre automaticamente i plugin quando:

1. Cartella plugin esiste in `PramaIA-PDK/plugins/`
2. Contiene `nodes.json` valido
3. Server PDK è riavviato (o hot-reload abilitato)

**Verifica**: 
```bash
# PDK Server chiama automaticamente
GET http://127.0.0.1:3001/api/nodes

# Nodo dovrebbe essere nella lista
{
  "nodeId": "text_uppercase_node",
  "nodeType": "text_uppercase",
  ...
}
```

### 2.7 Eseguire un Nodo da Workflow

Quando il WorkflowEngine incontra un nodo:

```python
# Backend chiama PDK
response = pdk_client.execute_node(
    node_type="text_uppercase",
    inputs={"text_input": "hello world"},
    config={"max_length": 10000}
)
# Ritorna: {"text_output": "HELLO WORLD"}
```

### 2.8 Esempio Completo: PDF Extractor Plugin

**Structure**:
```
pdf-extractor-plugin/
├── package.json
├── nodes.json
├── src/
│   ├── resolvers/
│   │   ├── pdfExtractResolver.js
│   │   └── index.js
│   └── utils/
│       └── pdfHelper.js
└── README.md
```

**nodes.json**:
```json
{
  "pluginName": "pdf-extractor-plugin",
  "pluginId": "pdf-extractor-v1",
  "nodes": [
    {
      "nodeId": "pdf_extract_text_node",
      "nodeType": "pdf_extract_text",
      "name": "Extract Text from PDF",
      "inputs": [
        {
          "name": "pdf_document",
          "type": "pdf",
          "required": true
        }
      ],
      "outputs": [
        {
          "name": "extracted_text",
          "type": "text"
        },
        {
          "name": "page_count",
          "type": "number"
        }
      ],
      "config": {
        "properties": {
          "max_pages": {
            "type": "number",
            "default": 100
          },
          "ocr_enabled": {
            "type": "boolean",
            "default": false
          }
        }
      }
    }
  ]
}
```

**pdfExtractResolver.js**:
```javascript
const pdf = require('pdf-parse');
const { extractWithOCR } = require('../utils/pdfHelper');

async function pdfExtractTextResolver(inputs, config, context) {
  const pdfBuffer = inputs.pdf_document;
  
  try {
    // Parse PDF
    const pdfData = await pdf(pdfBuffer);
    const text = pdfData.text;
    const pageCount = pdfData.numpages;
    
    // OCR se abilitato
    let finalText = text;
    if (config.ocr_enabled && !text.trim()) {
      finalText = await extractWithOCR(pdfBuffer);
    }
    
    return {
      extracted_text: finalText,
      page_count: pageCount
    };
  } catch (error) {
    context.logger.error(`PDF extraction failed: ${error.message}`);
    throw error;
  }
}

module.exports = { pdfExtractTextResolver };
```

### 2.9 Testing dei Nodi

**Test Manuale**:
```bash
# 1. Verificare nodo registrato
curl http://127.0.0.1:3001/api/nodes | grep "text_uppercase"

# 2. Eseguire nodo direttamente
curl -X POST http://127.0.0.1:3001/api/nodes/text_uppercase/execute \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"text_input": "hello"},
    "config": {"max_length": 10000}
  }'

# Response: {"text_output": "HELLO"}
```

**Test Unitario** (Mocha/Jest):
```javascript
const { textUppercaseResolver } = require('../src/resolvers/textUppercaseResolver');

describe('Text Uppercase Resolver', () => {
  it('converts text to uppercase', async () => {
    const result = await textUppercaseResolver(
      { text_input: 'hello' },
      { max_length: 10000 }
    );
    assert.equal(result.text_output, 'HELLO');
  });
  
  it('throws on exceeding max_length', async () => {
    try {
      await textUppercaseResolver(
        { text_input: 'a'.repeat(11) },
        { max_length: 10 }
      );
      assert.fail('Should have thrown');
    } catch (e) {
      assert(e.message.includes('max_length'));
    }
  });
});
```

## 3. Sviluppo di Nuove Event Source

### 3.1 Cos'è un Event Source

Un Event Source è un componente che:
1. Monitora una condizione
2. Genera eventi quando cambia
3. Invia eventi al Backend via `/api/events/process`

### 3.2 Architettura di un Event Source

**Struttura minimale**:

```
my-event-source/
├── main.py                  # Entry point
├── event_source.py         # Logica principale
├── config.py               # Configurazione
└── requirements.txt        # Dipendenze
```

### 3.3 Implementare un Event Source - Esempio

**Scenario**: Event source che monitora cambiamenti in una directory

**File: `my-event-source/main.py`**

```python
import asyncio
import os
from event_source import DirectoryMonitorEventSource

async def main():
    # Configurazione
    folder_to_monitor = os.getenv("MONITOR_FOLDER", "./documents")
    backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    
    # Crea event source
    event_source = DirectoryMonitorEventSource(
        folder_path=folder_to_monitor,
        backend_url=backend_url
    )
    
    # Avvia monitoraggio
    await event_source.start()

if __name__ == "__main__":
    asyncio.run(main())
```

**File: `my-event-source/event_source.py`**

```python
import asyncio
import os
import hashlib
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DirectoryMonitorEventSource:
    def __init__(self, folder_path: str, backend_url: str):
        self.folder_path = folder_path
        self.backend_url = backend_url
        self.file_hashes: Dict[str, str] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def start(self):
        """Avvia il monitoraggio della directory"""
        self.session = aiohttp.ClientSession()
        
        try:
            # Initial scan
            await self._initial_scan()
            
            # Periodic monitoring loop
            while True:
                await self._check_changes()
                await asyncio.sleep(5)  # Check ogni 5 secondi
        finally:
            await self.session.close()
    
    async def _initial_scan(self):
        """Scansione iniziale della directory"""
        logger.info(f"Initial scan of {self.folder_path}")
        for file_path in Path(self.folder_path).rglob("*"):
            if file_path.is_file():
                file_hash = self._calculate_hash(file_path)
                self.file_hashes[str(file_path)] = file_hash
    
    async def _check_changes(self):
        """Controlla cambiamenti nella directory"""
        current_files = {
            str(f): self._calculate_hash(f)
            for f in Path(self.folder_path).rglob("*")
            if f.is_file()
        }
        
        # Nuovi file
        for file_path, file_hash in current_files.items():
            if file_path not in self.file_hashes:
                await self._send_event("file_created", file_path)
                self.file_hashes[file_path] = file_hash
        
        # File modificati
        for file_path, old_hash in list(self.file_hashes.items()):
            if file_path in current_files:
                new_hash = current_files[file_path]
                if old_hash != new_hash:
                    await self._send_event("file_modified", file_path)
                    self.file_hashes[file_path] = new_hash
        
        # File eliminati
        for file_path in list(self.file_hashes.keys()):
            if file_path not in current_files:
                await self._send_event("file_deleted", file_path)
                del self.file_hashes[file_path]
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calcola hash file per rilevare modifiche"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    async def _send_event(self, event_type: str, file_path: str):
        """Invia evento al Backend"""
        event_payload = {
            "event_type": f"directory_monitor_{event_type}",
            "source": "directory-monitor-event-source",
            "data": {
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "source_folder": self.folder_path,
                "event_source_id": "directory-monitor-1"
            }
        }
        
        try:
            async with self.session.post(
                f"{self.backend_url}/api/events/process",
                json=event_payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Event sent: {event_type} for {file_path}")
                else:
                    logger.error(f"Failed to send event: {await resp.text()}")
        except Exception as e:
            logger.error(f"Error sending event: {e}")
            # Implement retry logic here if needed
```

**File: `my-event-source/requirements.txt`**

```
aiohttp==3.9.0
python-dotenv==1.0.0
```

### 3.4 Caratteristiche Consigliate

Un buon event source implementa:

**1. Retry Logic**:
```python
async def _send_event_with_retry(self, event, max_retries=3):
    for attempt in range(max_retries):
        try:
            await self._send_event(event)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return False
```

**2. Local Buffering**:
```python
import sqlite3
from datetime import datetime

class EventBuffer:
    def __init__(self, db_path="events.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                event_type TEXT,
                payload JSON,
                created_at TEXT,
                sent BOOLEAN DEFAULT 0
            )
        """)
        conn.commit()
    
    def add_event(self, event_type, payload):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload), datetime.utcnow().isoformat())
        )
        conn.commit()
    
    def get_unsent_events(self, limit=100):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT id, event_type, payload FROM events WHERE sent=0 LIMIT ?", (limit,))
        return cursor.fetchall()
    
    def mark_sent(self, event_id):
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE events SET sent=1 WHERE id=?", (event_id,))
        conn.commit()
```

**3. Health Check Endpoint**:
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "event_source": "directory-monitor",
        "buffered_events": len(event_buffer.get_unsent_events())
    })
```

### 3.5 Configurazione Event Source

Via variabili ambiente:

```bash
# Directory Monitor Event Source
MONITOR_FOLDER=/path/to/monitor
BACKEND_URL=http://127.0.0.1:8000
RECONCILIATION_INTERVAL=3600
MIN_DISCONNECTION_FOR_RECONCILE=1
```

### 3.6 Registrare Event Source

1. **Creare cartella**: `my-event-source/`
2. **Implementare logica**: Inviare eventi a `/api/events/process`
3. **Configurare**: Variabili ambiente
4. **Avviare**: Script di lancio separato o integrato in `start-all.ps1`

### 3.7 Integrare in start-all.ps1

```powershell
# Aggiungere a start-all.ps1
function Start-DirectoryMonitor {
    $env:MONITOR_FOLDER = "C:\monitored_folder"
    $env:BACKEND_URL = "http://127.0.0.1:8000"
    
    cd ".\my-event-source"
    & python main.py
}

# Nel Main
Start-DirectoryMonitor
```

## 4. Debugging durante lo Sviluppo

### 4.1 Testing Nodi Isolati

```bash
# Test diretto resolver
node -e "
const resolver = require('./src/resolvers/textUppercaseResolver.js');
resolver.textUppercaseResolver({text_input: 'test'}, {max_length: 100})
  .then(r => console.log(r))
  .catch(e => console.error(e));
"
```

### 4.2 Osservare Esecuzione Workflow

```bash
# Logare chiamate PDK
export PDK_LOG_LEVEL=DEBUG

# Logare backend
export LOGLEVEL=DEBUG
```

### 4.3 Verificare Type Matching

```python
# Nel backend
from backend.engine.workflow_engine import WorkflowEngine

# Aggiungere nel engine:
def _validate_connection(self, from_node, to_node, from_port, to_port):
    from_type = from_node.outputs[from_port].type
    to_type = to_node.inputs[to_port].type
    if from_type != to_type:
        raise ValidationError(
            f"Type mismatch: {from_node.id}.{from_port} ({from_type}) "
            f"→ {to_node.id}.{to_port} ({to_type})"
        )
```

## 5. Best Practices

### Per Nodi
- ✅ Validare tutti gli input
- ✅ Usare type hints in JavaScript/TypeScript
- ✅ Loggare step di elaborazione importanti
- ✅ Gestire errori esplicitamente
- ✅ Testare con data boundaries

### Per Event Source
- ✅ Implementare retry con backoff esponenziale
- ✅ Bufferare eventi localmente
- ✅ Implementare health check
- ✅ Loggare tutti i fallimenti di invio
- ✅ Non fare assunzioni su disponibilità backend

### Generale
- ✅ Documentare schema input/output
- ✅ Fornire esempi di utilizzo
- ✅ Testare integrazione end-to-end
- ✅ Versionare plugin/event source
- ✅ Mantenere retrocompatibilità

---

**Ultimo Aggiornamento**: 18 Novembre 2025  
**Versione**: 1.0
