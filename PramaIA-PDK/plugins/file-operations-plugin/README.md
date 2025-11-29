# File Operations Plugin

Plugin completo per operazioni avanzate sui file del sistema all'interno dell'ecosistema PramaIA.

## 🚀 Caratteristiche

Il plugin supporta **8 operazioni principali**:

- **📂 open_explorer**: Apre finestra Explorer/Finder su path specificato
- **📋 copy**: Copia file o cartelle con opzioni avanzate
- **🔄 move**: Sposta file o cartelle tra percorsi
- **🗑️ delete**: Elimina file con conferma opzionale
- **📦 zip**: Crea archivi ZIP con compressione configurabile
- **📦 unzip**: Estrae archivi ZIP
- **📁 create_dir**: Crea cartelle con percorsi annidati
- **ℹ️ file_info**: Ottiene informazioni dettagliate su file/cartelle

## 📋 Struttura Plugin

```
file-operations-plugin/
├── plugin.json              # Configurazione nodo PDK
├── src/
│   ├── __init__.py          # Package Python
│   └── file_operations_processor.py  # Logica operazioni
├── test_file_operations.py  # Suite di test completa
└── README.md                # Questa documentazione
```

## 🔧 Configurazione

Il plugin è pre-configurato con sensati default. Parametri supportati:

- **operation**: Tipo operazione (obbligatorio)
- **source_path**: Percorso sorgente (obbligatorio)
- **destination_path**: Percorso destinazione (per copy, move, zip, unzip)
- **confirm_delete**: Conferma eliminazione (default: true)
- **overwrite**: Sovrascrittura file esistenti (default: false)  
- **zip_compression**: Livello compressione ZIP (none/fast/best)

## 📖 Esempi di Utilizzo

### Apertura Explorer
```json
{
  "operation": "open_explorer",
  "source_path": "C:\\Users\\Username\\Documents"
}
```

### Copia File/Cartella
```json
{
  "operation": "copy",
  "source_path": "C:\\source\\file.txt",
  "destination_path": "C:\\destination\\file.txt",
  "overwrite": false
}
```

### Creazione ZIP
```json
{
  "operation": "zip",
  "source_path": "C:\\folder\\to\\compress",
  "destination_path": "C:\\archive.zip",
  "zip_compression": "best"
}
```

### Informazioni File
```json
{
  "operation": "file_info",
  "source_path": "C:\\some\\file.txt"
}
```

## 🧪 Test

Eseguire la suite di test completa:

```bash
cd PramaIA-PDK/plugins/file-operations-plugin
python test_file_operations.py
```

I test verificano:
- ✅ Tutte le 8 operazioni principali
- ✅ Gestione errori e edge cases
- ✅ Validazione input/output
- ✅ Operazioni su file temporanei

## 🌟 Funzionalità Avanzate

### Cross-Platform
- **Windows**: Supporto completo con Explorer
- **macOS**: Integrazione Finder
- **Linux**: Supporto file manager XDG

### Sicurezza
- Conferma eliminazione con GUI (tkinter)
- Validazione percorsi esistenti
- Gestione permessi avanzata
- Prevenzione sovrascrittura accidentale

### Informazioni Dettagliate
- Dimensioni file in formato human-readable
- Timestamp di creazione/modifica/accesso
- Conteggio file per cartelle
- Metadata estensioni e permessi

### Compressione ZIP
- Supporto compressione configurabile
- Preservazione struttura cartelle
- Estrazione con conteggio file
- Gestione ZIP corrotti

## 🔌 Integrazione PDK

Il plugin è completamente integrato con l'architettura PDK:

- Configurazione JSON completa
- Processore asincrono
- Validazione input automatica
- Output strutturato
- Logging dettagliato

## ⚡ Performance

- Operazioni asincrone per non bloccare UI
- Gestione memoria ottimizzata per file grandi
- Logging configurabile per debug
- Cleanup automatico risorse temporanee

## 🛠️ Sviluppo

Per estendere il plugin:

1. Aggiungere operazione in `plugin.json`
2. Implementare metodo in `FileOperationsProcessor`
3. Aggiungere test in `test_file_operations.py`
4. Aggiornare documentazione

## 📝 Note Tecniche

- **Dipendenze**: Python 3.7+, tkinter, pathlib, shutil, zipfile
- **Limitazioni**: Operazioni di rete non supportate
- **Encoding**: UTF-8 per tutti i path
- **Timeout**: Nessun timeout definito (operazioni sincrone)

## 🚦 Status

- ✅ **Implementazione**: Completa
- ✅ **Test Suite**: 8/8 test passati  
- ✅ **Documentazione**: Completa
- ⏳ **Integrazione PDK**: Da testare in ambiente reale

---

**Versione**: 1.0.0  
**Autore**: PramaIA Development Team  
**Licenza**: Per uso interno PramaIA ecosystem