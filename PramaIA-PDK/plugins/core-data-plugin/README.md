# Core Data Plugin

Questo plugin fornisce i nodi di elaborazione dati standard per i workflow PramaIA. I nodi consentono di elaborare, trasformare e combinare dati in vari formati.

## Nodi Inclusi

### JSON Processor
Elabora e manipola dati in formato JSON.

**Input:**
- `data` (obbligatorio): Dati JSON da elaborare
- `path` (opzionale): Percorso JSON per estrazione (es. 'results.items[0].title')

**Output:**
- `result`: Risultato dell'elaborazione JSON

**Configurazione:**
- `operation`: Tipo di operazione (extract, transform, filter, merge)
- `extraction_path`: Percorso per estrarre valori
- `filter_condition`: Condizione per filtrare dati
- `transform_template`: Template per trasformare i dati
- `default_value`: Valore di default se l'estrazione fallisce

### CSV Processor
Elabora e manipola dati in formato CSV.

**Input:**
- `data` (obbligatorio): Dati CSV in formato stringa o percorso file
- `query` (opzionale): Query SQL-like per filtrare/selezionare dati

**Output:**
- `result`: Risultato dell'elaborazione CSV come array di oggetti

**Configurazione:**
- `has_header`: Se il CSV ha una riga di intestazione
- `delimiter`: Carattere delimitatore per il CSV
- `output_format`: Formato dei dati di output (array, json, csv)
- `filter_expression`: Espressione per filtrare le righe
- `selected_columns`: Colonne da includere nell'output

### Data Merger
Unisce più fonti di dati in un'unica struttura.

**Input:**
- `data1` (obbligatorio): Prima fonte di dati
- `data2` (obbligatorio): Seconda fonte di dati
- `data3` (opzionale): Terza fonte di dati

**Output:**
- `result`: Risultato dell'unione dei dati

**Configurazione:**
- `merge_type`: Modalità di unione (concat, join, zip, merge_objects)
- `join_key`: Chiave da usare per unire i dati (per join)
- `join_type`: Tipo di join da eseguire (inner, left, right, full)
- `flatten_result`: Se appiattire il risultato in un array singolo

## Installazione

Questo plugin è parte della suite di plugin core di PramaIA e viene installato automaticamente con il PDK.

Per garantire il corretto funzionamento, sono richieste le seguenti dipendenze:
```
pip install pandas jsonpath-ng
```

## Utilizzo

I nodi possono essere aggiunti ai workflow tramite l'interfaccia di PramaIA. Per ogni nodo, configurare i parametri necessari in base alle proprie esigenze.

### Esempi

#### Estrazione dati JSON
```json
{
  "nodes": {
    "1": {
      "id": "1",
      "type": "json_processor",
      "config": {
        "operation": "extract",
        "extraction_path": "data.items[*].name"
      }
    }
  },
  "edges": {
    "1": {
      "source": "altroNodo",
      "sourceHandle": "output",
      "target": "1",
      "targetHandle": "data"
    }
  }
}
```

#### Filtro dati CSV
```json
{
  "nodes": {
    "1": {
      "id": "1",
      "type": "csv_processor",
      "config": {
        "has_header": true,
        "delimiter": ",",
        "filter_expression": "age > 30",
        "selected_columns": "name,email,age"
      }
    }
  },
  "edges": {
    "1": {
      "source": "altroNodo",
      "sourceHandle": "output",
      "target": "1",
      "targetHandle": "data"
    }
  }
}
```

#### Unione di dati
```json
{
  "nodes": {
    "1": {
      "id": "1",
      "type": "data_merger",
      "config": {
        "merge_type": "join",
        "join_key": "id",
        "join_type": "inner"
      }
    }
  },
  "edges": {
    "1": {
      "source": "nodoA",
      "sourceHandle": "output",
      "target": "1",
      "targetHandle": "data1"
    },
    "2": {
      "source": "nodoB",
      "sourceHandle": "output",
      "target": "1",
      "targetHandle": "data2"
    }
  }
}
```

## Dipendenze

- Python 3.8+
- pandas: per l'elaborazione efficiente di dati tabulari
- jsonpath-ng: per l'estrazione avanzata di dati JSON

## Sviluppo

Per estendere la funzionalità di un nodo:

1. Modifica il file del processore corrispondente in `src/`
2. Aggiorna il file `plugin.json` se necessario
3. Ricarica il plugin nel PDK

---

&copy; 2023-2024 PramaIA Team
