# PDK Server - Configurazione Livelli di Log

Questo documento fornisce istruzioni per configurare i livelli di verbosità dei log del server PDK e risolvere problemi di visualizzazione dei nodi nella palette workflow.

## Problema

Il server PDK ha una verbosità eccessiva nei log che può rendere difficile identificare messaggi importanti e può interferire con la corretta elaborazione delle risposte API, causando problemi di visualizzazione dei nodi nella palette workflow.

## Soluzione

Abbiamo implementato un nuovo sistema di logging con diversi livelli di verbosità che può essere configurato tramite variabili d'ambiente o tramite API.

### Livelli di log disponibili

- **ERROR**: Solo errori gravi
- **WARN**: Errori e avvertimenti
- **INFO**: Informazioni generali (default)
- **DEBUG**: Informazioni dettagliate per debug
- **TRACE**: Informazioni molto dettagliate (massima verbosità)

## Utilizzo

### Avvio del server con livello di log specifico

Usa lo script PowerShell incluso per avviare il server PDK con il livello di log desiderato:

```powershell
.\start_pdk_server.ps1 -LogLevel INFO
```

Sostituisci `INFO` con uno dei livelli disponibili: `ERROR`, `WARN`, `INFO`, `DEBUG` o `TRACE`.

### Controllo del funzionamento

Se noti che i nodi non vengono visualizzati nella palette workflow, puoi utilizzare gli script di diagnostica inclusi:

1. **Test dell'endpoint nodi del server PDK**:
   ```
   cd scripts
   node test_pdk_nodes.js
   ```

2. **Test della comunicazione tra backend e server PDK**:
   ```
   cd scripts
   node debug_pdk_api.js
   ```

## Risoluzione dei problemi

### Nessun nodo appare nella palette

1. Verifica che il server PDK sia in esecuzione:
   ```
   .\start_pdk_server.ps1 -LogLevel INFO
   ```

2. Controlla che l'endpoint `/api/nodes` risponda correttamente:
   ```
   cd scripts
   node test_pdk_nodes.js
   ```

3. Verifica che il backend comunichi correttamente con il server PDK:
   ```
   cd scripts
   node debug_pdk_api.js
   ```

4. Se il test diretto al server PDK funziona ma il backend non riesce a ottenere i nodi, potrebbe esserci un problema di rete o di proxy. Verifica che le configurazioni degli URL in `PramaIAServer/frontend/client/src/config/appConfig.js` siano corrette.

### Log troppo verbosi

Se hai bisogno di ridurre la verbosità dei log:

1. Avvia il server con un livello più basso:
   ```
   .\start_pdk_server.ps1 -LogLevel WARN
   ```

2. Per disabilitare completamente i log non critici:
   ```
   .\start_pdk_server.ps1 -LogLevel ERROR
   ```

### Log non sufficientemente dettagliati per il debug

Se hai bisogno di più dettagli per il debug:

1. Avvia il server con un livello più alto:
   ```
   .\start_pdk_server.ps1 -LogLevel DEBUG
   ```

2. Per il massimo livello di dettaglio:
   ```
   .\start_pdk_server.ps1 -LogLevel TRACE
   ```

## Modifica della configurazione a runtime

È possibile modificare il livello di log anche tramite l'API del logger nel codice:

```javascript
// Importa il logger
import logger from './logger.js';

// Imposta il livello di log
logger.setLevel('DEBUG');

// Oppure usa le impostazioni ottimizzate
logger.setSensibleDefaults('DEBUG');
```

## Note tecniche

- Il sistema di log si trova in `PramaIA-PDK/server/logger.js`
- La funzione `setSensibleDefaults` configura automaticamente le opzioni di logging appropriate per ogni livello
- Il middleware di logging per Express è configurato per ridurre la verbosità per le richieste non critiche
- Quando si è in modalità `INFO` o inferiore, le risposte delle API non vengono loggate per evitare sovraccarichi
