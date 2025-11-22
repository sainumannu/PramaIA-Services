# Document Folder Monitor Agent

Agent esterno per PramaIA con **sistema di filtri intelligenti** che monitora cartelle, rileva cambiamenti nei file di testo e documenti (doc, docx, odt, txt, xls, xlsx, ods e pdf) e comunica al sistema principale solo i file processabili, evitando sprechi di banda per file non vettorizzabili (es. video MP4).

## 🚀 Caratteristiche principali

### Monitoraggio Avanzato
- **Monitoraggio file system** in tempo reale (watchdog)
- **Rilevamento eventi** (creazione, modifica, eliminazione, spostamento)
- **Gestione cartelle** multiple con autostart configurabile
- **Persistenza eventi** via SQLite con buffer intelligente

### 🔍 Sistema di Filtri Intelligenti
- **Valutazione pre-upload**: Ogni file viene valutato prima del trasferimento
- **Decisioni differenziate**:
  - `PROCESS_FULL`: Documenti, codice, PDF → Trasferimento completo
  - `METADATA_ONLY`: Immagini, database → Solo metadati, no contenuto
  - `SKIP`: Video, archivi, eseguibili → Nessun trasferimento
- **Risparmio banda 95%+**: Evita trasferimenti inutili di file giganti
- **Fallback locale**: Funziona anche quando il server di filtri è offline

### 🔄 Sincronizzazione Multi-layer (NUOVO!)
- **Event Buffering**: Bufferizzazione eventi in SQLite per disconnessioni brevi
- **Riconciliazione Periodica**: Scan completo ogni ora per rilevare cambiamenti mancati
- **Recovery Sync**: Sincronizzazione automatica quando la connessione viene ripristinata
- **Auto-riparazione**: Rilevamento e correzione automatica delle incoerenze
- **Strategia Robusta**: Garantisce consistenza tra file system e vectorstore

### 📋 Logging Avanzato
- **Integrazione con LogService**: Tutti i log vengono inviati al servizio centrale
- **Configurazione via variabili d'ambiente**: Nessuna porta o endpoint hardcoded
- **Fallback locale**: Funziona anche quando LogService non è disponibile
- **Strumenti di diagnostica**: Suite di utilità per test e manutenzione

### API e Comunicazione
- **API REST** per gestione e configurazione
- **Registrazione automatica** con heartbeat al server principale
- **Notifiche in tempo reale** al backend con metadati intelligenti

## 📋 Requisiti
- Python 3.9+
- Solo dipendenze open source
- Accesso di rete al server PramaIA (porta 8000)
- Accesso al server di filtri per ottimizzazioni avanzate

## 📁 Struttura del progetto
```
document-folder-monitor-agent/
├── src/
│   ├── main.py                  # Entry point con uvicorn
│   ├── control_api.py           # API REST per controllo
│   ├── folder_monitor.py        # Core monitoring logic
│   ├── smart_file_handler.py    # Handler con filtri intelligenti
│   ├── filter_client.py         # Client per sistema filtri
│   ├── event_buffer.py          # Buffer eventi SQLite
│   ├── reconciliation_service.py # Servizio riconciliazione
│   ├── recovery_sync.py         # Sincronizzazione al riconnessione
│   └── logger.py                # Integrazione con LogService
├── utils/                       # Strumenti di utilità
│   ├── check_logger_integration.py # Test connessione LogService
│   ├── force_logs.py            # Script per forzare invio log
│   ├── fix_logger.py            # Correzione problemi logger
│   └── diagnose_and_fix_logging.py # Diagnostica automatica
├── docs/                        # Documentazione completa
│   ├── DOCUMENT_MONITORING_AUTOSTART.md # Guida utente
│   ├── TECHNICAL_DOCUMENTATION.md       # Docs sviluppatori  
│   ├── CHANGELOG_SMART_FILTERS.md       # Storia implementazioni
│   └── SINCRONIZZAZIONE_MULTI_LAYER.md  # Documentazione sincronizzazione
├── requirements.txt
└── README.md
```


## ⚡ Avvio rapido

### 1. Installazione
```bash
# Installa dipendenze
pip install -r requirements.txt
```

### 2. Avvio con filtri intelligenti
```bash
# Windows
python -m uvicorn src.main:app --reload --port 8001

# Mac/Linux  
chmod +x start.command
./start.command
```

### 3. Test del sistema di filtri
```bash
# Crea script di test temporaneo per verificare funzionalità
python -c "
from src.filter_client import agent_filter_client
print('Test Document:', agent_filter_client.should_process_file('document.docx', 1024))
print('Test Video:', agent_filter_client.should_process_file('video.mp4', 100*1024*1024))
"
```

## 🔧 Configurazione

### Variabili d'ambiente
```bash
# Server principale PramaIA
BACKEND_PORT=8000
BACKEND_HOST=localhost

# Porta agent
PLUGIN_DOCUMENT_MONITOR_PORT=8001

# Identificazione agent
PLUGIN_CLIENT_ID=document-monitor-001
PLUGIN_CLIENT_NAME="Document Folder Monitor"

# Configurazione sincronizzazione
RECONCILIATION_INTERVAL=3600       # Intervallo riconciliazione (secondi)
AUTO_RECONCILE_ON_RECONNECT=true   # Riconciliazione automatica alla riconnessione
MIN_DISCONNECTION_FOR_RECONCILE=1  # Minuti di disconnessione per attivare riconciliazione

# Configurazione LogService
PRAMAIALOG_ENABLED=true            # Abilita/disabilita l'integrazione con LogService
PRAMAIALOG_HOST=localhost          # Host del LogService (senza protocollo)
PRAMAIALOG_PORT=8081               # Porta del LogService
PRAMAIALOG_PROTOCOL=http://        # Protocollo da utilizzare (http:// o https://)
PRAMAIALOG_API_KEY=your_api_key    # Chiave API per l'autenticazione al LogService
```

### File di configurazione
Il file `monitor_config.json` gestisce:
- Lista cartelle monitorate
- Impostazioni autostart per cartella
- Configurazioni specifiche per tipo di file

## 🎯 Sistema di Filtri in Dettaglio

### Tipi di azione supportati

| Azione | Descrizione | Esempio di File | Banda Utilizzata |
|--------|-------------|-----------------|------------------|
| `PROCESS_FULL` | Trasferimento e processamento completo | PDF, TXT, PY, DOC | 100% |
| `METADATA_ONLY` | Solo metadati del file | JPG < 1MB, DB files | ~1KB |
| `SKIP` | Nessun trasferimento | MP4, ZIP, EXE | 0% |

### Configurazione filtri server-side
I filtri sono configurabili tramite il server principale:
```json
{
  "documents": {
    "extensions": [".pdf", ".doc", ".txt"],
    "max_size": 10485760,
    "action": "process_full"
  },
  "videos": {
    "extensions": [".mp4", ".mov", ".avi"],
    "action": "skip"
  },
  "images": {
    "extensions": [".jpg", ".png", ".gif"],
    "max_size": 1048576,
    "action": "metadata_only"
  }
}
```

### Fallback locale
Quando il server di filtri non è disponibile:
- File con estensioni video/archivio → `SKIP`
- File di codice sorgente → `PROCESS_FULL`
- File piccoli (< 100KB) → `PROCESS_FULL`
- File medi (< 1MB) → `METADATA_ONLY`
- File grandi → `SKIP`

## 🔄 Sistema di Sincronizzazione Multi-layer

### Strategia a 3 livelli

| Livello | Funzionalità | Scenario | Implementazione |
|---------|--------------|----------|-----------------|
| Layer 1 | Event Buffering | Disconnessioni brevi | `event_buffer.py` |
| Layer 2 | Riconciliazione Periodica | Modifiche mancate | `reconciliation_service.py` |
| Layer 3 | Recovery Sync | Riconnessione dopo interruzione | `recovery_sync.py` |

### Endpoint di controllo
```
GET /monitor/sync-status          # Stato sincronizzazione
POST /monitor/reconcile?folder_path={path}  # Forza riconciliazione
POST /monitor/force-sync          # Forza invio eventi bufferizzati
```

### Interfaccia di Monitoraggio della Sincronizzazione
L'interfaccia web del server PramaIA include ora una nuova scheda "Sincronizzazione" nel pannello di monitoraggio documenti che permette di:
- Visualizzare lo stato di connessione dei client
- Monitorare il servizio di riconciliazione
- Forzare la sincronizzazione manuale
- Visualizzare metriche di sincronizzazione

Per i dettagli completi, vedere [INTERFACCIA_SINCRONIZZAZIONE.md](INTERFACCIA_SINCRONIZZAZIONE.md)

### Log di esempio
```
🔄 Riconciliazione periodica avviata per cartella: C:\Documents
📊 Scan filesystem: trovati 124 file
🔍 Confronto con vectorstore: rilevate 3 differenze
✅ Riconciliazione completata. Aggiunti: 1, Aggiornati: 1, Eliminati: 1
```

## 📊 Monitoraggio delle Performance

### Metriche disponibili
- **Bandwidth saved**: Percentuale di banda risparmiata
- **Files processed**: Numero di file elaborati per tipo di azione
- **Filter hit rate**: Efficacia delle regole di filtraggio
- **Fallback usage**: Frequenza di uso delle regole locali
- **Sync consistency**: Percentuale di file correttamente sincronizzati

### Log di esempio
```
📄 Nuovo file rilevato: video.mp4 (104,857,600 bytes)
🔍 Decisione filtri: skip - Extension filtered locally
⏭️ File 'video.mp4' ignorato per filtri - Evitato trasferimento di 104,857,600 bytes

📄 Nuovo file rilevato: report.docx (1,024 bytes)  
🔍 Decisione filtri: process_full - Document under size limit
✅ File 'report.docx' inviato al backend (created)
```
