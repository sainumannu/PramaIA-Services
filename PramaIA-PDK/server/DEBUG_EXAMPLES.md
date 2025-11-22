# Configurazione Debug per PDK Server

Questo file contiene esempi di comandi per avviare il PDK Server con diversi livelli di verbosità.

## Avvio Semplice

### 1. Log Minimi (solo errori)
```powershell
.\start-all-clean.ps1 -PDKLogLevel ERROR
```

### 2. Log Standard (errori e informazioni generali)
```powershell
.\start-all-clean.ps1 -PDKLogLevel INFO
```

### 3. Log Dettagliati (per debug)
```powershell
.\start-all-clean.ps1 -PDKLogLevel DEBUG
```

### 4. Log Completi (per tracciamento dettagliato)
```powershell
.\start-all-clean.ps1 -PDKLogLevel TRACE
```

## Variabili d'Ambiente

È possibile impostare direttamente la variabile d'ambiente `PDK_LOG_LEVEL` prima di avviare il server:

```powershell
$env:PDK_LOG_LEVEL = "DEBUG"
node server/plugin-api-server.js
```

## Esempi di Output

### Livello ERROR
```
[2025-08-17T19:23:22.822Z] ❌ ERROR: Errore lettura plugin test-plugin: Unexpected token in JSON
```

### Livello INFO
```
[2025-08-17T19:23:22.822Z] ✅ Server PDK avviato su http://localhost:3001
[2025-08-17T19:23:22.822Z] ℹ️ Plugin disponibili: 15
[2025-08-17T19:23:22.827Z] ℹ️ Server pronto ad accettare connessioni
```

### Livello DEBUG
```
[2025-08-17T19:23:22.822Z] ✅ Server PDK avviato su http://localhost:3001
[2025-08-17T19:23:22.822Z] ℹ️ Plugin disponibili: 15
[2025-08-17T19:23:22.826Z] 🔍 DEBUG: Plugin core-api-plugin: [PLUGIN] Core API (2 nodes)
[2025-08-17T19:23:22.826Z] 🔍 DEBUG: Plugin core-data-plugin: [PLUGIN] Core Data (3 nodes)
```

### Livello TRACE
```
[2025-08-17T19:23:42.534Z] 🌐 GET /api/nodes [go7c27t2]
[2025-08-17T19:23:42.535Z] 🌐 GET /api/nodes Ottenendo tutti i nodi disponibili
[2025-08-17T19:23:42.538Z] 📊 TRACE: Node User Input icon: "👤" [chars: 128172]
[2025-08-17T19:23:42.539Z] 📊 TRACE: Node File Input icon: "📄" [chars: 128196]
```
