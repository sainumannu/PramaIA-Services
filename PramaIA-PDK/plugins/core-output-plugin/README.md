# Core Output Plugin

Questo plugin fornisce i nodi di output standard per i workflow PramaIA. I nodi consentono di visualizzare risultati, salvare contenuti su file e inviare email.

## Nodi Inclusi

### Text Output
Visualizza output testuale all'utente in vari formati (testo semplice, markdown, HTML).

**Input:**
- `text` (obbligatorio): Testo da visualizzare
- `title` (opzionale): Titolo opzionale per l'output

**Configurazione:**
- `format`: Formato di visualizzazione (plain, markdown, html)
- `template`: Template opzionale per formattare il testo

### File Output
Salva l'output su file nel filesystem.

**Input:**
- `content` (obbligatorio): Contenuto da salvare nel file
- `filename` (opzionale): Nome del file (altrimenti usa quello configurato)

**Output:**
- `path`: Percorso completo del file salvato

**Configurazione:**
- `default_filename`: Nome file di default se non specificato
- `directory`: Directory dove salvare il file
- `overwrite`: Se sovrascrivere i file esistenti

### Email Output
Invia l'output via email.

**Input:**
- `content` (obbligatorio): Contenuto dell'email
- `subject` (opzionale): Oggetto dell'email
- `recipient` (opzionale): Destinatario dell'email
- `attachments` (opzionale): Lista di file da allegare

**Output:**
- `status`: Stato dell'invio dell'email

**Configurazione:**
- Impostazioni SMTP (server, porta, username, password)
- Impostazioni email (mittente, destinatario di default, oggetto di default)

## Installazione

Questo plugin è parte della suite di plugin core di PramaIA e viene installato automaticamente con il PDK.

## Utilizzo

I nodi possono essere aggiunti ai workflow tramite l'interfaccia di PramaIA. Per ogni nodo, configurare i parametri necessari in base alle proprie esigenze.

### Esempi

#### Output Testuale
```json
{
  "nodes": {
    "1": {
      "id": "1",
      "type": "text_output",
      "config": {
        "format": "markdown",
        "template": "## {{title}}\n\n{{text}}"
      }
    }
  },
  "edges": {
    "1": {
      "source": "altroNodo",
      "sourceHandle": "output",
      "target": "1",
      "targetHandle": "text"
    }
  }
}
```

#### Salvataggio su File
```json
{
  "nodes": {
    "1": {
      "id": "1",
      "type": "file_output",
      "config": {
        "default_filename": "risultato.json",
        "directory": "output_workflow",
        "overwrite": true
      }
    }
  },
  "edges": {
    "1": {
      "source": "altroNodo",
      "sourceHandle": "output",
      "target": "1",
      "targetHandle": "content"
    }
  }
}
```

## Dipendenze

- Python 3.8+
- Moduli Python standard: `smtplib`, `email`

## Sviluppo

Per estendere la funzionalità di un nodo:

1. Modifica il file del processore corrispondente in `src/`
2. Aggiorna il file `plugin.json` se necessario
3. Ricarica il plugin nel PDK

---

&copy; 2023-2024 PramaIA Team
