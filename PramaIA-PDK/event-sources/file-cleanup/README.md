# FileCleanup / FileArchiver Node

Questo nodo PDK permette di eliminare o archiviare (spostare) un file dal filesystem.

## Parametri di input
- `file_path` (string): percorso assoluto del file da trattare (obbligatorio)
- `mode` (string): 'delete' per eliminare, 'archive' per spostare (default: archive)
- `backup_dir` (string): cartella di destinazione per archiviazione (richiesta se mode=archive)
- `log` (boolean): se true, stampa log su stdout (opzionale)

## Output
- `result` (string): messaggio di esito (successo, errore, percorso file archiviato)

## Configurazione opzionale (`plugin.json`)
- `default_mode`: modalità di default ('archive' o 'delete')
- `default_backup_dir`: cartella di backup di default

## Esempio di utilizzo

```python
from file_cleanup import resolve_file_cleanup

inputs = {
    'file_path': '/tmp/test.txt',
    'mode': 'archive',
    'backup_dir': '/tmp/backup',
    'log': True
}
result = resolve_file_cleanup(inputs)
print(result)
```

## Note
- Se il file non esiste, restituisce errore.
- In modalità archive, aggiunge timestamp al nome del file archiviato.
- In modalità delete, elimina definitivamente il file.
