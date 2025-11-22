# Core Input Plugin

Questo plugin fornisce i nodi di input di base per i workflow PramaIA. Questi nodi consentono agli utenti di interagire con i workflow fornendo input testuali o caricando file.

## Nodi disponibili

### User Input

Questo nodo consente all'utente di inserire testo tramite un modulo nell'interfaccia utente. Il workflow si fermerà a questo nodo fino a quando l'utente non fornisce l'input richiesto.

**Configurazione:**
- **Prompt**: Il testo da mostrare all'utente per guidare l'input
- **Placeholder**: Testo di esempio mostrato nel campo di input

**Output:**
- **output**: Il testo inserito dall'utente

### File Input

Questo nodo consente all'utente di caricare file come input per il workflow. Il workflow si fermerà a questo nodo fino a quando l'utente non carica un file.

**Configurazione:**
- **Estensioni permesse**: Lista di estensioni di file che l'utente può caricare (es. .pdf, .txt)
- **Dimensione massima (MB)**: Dimensione massima del file in MB

**Output:**
- **content**: Contenuto testuale del file (se applicabile)
- **binary**: Contenuto binario del file
- **metadata**: Metadati del file (nome, dimensione, tipo, ecc.)

## Utilizzo

Questi nodi sono utili all'inizio di un workflow per raccogliere input dall'utente. Puoi collegarli ad altri nodi per elaborare l'input ricevuto.

## Esempi

### Workflow di processamento testo
```
User Input → Text Processor → Output
```

### Workflow di analisi file
```
File Input → File Parser → Data Analysis → Output
```
