# Workflow Scheduler Plugin

Plugin per la schedulazione dell'esecuzione dei workflow nel sistema PramaIA-PDK.

## Descrizione

Questo plugin aggiunge un nodo di tipo "control" che permette di programmare l'esecuzione di un workflow secondo vari criteri temporali. Il nodo può essere configurato per eseguire operazioni a intervalli regolari, in base a espressioni cron, a date specifiche o in risposta a eventi.

## Funzionalità

- **Schedulazione a intervalli** - Esegui il workflow ogni X secondi, minuti, ore o giorni
- **Schedulazione cron** - Utilizza espressioni cron per schedulazioni complesse
- **Schedulazione a data specifica** - Esegui il workflow in una data e ora specifiche
- **Schedulazione basata su eventi** - Esegui il workflow in risposta a eventi specifici
- **Limiti di esecuzione** - Imposta date di inizio/fine e numero massimo di esecuzioni
- **Monitoraggio esecuzioni** - Mantieni uno storico delle esecuzioni con opzioni di notifica

## Configurazione

### Tipi di schedulazione

- **Intervallo**: Esecuzione ripetuta a intervalli fissi (es. ogni 5 minuti)
- **Cron**: Esecuzione in base a un'espressione cron (es. `0 9 * * 1-5` per ogni giorno lavorativo alle 9:00)
- **Data specifica**: Esecuzione singola a una data e ora precise
- **Evento**: Esecuzione in risposta a un evento specifico

### Opzioni avanzate

- **Data di inizio**: Quando iniziare la schedulazione
- **Data di fine**: Quando terminare la schedulazione
- **Numero massimo di esecuzioni**: Limita il numero di volte che il workflow viene eseguito
- **Fuso orario**: Specifica il fuso orario per la schedulazione
- **Monitoraggio esecuzioni**: Opzioni per tracciare e notificare le esecuzioni

## Esempi d'uso

### Esecuzione ogni 10 minuti

```json
{
  "schedule_type": "interval",
  "interval": {
    "value": 10,
    "unit": "minutes"
  }
}
```

### Esecuzione ogni lunedì alle 9:00

```json
{
  "schedule_type": "cron",
  "cron_expression": "0 9 * * 1",
  "timezone": "Europe/Rome"
}
```

### Esecuzione a una data specifica

```json
{
  "schedule_type": "date",
  "specific_date": "2025-12-31T23:59:59"
}
```

### Esecuzione in risposta a un evento

```json
{
  "schedule_type": "event",
  "event_name": "nuovo_documento"
}
```

## Integrazione nei workflow

Il nodo Workflow Scheduler può essere posizionato all'inizio di un workflow o in qualsiasi altro punto dove sia necessario introdurre un'attivazione programmata. Il nodo ha due output:

1. **output**: Contiene i dati da passare al nodo successivo
2. **metadata**: Contiene informazioni sulla schedulazione e sull'esecuzione corrente

## Note sull'implementazione

- L'implementazione utilizza le API standard di JavaScript per timer e date
- L'implementazione delle espressioni cron è semplificata; in un ambiente di produzione, si consiglia di utilizzare librerie specializzate come `node-cron` o `cron-parser`
- La persistenza delle configurazioni e degli stati di esecuzione richiede un sistema di storage esterno (non incluso)
