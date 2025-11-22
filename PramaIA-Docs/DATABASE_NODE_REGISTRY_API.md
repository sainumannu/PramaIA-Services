# Database Node Registry API Documentation

## 🎯 Overview

Il **DatabaseNodeRegistry** sostituisce il precedente NodeRegistry in-memory con un sistema basato su database che offre:

- **Gestione runtime** dei tipi di nodo
- **Auto-discovery** dei plugin PDK
- **Mapping automatico** legacy → modern
- **Analytics e monitoring**
- **API per registrazione dinamica**

---

## 🗃️ Database Schema

### **NodeType**
Tabella principale per i tipi di nodi disponibili.

```sql
CREATE TABLE node_types (
    id INTEGER PRIMARY KEY,
    node_type VARCHAR(100) UNIQUE,           -- Nome tipo nodo (es: "document_input_node")
    plugin_id VARCHAR(100),                  -- ID plugin PDK (NULL per nodi nativi)
    processor_class VARCHAR(200),            -- Classe processore (es: "PDKProxyProcessor")
    display_name VARCHAR(200),               -- Nome visualizzato
    description TEXT,                        -- Descrizione nodo
    is_active BOOLEAN DEFAULT TRUE,          -- Nodo attivo/disattivato
    is_legacy BOOLEAN DEFAULT FALSE,         -- Flag per nodi deprecati
    created_at DATETIME,
    updated_at DATETIME,
    config_schema JSON,                      -- Schema configurazione
    input_schema JSON,                       -- Schema input
    output_schema JSON,                      -- Schema output
    category VARCHAR(50),                    -- Categoria (input, output, processing, etc.)
    version VARCHAR(20) DEFAULT "1.0.0",
    author VARCHAR(100)
);
```

### **NodeTypeMapping**
Mapping tra nodi legacy e moderni per compatibilità.

```sql
CREATE TABLE node_type_mappings (
    id INTEGER PRIMARY KEY,
    legacy_type_id INTEGER REFERENCES node_types(id),
    modern_type_id INTEGER REFERENCES node_types(id),
    auto_migrate BOOLEAN DEFAULT TRUE,       -- Migrazione automatica abilitata
    migration_notes TEXT,
    is_deprecated BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    created_by VARCHAR(100)
);
```

### **PluginRegistry**
Registry dei plugin PDK attivi.

```sql
CREATE TABLE plugin_registry (
    id INTEGER PRIMARY KEY,
    plugin_id VARCHAR(100) UNIQUE,          -- ID plugin (es: "core-input-plugin")
    plugin_name VARCHAR(200),               -- Nome plugin
    plugin_version VARCHAR(20),             -- Versione
    base_url VARCHAR(500),                  -- URL PDK server
    api_key VARCHAR(100),
    config JSON,
    is_active BOOLEAN DEFAULT TRUE,
    last_ping DATETIME,
    status VARCHAR(20) DEFAULT "unknown",   -- online, offline, error
    registered_at DATETIME,
    registered_by VARCHAR(100),
    description TEXT,
    author VARCHAR(100)
);
```

---

## 🔧 Core API Methods

### **get_processor(node_type: str)**
Ottiene il processore per un tipo di nodo con fallback automatico.

```python
from backend.engine.db_node_registry import db_node_registry

# Nodo moderno
processor = db_node_registry.get_processor("document_input_node")

# Nodo legacy (auto-mappato)
processor = db_node_registry.get_processor("PDFInput")  # → document_input_node
```

**Comportamento:**
1. Cerca il nodo diretto nel database
2. Se non trovato, cerca mapping legacy → modern
3. Se trovato mapping, richiama ricorsivamente con il tipo moderno
4. Crea e cache il processore appropriato
5. Solleva `ValueError` se nodo non supportato

### **get_supported_node_types()**
Ottiene lista di tutti i tipi di nodi supportati.

```python
supported = db_node_registry.get_supported_node_types()
# ['document_input_node', 'pdf_text_extractor', 'chroma_vector_store', ...]
```

### **is_node_type_supported(node_type: str)**
Verifica se un tipo di nodo è supportato.

```python
is_supported = db_node_registry.is_node_type_supported("PDFInput")  # True (mappato)
```

---

## 🚀 Runtime Registration API

### **register_node_type()**
Registra un nuovo tipo di nodo runtime.

```python
await db_node_registry.register_node_type(
    node_type="my_custom_processor",
    processor_class="PDKProxyProcessor",
    plugin_id="my-custom-plugin",
    display_name="My Custom Processor",
    description="Processore personalizzato per...",
    category="processing",
    version="1.0.0",
    author="My Company",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string"}
        }
    },
    output_schema={
        "type": "object", 
        "properties": {
            "result": {"type": "string"}
        }
    }
)
```

### **create_legacy_mapping()**
Crea mapping legacy → modern per compatibilità.

```python
await db_node_registry.create_legacy_mapping(
    legacy_type="OldTextProcessor",
    modern_type="text_processor",
    auto_migrate=True
)
```

---

## 🔌 Plugin Auto-Discovery

Il sistema scopre automaticamente i plugin PDK e registra i loro nodi.

### **Processo di Discovery:**
1. Query al PDK Server: `GET /api/plugins`
2. Per ogni plugin, registra entry in `plugin_registry`
3. Per ogni nodo del plugin, crea entry in `node_types`
4. Configura processori PDKProxy per esecuzione

### **Configurazione Plugin:**
```json
{
  "id": "my-custom-plugin",
  "name": "My Custom Plugin", 
  "version": "1.0.0",
  "description": "Plugin personalizzato",
  "nodes": [
    {
      "id": "my_processor",
      "name": "My Processor",
      "description": "Processore custom",
      "category": "processing",
      "input_schema": {...},
      "output_schema": {...}
    }
  ]
}
```

---

## 📊 Analytics & Monitoring

### **NodeExecutionLog**
Tabella per tracking esecuzioni nodi.

```sql
CREATE TABLE node_execution_logs (
    id INTEGER PRIMARY KEY,
    node_type VARCHAR(100),
    execution_id VARCHAR(50),
    workflow_id VARCHAR(50),
    status VARCHAR(20),                      -- success, failed, timeout
    execution_time_ms INTEGER,
    error_message TEXT,
    input_data_hash VARCHAR(64),            -- Hash per privacy
    output_data_hash VARCHAR(64),
    created_at DATETIME,
    processor_version VARCHAR(20)
);
```

### **Query Analytics:**
```python
from backend.db.database import SessionLocal
from backend.db.node_registry_models import NodeExecutionLog

db = SessionLocal()

# Nodi più utilizzati
popular_nodes = db.query(
    NodeExecutionLog.node_type,
    func.count().label('usage_count')
).group_by(NodeExecutionLog.node_type).all()

# Performance per tipo nodo
avg_performance = db.query(
    NodeExecutionLog.node_type,
    func.avg(NodeExecutionLog.execution_time_ms).label('avg_time')
).group_by(NodeExecutionLog.node_type).all()
```

---

## 🔄 Legacy Migration

### **Mapping Predefiniti**
Il sistema include mapping per nodi legacy comuni:

```python
PREDEFINED_MAPPINGS = {
    "PDFInput": "document_input_node",
    "PDFInputValidator": "document_input_node", 
    "UpdateInputValidator": "text_filter",
    "ChromaVectorStore": "chroma_vector_store",
    "LLMProcessor": "llm_processor",
    "TextChunker": "text_chunker",
    "TextEmbedder": "text_embedder",
    "QueryInput": "query_input_node",
    "ChromaRetriever": "chroma_retriever",
    "PDFResultsFormatter": "document_results_formatter"
}
```

### **Processo di Migrazione:**
1. Nodi legacy inseriti come `is_active=False`
2. Mapping creati con `auto_migrate=True`
3. Richieste a nodi legacy automaticamente redirette
4. Log di migrazione per tracking

---

## 🌐 REST API Endpoints

### **Node Management**

#### **GET /api/admin/nodes**
Lista tutti i tipi di nodi.

```bash
curl -X GET http://localhost:8000/api/admin/nodes
```

**Response:**
```json
{
  "nodes": [
    {
      "id": 1,
      "node_type": "document_input_node",
      "plugin_id": "core-input-plugin",
      "display_name": "Document Input",
      "category": "input",
      "is_active": true,
      "is_legacy": false,
      "created_at": "2025-11-20T10:00:00Z"
    }
  ]
}
```

#### **POST /api/admin/nodes**
Registra nuovo tipo di nodo.

```bash
curl -X POST http://localhost:8000/api/admin/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "my_processor",
    "processor_class": "PDKProxyProcessor",
    "plugin_id": "my-plugin",
    "display_name": "My Processor",
    "category": "processing"
  }'
```

#### **POST /api/admin/nodes/mappings**
Crea mapping legacy → modern.

```bash
curl -X POST http://localhost:8000/api/admin/nodes/mappings \
  -H "Content-Type: application/json" \
  -d '{
    "legacy_type": "OldProcessor",
    "modern_type": "new_processor",
    "auto_migrate": true
  }'
```

### **Plugin Management**

#### **GET /api/admin/plugins**
Lista plugin registrati.

#### **POST /api/admin/plugins/discover**
Forza discovery di nuovi plugin.

#### **PUT /api/admin/plugins/{plugin_id}/status**
Aggiorna status plugin (attivo/disattivato).

---

## 🚦 Error Handling

### **Errori Comuni**

#### **ValueError: Tipo di nodo non supportato**
```python
try:
    processor = db_node_registry.get_processor("unknown_node")
except ValueError as e:
    logger.error(f"Nodo non supportato: {e}")
    # Controlla nodi disponibili
    available = db_node_registry.get_supported_node_types()
```

#### **Database Connection Errors**
```python
from sqlalchemy.exc import SQLAlchemyError

try:
    processor = db_node_registry.get_processor("node_type")
except SQLAlchemyError as e:
    logger.error(f"Errore database: {e}")
    # Fallback o retry logic
```

### **Logging**
Tutte le operazioni sono logged con contesto dettagliato:

```python
# Esempi log
logger.info("🗃️ DatabaseNodeRegistry inizializzato")
logger.info("🔄 Migrazione automatica: PDFInput → document_input_node")
logger.error("🚨 NODO NON TROVATO: UnknownNode")
logger.info("📝 Registrato nuovo tipo di nodo: my_processor")
```

---

## 🧪 Testing

### **Unit Tests**
```python
import pytest
from backend.engine.db_node_registry import DatabaseNodeRegistry

@pytest.fixture
def registry():
    return DatabaseNodeRegistry()

def test_get_processor_modern_node(registry):
    processor = registry.get_processor("document_input_node")
    assert processor is not None
    assert processor.__class__.__name__ == "PDKProxyProcessor"

def test_get_processor_legacy_mapping(registry):
    processor = registry.get_processor("PDFInput")
    assert processor is not None
    # Dovrebbe essere mappato a document_input_node

def test_unsupported_node_raises_error(registry):
    with pytest.raises(ValueError, match="Tipo di nodo non supportato"):
        registry.get_processor("NonExistentNode")
```

### **Integration Tests**
```python
def test_workflow_execution_with_legacy_nodes():
    """Testa che i workflow con nodi legacy funzionino tramite mapping"""
    # Simula esecuzione workflow con PDFInput
    # Verifica che venga mappato a document_input_node
    # Conferma che il workflow completi con successo
```

---

## 📈 Performance

### **Caching**
- Processori cached dopo primo lookup
- Cache invalidata quando nodi vengono registrati/modificati
- Database sessions gestite con connection pooling

### **Optimizations**
- Indici su `node_type`, `plugin_id`, `is_active`
- Lazy loading delle relazioni SQLAlchemy
- Batch operations per registrazione multipla

---

## 🎯 Migration Guide

### **Da NodeRegistry a DatabaseNodeRegistry**

1. **Backup esistente**:
   ```bash
   cp backend/engine/node_registry.py backend/engine/node_registry.py.backup
   ```

2. **Esegui migrazione database**:
   ```bash
   python backend/db/migrations/migrate_to_db_node_registry.py
   ```

3. **Aggiorna import**:
   ```python
   # Prima
   from backend.engine.node_registry import NodeRegistry
   
   # Dopo  
   from backend.engine.db_node_registry import db_node_registry
   ```

4. **Testa compatibilità**:
   ```bash
   python test_db_node_registry.py
   ```

### **Rollback (se necessario)**
1. Ripristina file backup
2. Aggiorna import ai vecchi
3. Rimuovi tabelle create: `DROP TABLE node_types, node_type_mappings, plugin_registry`

---

## 📚 Esempi Pratici

### **Sviluppatore Plugin**
```python
# 1. Il plugin si auto-registra
# 2. Sviluppatore non deve modificare backend
# 3. Nodi disponibili automaticamente nei workflow

# Nel plugin: nodes.json
{
  "id": "sentiment_analyzer", 
  "name": "Sentiment Analyzer",
  "input_schema": {"text": "string"},
  "output_schema": {"sentiment": "string", "score": "number"}
}
```

### **Admin Sistema**
```python
# Registrazione manuale nodo custom
await db_node_registry.register_node_type(
    node_type="custom_validator",
    processor_class="CustomValidatorProcessor", 
    display_name="Custom Validator",
    category="validation"
)

# Creazione mapping per compatibilità
await db_node_registry.create_legacy_mapping(
    legacy_type="OldValidator",
    modern_type="custom_validator"
)
```

### **Utente Workflow**
```python
# I workflow continuano a funzionare
# Sia con nodi legacy che moderni
workflow = {
    "nodes": [
        {"node_type": "PDFInput", ...},      # Auto-mappato
        {"node_type": "text_processor", ...}  # Diretto
    ]
}
```

---

**Happy Node Managing! 🚀**