# Guida all'integrazione con PramaIA-PDK

## Introduzione

Questa guida descrive come integrare il client JavaScript di PramaIA-LogService con PramaIA-PDK.

## Prerequisiti

- PramaIA-PDK installato e configurato
- PramaIA-LogService avviato e funzionante
- API key valida per PramaIA-PDK

## Installazione del client

1. Copia la directory `clients/javascript` dal repository PramaIA-LogService nella directory `server/utils` di PramaIA-PDK:

```powershell
Copy-Item -Path "C:\PramaIA\PramaIA-LogService\clients\javascript" -Destination "C:\PramaIA\PramaIA-PDK\server\utils\pramaialog" -Recurse
```

2. Installa il client come dipendenza locale:

```powershell
cd C:\PramaIA\PramaIA-PDK\server
npm install ./utils/pramaialog
```

## Configurazione

Configura il logger nel file di configurazione del PDK:

```javascript
// config.js o simile
const config = {
  // Altre configurazioni...
  
  logging: {
    // Si raccomanda di leggere il backend dal file .env o dalle variabili d'ambiente
    // Esempio: BACKEND_URL=http://127.0.0.1:8081 oppure PRAMAIALOG_HOST=http://127.0.0.1 + PRAMAIALOG_PORT=8081
    serviceHost: process.env.BACKEND_URL || process.env.PRAMAIALOG_HOST || 'http://localhost:8081',
    apiKey: 'pramaiapdk_api_key_123456',
    level: process.env.PDK_LOG_LEVEL || 'info'
  }
};

module.exports = config;
```

## Utilizzo

### Inizializzazione del logger

Crea un file `server/utils/logger.js` per inizializzare il logger centralizzato:

```javascript
const { PramaIALogger, LogLevel, LogProject } = require('./pramaialog/pramaialog');
const config = require('../config');

// Mappa i livelli di log da stringa a enum
const mapLogLevel = (level) => {
  const levelMap = {
    'debug': LogLevel.DEBUG,
    'info': LogLevel.INFO,
    'warn': LogLevel.WARNING,
    'error': LogLevel.ERROR,
    'critical': LogLevel.CRITICAL
  };
  return levelMap[level.toLowerCase()] || LogLevel.INFO;
};

// Crea un'istanza globale del logger
const pdkLogger = new PramaIALogger({
  apiKey: config.logging.apiKey,
  project: LogProject.PDK,
  module: 'pdk-server',
  host: config.logging.serviceHost
});

// Funzione di convenienza per ottenere un logger per un modulo specifico
function getLogger(moduleName) {
  return new PramaIALogger({
    apiKey: config.logging.apiKey,
    project: LogProject.PDK,
    module: moduleName,
    host: config.logging.serviceHost
  });
}

module.exports = {
  pdkLogger,
  getLogger,
  LogLevel
};
```

### Utilizzo nei vari moduli

Esempio di utilizzo nel file `server/plugin-api-server.js`:

```javascript
const { getLogger } = require('./utils/logger');

// Crea un logger specifico per questo modulo
const logger = getLogger('plugin-api-server');

// All'avvio del server
logger.info('PDK server avviato', { port: serverPort });

// Gestione degli errori
app.use((err, req, res, next) => {
  logger.error(
    'Errore interno del server',
    { 
      errorType: err.name,
      errorMessage: err.message,
      stack: err.stack
    },
    { 
      requestPath: req.path,
      requestMethod: req.method,
      userId: req.user ? req.user.id : null
    }
  );
  
  res.status(500).send('Errore interno del server');
});
```

Esempio di utilizzo in un gestore di plugin:

```javascript
const { getLogger } = require('../utils/logger');

// Crea un logger specifico per questo modulo
const logger = getLogger('document-monitor-plugin');

class DocumentMonitorPlugin {
  constructor() {
    logger.info('Inizializzazione plugin Document Monitor');
  }
  
  async processDocument(document) {
    try {
      logger.info(
        'Elaborazione documento',
        { documentId: document.id, documentName: document.name }
      );
      
      // Logica di elaborazione...
      
      return result;
    } catch (error) {
      logger.error(
        'Errore durante l\'elaborazione del documento',
        {
          errorType: error.name,
          errorMessage: error.message,
          stack: error.stack
        },
        {
          documentId: document.id,
          documentName: document.name
        }
      );
      throw error;
    }
  }
}
```

## Middleware di logging per Express

Per registrare automaticamente le richieste HTTP, è possibile creare un middleware di logging:

```javascript
const { getLogger } = require('./utils/logger');
const { v4: uuidv4 } = require('uuid');

const logger = getLogger('http_middleware');

function loggingMiddleware(req, res, next) {
  const startTime = Date.now();
  
  // Genera un ID univoco per la richiesta
  const requestId = uuidv4();
  
  // Aggiungi l'ID alla richiesta per poterlo usare in altri middleware
  req.requestId = requestId;
  
  // Log di inizio richiesta
  logger.info(
    `Inizio richiesta ${req.method} ${req.path}`,
    null,
    {
      requestId,
      method: req.method,
      path: req.path,
      query: req.query,
      ip: req.ip
    }
  );
  
  // Intercetta la fine della risposta
  res.on('finish', () => {
    // Calcola il tempo di risposta
    const processTime = Date.now() - startTime;
    
    // Log di fine richiesta
    logger.info(
      `Fine richiesta ${req.method} ${req.path}`,
      {
        statusCode: res.statusCode,
        processTimeMs: processTime
      },
      {
        requestId,
        method: req.method,
        path: req.path
      }
    );
  });
  
  next();
}

// Utilizzo nel server Express
const app = express();
app.use(loggingMiddleware);
```

## Gestione degli errori non catturati

Per registrare errori non catturati a livello di processo:

```javascript
const { pdkLogger } = require('./utils/logger');

process.on('uncaughtException', (error) => {
  pdkLogger.critical(
    'Errore non catturato nell\'applicazione',
    {
      errorType: error.name,
      errorMessage: error.message,
      stack: error.stack
    }
  );
  
  // Assicurati che i log vengano inviati prima di terminare
  pdkLogger.flush().finally(() => {
    process.exit(1);
  });
});

process.on('unhandledRejection', (reason, promise) => {
  pdkLogger.critical(
    'Promise rejection non gestita',
    {
      reason: reason instanceof Error ? { 
        errorType: reason.name,
        errorMessage: reason.message,
        stack: reason.stack
      } : String(reason)
    }
  );
});
```

## Best practices

1. **Chiusura del logger**: chiamare `logger.close()` o `logger.flush()` prima di terminare il processo
2. **Livelli di log**: utilizzare il livello di log appropriato per ciascun messaggio
3. **Struttura coerente**: mantenere una struttura coerente per i campi `details` e `context`
4. **Performance**: evitare di generare messaggi di log troppo frequenti o con dati troppo grandi
5. **Intercettazione errori**: utilizzare i gestori di errori per registrare tutti gli errori dell'applicazione
