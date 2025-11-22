# Database di Hash dei File

## Panoramica

Il sistema di tracciamento degli hash dei file è una componente fondamentale dell'agente `document-folder-monitor-agent`. Questo sistema permette di:

1. Rilevare file nuovi vs. file modificati
2. Evitare ri-elaborazioni non necessarie di file identici
3. Tracciare le modifiche ai documenti nel tempo
4. Supportare la de-duplicazione efficiente

## Configurazione

### Posizione del Database

Il database degli hash è configurato tramite la variabile d'ambiente `FILE_HASHES_DB` nel file `.env`:

```
FILE_HASHES_DB=data/file_hashes.db
```

> **IMPORTANTE**: La posizione del database è ora centralizzata e definita in questo file. Il percorso può essere relativo o assoluto. Se relativo, viene interpretato rispetto alla directory principale dell'agente.

### Struttura del Database

Il database `file_hashes.db` è un database SQLite contenente la tabella principale `file_hashes` con la seguente struttura:

```sql
CREATE TABLE file_hashes (
    file_path TEXT PRIMARY KEY,
    hash_value TEXT NOT NULL,
    size INTEGER NOT NULL,
    last_modified REAL NOT NULL,
    last_check REAL NOT NULL,
    vectorstore_id TEXT NULL
)
```

Dove:
- `file_path`: percorso completo del file (chiave primaria)
- `hash_value`: hash del file in formato: `path_component:size:mtime:md5_hash`
- `size`: dimensione del file in byte
- `last_modified`: timestamp dell'ultima modifica del file
- `last_check`: timestamp dell'ultimo controllo del file
- `vectorstore_id`: ID opzionale che collega il file al sistema vectorstore

## Algoritmo di Hash

Per ottimizzare le prestazioni, specialmente con file di grandi dimensioni, l'algoritmo di hash utilizza un approccio ibrido:

1. **File piccoli** (<100KB): hash MD5 completo del contenuto
2. **File grandi**: hash MD5 basato su:
   - Primi 4KB del file
   - Ultimi 4KB del file
   - Metadati: percorso della directory, dimensione e timestamp di modifica

Questo approccio garantisce:
- Alta probabilità di rilevare modifiche effettive
- Prestazioni ottimali anche con file di grandi dimensioni
- Unicità degli hash anche per file identici in directory diverse

## Gestione e Manutenzione

### Pulizia del Database

Per pulire il database degli hash, utilizzare lo script `clean_hash_db.py`:

```bash
python clean_hash_db.py
```

Questo script rimuove tutti gli hash dal database ma mantiene la struttura delle tabelle.

### Rimozione dei Database Obsoleti

Per rimuovere eventuali database di hash obsoleti (presenti in posizioni precedenti), utilizzare lo script `remove_old_hash_files.py`:

```bash
python remove_old_hash_files.py
```

Questo script:
1. Crea backup dei vecchi database
2. Rimuove i file obsoleti
3. Assicura che la directory per il nuovo database esista

## Ciclo di Vita degli Hash

1. **Creazione di un file**:
   - Viene calcolato un nuovo hash e memorizzato nel database

2. **Modifica di un file**:
   - Viene calcolato un nuovo hash
   - Confrontato con l'hash precedente per determinare se il file è cambiato

3. **Rimozione di un file**:
   - L'hash viene mantenuto nel database (per velocizzare eventuali ri-creazioni)
   - L'API supporta la rimozione esplicita degli hash tramite `remove_file_hash()`

## Risoluzione Problemi

### Hash non aggiornati

Se gli hash sembrano non aggiornarsi correttamente:

1. Verificare che il percorso nel file `.env` sia corretto
2. Assicurarsi che la directory esista e sia scrivibile
3. Pulire il database con `clean_hash_db.py`
4. Controllare i log per errori relativi al calcolo degli hash

### File rilevati erroneamente come modificati

Questo può accadere quando:

1. Il database degli hash è stato corrotto
2. Sono presenti più database degli hash in percorsi diversi
3. Gli hash sono calcolati in modo inconsistente

Soluzione: eseguire `remove_old_hash_files.py` seguito da `clean_hash_db.py`