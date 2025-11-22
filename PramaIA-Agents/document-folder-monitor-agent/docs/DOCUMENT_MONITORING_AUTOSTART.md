# Document Folder Monitoring - Guida Completa all'Uso

## Introduzione

Il Document Folder Monitor Agent è un sistema avanzato di monitoraggio cartelle con **filtri intelligenti** che ottimizza automaticamente il traffico di rete. Monitora le cartelle del filesystem e trasferisce al backend di PramaIA solo i documenti e file di testo processabili, evitando sprechi di banda per file giganti non vettorizzabili (es. video MP4 da GB).

## 🚀 Caratteristiche principali

### Monitoraggio Intelligente
- **Monitoraggio di cartelle multiple** in parallelo
- **Rilevamento automatico** di documenti e file di testo processabili
- **Sistema di filtri intelligenti** con risparmio banda del 95%+
- **Invio differenziato** basato sul tipo e dimensione del file
- **Autostart di cartelle selezionate** all'avvio del plugin
- **Configurazione persistente** delle cartelle monitorate
- **Dashboard di controllo** integrata in PramaIA

### 🔍 Sistema di Filtri Intelligenti (NUOVO!)

Il sistema di filtri rivoluziona il modo in cui l'agent gestisce i file, evitando trasferimenti inutili e ottimizzando le performance.

#### Come funziona
1. **Valutazione pre-upload**: Ogni file viene analizzato prima del trasferimento
2. **Interrogazione server**: L'agent chiede al server come gestire ogni file
3. **Decisione intelligente**: Basata su estensione, dimensione e contenuto
4. **Azione mirata**: Esecuzione dell'azione più appropriata

#### Tipi di azione

| 🎯 Azione | 📋 Descrizione | 📄 Esempi | 💾 Banda |
|-----------|----------------|-----------|----------|
| `PROCESS_FULL` | Trasferimento e processamento completo | PDF, DOC, TXT, PY | 100% |
| `METADATA_ONLY` | Solo metadati del file | JPG piccole, DB files | ~1KB |
| `SKIP` | Nessun trasferimento | MP4, ZIP, EXE grandi | 0% |

#### Benefici concreti
- **95%+ risparmio banda**: Testato con file reali
- **Velocità migliorata**: Solo file utili vengono trasferiti
- **Resilienza**: Funziona anche quando il server filtri è offline
- **Trasparenza**: Log dettagliati di ogni decisione

## Funzionalità di Autostart

La funzionalità di autostart consente di avviare automaticamente il monitoraggio di cartelle selezionate all'avvio del plugin, senza la necessità di un'attivazione manuale da parte dell'utente.

### Come funziona

1. All'avvio del plugin, viene caricata la configurazione dal file `monitor_config.json`
2. Dopo un breve ritardo (5 secondi per assicurare l'inizializzazione corretta), il sistema avvia automaticamente il monitoraggio delle cartelle contrassegnate con autostart
3. Le cartelle non contrassegnate con autostart devono essere avviate manualmente dall'interfaccia di PramaIA

### Configurazione

È possibile configurare l'autostart attraverso:

1. **Interfaccia web PramaIA**: Nella dashboard di monitoraggio documenti, ogni cartella ha un interruttore "Autostart" che può essere attivato o disattivato.
2. **Configurazione manuale**: Modificando il file `monitor_config.json` nella directory del plugin.

Esempio di configurazione:

```json
{
  "folders": [
    "C:/Cartella1",
    "C:/Cartella2",
    "C:/Cartella3"
  ],
  "autostart_folders": [
    "C:/Cartella1",
    "C:/Cartella3"
  ]
}
```

In questo esempio, le cartelle "Cartella1" e "Cartella3" verranno monitorate automaticamente all'avvio del plugin.

## API e integrazione

Il plugin espone le seguenti API per la gestione dell'autostart:

- `GET /monitor/status` - Restituisce lo stato attuale, inclusa la lista delle cartelle con autostart abilitato
- `POST /monitor/autostart` - Imposta o rimuove l'autostart per una cartella
- `POST /monitor/start` - Avvia il monitoraggio di cartelle specifiche
- `POST /monitor/stop` - Ferma tutto il monitoraggio attivo

### Esempio di utilizzo API

```javascript
// Abilitare l'autostart per una cartella
fetch('http://localhost:8001/monitor/autostart', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    folder_path: "C:/Cartella1", 
    autostart: true 
  })
});

// Disabilitare l'autostart
fetch('http://localhost:8001/monitor/autostart', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    folder_path: "C:/Cartella1", 
    autostart: false 
  })
});
```

## Risoluzione problemi

### Problemi comuni di autostart
Se le cartelle con autostart non vengono avviate automaticamente:

1. Verificare che il file `monitor_config.json` sia correttamente formattato
2. Controllare che le cartelle esistano e siano accessibili
3. Verificare i log all'avvio del plugin per messaggi di errore
4. Riavviare il plugin per forzare il caricamento della configurazione

### Problemi di filtri intelligenti
Se i filtri non funzionano correttamente:

1. **Server filtri non raggiungibile**: L'agent usa fallback locali (normale)
2. **File grandi trasferiti**: Verificare la configurazione server-side
3. **File piccoli saltati**: Controllare le regole di estensione
4. **Test sistema**: Eseguire `python test_filters.py` per verificare

### Debug e monitoraggio

#### Log di esempio con filtri
```
📄 Nuovo file rilevato: video.mp4 (104,857,600 bytes)
🔍 Decisione filtri: skip - Extension filtered locally  
⏭️ FILE SALTATO - Evitato trasferimento di 104,857,600 bytes

📄 Nuovo file rilevato: report.docx (1,024 bytes)
🔍 Decisione filtri: process_full - Document under size limit
✅ File 'report.docx' inviato al backend (created)
   Filtro applicato: documents
```

#### Comandi di test
```bash
# Test decisioni filtri
python test_filters.py

# Test completo con simulazione risparmio banda
python test_smart_handler.py

# Verifica connessione server filtri
curl http://localhost:8000/api/agent-filters/evaluate-file/
```

#### Metriche di performance
- **Bandwidth saved**: Percentuale banda risparmiata (target: 90%+)
- **Files by action**: Distribuzione PROCESS_FULL/METADATA_ONLY/SKIP
- **Fallback rate**: Frequenza uso regole locali vs server
- **Processing time**: Tempo valutazione per file

## 🔧 Configurazione Avanzata

### File di configurazione filtri locali
Crea `src/local_filters.json` per personalizzare i fallback:
```json
{
  "skip_extensions": [".mp4", ".avi", ".mov", ".zip", ".exe"],
  "process_extensions": [".pdf", ".txt", ".doc", ".docx", ".odt", ".rtf", ".md", ".json"],
  "metadata_max_size": 1048576,
  "process_max_size": 10485760
}
```

### Variabili d'ambiente per filtri
```bash
# URL server filtri (default: stesso del backend)
FILTER_SERVER_URL=http://localhost:8000

# Timeout per query filtri (secondi)
FILTER_QUERY_TIMEOUT=5

# Abilitazione cache locale filtri
FILTER_CACHE_ENABLED=true
FILTER_CACHE_TTL=300
```
