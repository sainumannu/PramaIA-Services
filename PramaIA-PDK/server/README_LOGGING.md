# PDK Server Logging System

Questo modulo fornisce un sistema di logging avanzato per il PDK Server con controllo della verbosità tramite livelli di log.

## Livelli di Log

I livelli di log disponibili sono (dal meno verboso al più verboso):

- **ERROR** (0): Solo errori
- **WARN** (1): Errori e warning
- **INFO** (2): Informazioni normali (default)
- **DEBUG** (3): Informazioni dettagliate di debug
- **TRACE** (4): Informazioni molto dettagliate e tracciamento

## Come utilizzare

### Impostazione del livello di log

È possibile impostare il livello di log in diversi modi:

1. **Variabile d'ambiente**:
   ```
   PDK_LOG_LEVEL=DEBUG node server/plugin-api-server.js
   ```

2. **Nel codice**:
   ```javascript
   import logger from './logger.js';
   
   // Imposta il livello di log
   logger.setLevel('DEBUG');
   // oppure
   logger.setLevel(logger.levels.DEBUG);
   ```

### Log di eventi

Utilizza le funzioni appropriate per ogni livello di log:

```javascript
logger.error('Messaggio di errore critico');
logger.warn('Avviso importante');
logger.info('Informazione standard');
logger.debug('Informazione utile per debug');
logger.trace('Informazione dettagliata per tracciamento');
```

### Funzioni specializzate

Il modulo fornisce anche funzioni specializzate per:

- `logger.api(method, endpoint, message)` - Per log di chiamate API
- `logger.icon(message)` - Per log specifici di debug icone
- `logger.node(nodeId, message)` - Per log relativi a nodi specifici
- `logger.success(message)` - Per segnalare operazioni completate con successo

### Express Middleware

Il modulo include un middleware per Express che gestisce automaticamente il log delle richieste:

```javascript
app.use(logger.requestLogger);
```

## Controllo dell'output

È possibile personalizzare ulteriormente l'output dei log:

- `logger.setColorEnabled(true/false)` - Attiva/disattiva i colori nei log
- `logger.setTimestampEnabled(true/false)` - Attiva/disattiva i timestamp nei log
- `logger.setRequestLoggingEnabled(true/false)` - Attiva/disattiva il logging delle richieste

## Configurazione completa

```javascript
import logger from './logger.js';

// Imposta il livello di log
logger.setLevel('DEBUG');

// Personalizza l'output
logger.setColorEnabled(true);
logger.setTimestampEnabled(true);

// Usa il middleware
app.use(logger.requestLogger);

// Ottieni la configurazione corrente
const config = logger.getConfig();
console.log('Configurazione attuale:', config);
```

## Esempi di utilizzo per diversi scenari

### Produzione
```
PDK_LOG_LEVEL=INFO node server/plugin-api-server.js
```

### Debugging
```
PDK_LOG_LEVEL=DEBUG node server/plugin-api-server.js
```

### Tracciamento dettagliato (per debugging avanzato)
```
PDK_LOG_LEVEL=TRACE node server/plugin-api-server.js
```
