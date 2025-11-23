# Test CRUD Metadati - PramaIA Agent

Questa directory contiene una suite di test completa per verificare il corretto funzionamento delle operazioni CRUD con il nuovo formato di metadati richiesto dal server PramaIA.

## 📁 Files di Test

### `test_metadata_quick.py`
Test rapido per verifiche immediate:
- ✅ Estrazione metadati da file di test
- ✅ Validazione formato payload JSON
- ✅ Verifica configurazione ambiente

**Uso:**
```bash
python test_metadata_quick.py
```

### `test_crud_metadata.py`
Test completo delle operazioni CRUD:
- 🔍 **CREATE**: Test creazione file e estrazione metadati
- 📝 **UPDATE**: Test modifica file e aggiornamento metadati
- 🗑️ **DELETE**: Test eliminazione file con preservazione metadati
- 🌐 **Backend**: Test comunicazione con server (se disponibile)

**Uso:**
```bash
python test_crud_metadata.py
```

### `run_crud_tests.bat`
Script batch per Windows che:
- Imposta variabili d'ambiente di default
- Esegue prima il test rapido
- Se passa, esegue il test completo
- Fornisce report finale consolidato

**Uso:**
```cmd
run_crud_tests.bat
```

## ⚙️ Configurazione

### Variabili d'Ambiente
I test utilizzano queste variabili d'ambiente:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `CLIENT_ID` | `test-agent-crud` | ID client per identificare l'agent |
| `BACKEND_URL` | `http://localhost:8000` | URL base del server PramaIA |
| `BACKEND_PORT` | `8000` | Porta del server (se BACKEND_URL non impostato) |

**Impostazione variabili:**
```cmd
# Windows
set CLIENT_ID=mio-agent
set BACKEND_URL=http://server.example.com:8080

# Linux/Mac  
export CLIENT_ID=mio-agent
export BACKEND_URL=http://server.example.com:8080
```

### Dipendenze
I test richiedono i moduli dell'agent PramaIA:
- `src/unified_file_handler.py`
- `src/event_buffer.py`
- `src/filter_client.py`
- `src/logger.py`

Dipendenze Python opzionali:
- `requests` - per test comunicazione backend
- `fitz` (PyMuPDF) - per metadati PDF avanzati

## 📊 Output dei Test

### Test Rapido
```
🧪 Test rapido metadati agent
==================================================

Configurazione ambiente:
   ✅ CLIENT_ID: test-agent-crud
   ✅ BACKEND_URL: http://localhost:8000
   ⚠️ BACKEND_PORT: 8000
   ⚠️ BACKEND_BASE_URL: MISSING

Estrazione metadati:
✅ Metadati estratti correttamente: 12 campi
   📄 File: tmpfile.txt
   📦 Dimensione: 35 bytes
   📅 Creato: 2024-11-22T10:30:45

Formato payload:
✅ Formato payload corretto
   🆔 Client ID: test-agent-crud
   📁 Path originale: /test/path/test.pdf
   🔄 Source: agent
   📋 Campi metadati: 12

📊 RISULTATI:
   ✅ PASS Configurazione ambiente
   ✅ PASS Estrazione metadati
   ✅ PASS Formato payload

🎯 Successo: 3/3 (100%)
🎉 Test completati con successo!
```

### Test Completo
Il test completo genera un report JSON dettagliato con:
- Timestamp di esecuzione
- Statistiche per ogni tipo di operazione
- Dettagli di ogni test eseguito
- Summary con percentuali di successo

**Esempio report:**
```json
{
  "timestamp": "2024-11-22T10:30:45",
  "summary": {
    "metadata_extraction": {
      "total": 5,
      "successful": 5,
      "failed": 0
    },
    "create_operations": {
      "total": 5, 
      "successful": 5,
      "failed": 0
    },
    ...
  }
}
```

## 🔧 Debug e Troubleshooting

### Errori Comuni

**1. Modulo non trovato:**
```
ModuleNotFoundError: No module named 'src.unified_file_handler'
```
*Soluzione:* Verificare di eseguire i test dalla directory `document-folder-monitor-agent`

**2. Backend non disponibile:**
```
⚠️ Backend non disponibile - skip test comunicazione
```
*Soluzione:* Avviare il server PramaIA o impostare `BACKEND_URL` corretto

**3. Errore estrazione metadati PDF:**
```
❌ Errore nell'estrazione metadati PDF
```
*Soluzione:* Installare PyMuPDF: `pip install PyMuPDF`

### File di Log
I test generano diversi file utili per il debug:
- `crud_test_report_<timestamp>.json` - Report completo test CRUD
- Log della console con emoji per identificare rapidamente errori

### Verifica Manuale
Per verificare manualmente l'estrazione metadati:

```python
# Test diretto dell'estrazione metadati
import sys, os
sys.path.insert(0, 'src')
from unified_file_handler import UnifiedFileHandler
from event_buffer import EventBuffer

handler = UnifiedFileHandler([], ".", EventBuffer())
metadata = handler._extract_file_metadata("path/to/file.pdf")
print(json.dumps(metadata, indent=2))
```

## 🎯 Utilizzo per Debug

### Durante Sviluppo
1. Eseguire `test_metadata_quick.py` dopo ogni modifica
2. Verificare che tutti i campi richiesti siano presenti
3. Controllare formato JSON del payload

### Prima del Deploy
1. Eseguire `run_crud_tests.bat` completo
2. Verificare successo 100% o investigare fallimenti
3. Testare con file reali dell'ambiente di produzione

### In Produzione
1. Eseguire periodicamente i test per verificare integrità
2. Monitorare dimensione e formato dei metadati inviati
3. Verificare compatibilità con nuove versioni del server

## 📋 Checklist Pre-Deploy

- [ ] Test rapido passa al 100%
- [ ] Test completo passa al 100%
- [ ] Variabili d'ambiente configurate correttamente
- [ ] Backend raggiungibile e configurato
- [ ] Metadati PDF estratti correttamente (se richiesto)
- [ ] Log dell'agent mostrano "con metadati" nei messaggi
- [ ] Payload JSON valido e conforme al formato server

---

*Generato automaticamente - Parte del sistema PramaIA Agent Metadata Integration*