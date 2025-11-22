````markdown
# Documentazione Tecnica - Sistema di Filtri Intelligenti

## Architettura del Sistema

Il sistema di filtri intelligenti è composto da diversi componenti che lavorano insieme per ottimizzare il traffico di rete e migliorare le performance dell'agent.

### Componenti Principali

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  SmartFileHandler│───→│  AgentFilterClient│───→│ Server Filtri   │
│  (Agent)        │    │  (Local Cache)   │    │ (Backend)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Event Buffer   │    │  Fallback Rules  │    │ Filter Rules DB │
│  (SQLite)       │    │  (Local)         │    │ (Configurable)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│  File Hash DB   │
│  (SQLite)       │
└─────────────────┘
```

Consulta la [documentazione del database degli hash](FILE_HASH_DATABASE.md) per dettagli sul sistema di tracciamento degli hash dei file.

## 🔧 Implementazione Dettagliata

### 1. SmartFileHandler (`smart_file_handler.py`)

Handler principale che gestisce eventi del file system con filtri intelligenti.

```python
class SmartFileHandler(FileSystemEventHandler):
    def __init__(self, pdf_list, folder, event_buffer):
        self.filter_client = agent_filter_client
        # ...
    
    def on_created(self, event):
        # 1. Rileva nuovo file
        # 2. Ottiene dimensione e path
        # 3. Interroga sistema filtri
        # 4. Esegue azione appropriata
```

**Caratteristiche chiave**:
- Integrazione trasparente con eventi watchdog
- Gestione differenziata per tipo di evento (created/modified/deleted/moved)
- Logging dettagliato delle decisioni
- Metadati estesi per il backend

### 2. AgentFilterClient (`filter_client.py`)

Client-side per comunicazione con il server di filtri.

```python
class AgentFilterClient:
    def should_process_file(self, file_path, file_size):
        # 1. Cache lookup
        # 2. Server query (se non in cache)
        # 3. Fallback locale (se server non disponibile)
        # 4. Decisione strutturata
```

**Caratteristiche chiave**:
- **Cache intelligente**: Evita query ripetute per stessi pattern
- **Fallback robusto**: Continua a funzionare anche offline
- **Timeout gestiti**: Non blocca mai l'agent
- **Retry logic**: Gestisce errori di rete temporanei

#### Struttura delle decisioni
```python
FilterDecision = {
    'action': 'process_full|metadata_only|skip',
    'reason': 'Human readable explanation',
    'should_upload': bool,
    'should_process_content': bool,
    'extract_metadata': bool,
    'filter_name': 'Rule name applied'
}
```

### 3. Server-side Filters (Backend)

#### AgentFilterService (`agent_filter_service.py`)
```python
@dataclass
class FilterRule:
    name: str
    extensions: List[str]
    max_size: Optional[int]
    min_size: Optional[int]
    action: FilterAction
```

**Filtri predefiniti**:
- **Documents**: PDF, DOC, TXT → `PROCESS_FULL`
- **Images**: JPG, PNG → `METADATA_ONLY` se < 1MB
- **Videos**: MP4, AVI, MOV → `SKIP`
- **Archives**: ZIP, RAR → `SKIP`
- **Executables**: EXE, DLL → `SKIP`

#### API Endpoints (`agent_filters_router.py`)
```python
POST /api/agent-filters/evaluate-file/
POST /api/agent-filters/evaluate-batch/
GET  /api/agent-filters/supported-extensions/
GET  /api/agent-filters/rules/
POST /api/agent-filters/rules/
```

## 📊 Algoritmi di Decisione

### Logica del Server
```python
def evaluate_file(file_path, file_size):
    # 1. Estrazione estensione
    extension = Path(file_path).suffix.lower()
    
    # 2. Ricerca regola per estensione
    for rule in rules:
        if extension in rule.extensions:
            # 3. Verifica vincoli dimensione
            if rule.max_size and file_size > rule.max_size:
                return SKIP_LARGE
            # 4. Applica azione regola
            return rule.action
    
    # 5. Regola di default per estensioni sconosciute
    return default_for_unknown(file_size)
```

### Logica di Fallback Locale
```python
def local_fallback_decision(file_path, file_size):
    extension = Path(file_path).suffix.lower()
    
    # Filtri locali per estensioni problematiche
    if extension in SKIP_EXTENSIONS:
        return {'action': 'skip', 'reason': 'Extension filtered locally'}
    
    # Regole di dimensione conservative
    if file_size > 50 * 1024 * 1024:  # > 50MB
        return {'action': 'skip', 'reason': 'File too large for processing'}
    
    # Regole per codice sorgente
    if extension in SOURCE_CODE_EXTENSIONS:
        return {'action': 'process_full', 'reason': 'Fallback - source code'}
    
    # Fallback sicuro per documenti piccoli
    if file_size < 100 * 1024:  # < 100KB
        return {'action': 'process_full', 'reason': 'Fallback - safe document'}
```

### 5. FileHashTracker (`file_hash_tracker.py`)

Gestisce il tracciamento degli hash dei file per rilevare modifiche e supportare la de-duplicazione.

```python
class FileHashTracker:
    def __init__(self, db_path: str = ""):
        # Utilizza variabile d'ambiente FILE_HASHES_DB
        if not db_path:
            db_path = os.getenv("FILE_HASHES_DB", "data/file_hashes.db")
        # ...
    
    def calculate_file_hash(self, file_path: str) -> str:
        # Calcola hash efficiente basato su:
        # - Percorso file
        # - Dimensione e data modifica
        # - Primi e ultimi 4KB per file grandi
        # - Hash completo per file piccoli
```

**Caratteristiche chiave**:
- Calcolo efficiente degli hash per file di qualsiasi dimensione
- Database SQLite centralizzato e configurabile
- Rilevamento preciso delle modifiche
- Supporto per ID vectorstore

## 🚀 Performance e Ottimizzazioni

### Cache Locale
- **TTL**: 5 minuti per decisioni server
- **LRU**: Eviction automatica quando cache piena
- **Pattern recognition**: Cache condivisa per pattern simili

### Batch Processing
```python
# Ottimizzazione per multiple valutazioni
decisions = filter_client.evaluate_batch_files([
    ('file1.pdf', 1024),
    ('file2.mp4', 104857600),
    ('file3.jpg', 2097152)
])
```

### Metriche di Performance
- **Query time**: < 50ms per decisione (target)
- **Cache hit rate**: > 80% (target)
- **Bandwidth savings**: > 90% (tipico)
- **False positives**: < 1% (file processabili saltati)

## 🔒 Sicurezza e Resilienza

### Gestione Errori
- **Network timeout**: 5 secondi default
- **Server unreachable**: Fallback automatico a regole locali
- **Malformed response**: Logging + fallback sicuro
- **Cache corruption**: Auto-rebuild della cache

### Logging e Audit
```python
# Ogni decisione viene loggata
logger.info(f"Filter decision for {filename}: {action} - {reason}")

# Metriche aggregate ogni ora
logger.info(f"Hourly stats: {processed}/{total} files, {bandwidth_saved}MB saved")
```

## 📈 Monitoraggio e Debug

### Comandi di Test
```bash
# Test singolo file
python -c "from src.filter_client import agent_filter_client; print(agent_filter_client.should_process_file('test.mp4', 100*1024*1024))"

# Test batch completo
python test_filters.py

# Simulazione risparmio banda
python test_smart_handler.py
```

### Endpoint di Debug
```bash
# Stato filtri server
curl http://localhost:8000/api/agent-filters/debug/stats

# Cache status client
curl http://localhost:8001/monitor/debug/filter-cache
```

### Log di Esempio
```
2025-08-16 10:30:15 - INFO - 📄 Nuovo file rilevato: presentation.pptx (5,242,880 bytes)
2025-08-16 10:30:15 - INFO - 🔍 Decisione filtri: metadata_only - Document over size limit  
2025-08-16 10:30:15 - INFO - 📊 SOLO METADATI - Evitato trasferimento contenuto di 5,242,880 bytes
2025-08-16 10:30:15 - INFO - ✅ Metadati inviati al backend per presentation.pptx
```

## 🛠️ Estensibilità

### Aggiunta Nuovi Filtri Server-side
```python
# Nuovo filtro per codice sorgente
new_rule = FilterRule(
    name="source_code",
    extensions=[".py", ".js", ".ts", ".java", ".cpp"],
    max_size=1024*1024,  # 1MB max
    action=FilterAction.PROCESS_FULL
)
filter_service.add_rule(new_rule)
```

### Personalizzazione Fallback Locali
```python
# Aggiunta regole locali personalizzate
CUSTOM_SKIP_EXTENSIONS = [".tmp", ".log", ".bak"]
SOURCE_CODE_EXTENSIONS.extend([".rs", ".go", ".php"])
```

### Integration Points
- **Event system**: Emette eventi per ogni decisione filtri
- **Metrics collector**: Interfaccia per sistemi di monitoraggio esterni
- **Config hot-reload**: Ricarica regole senza restart

````
