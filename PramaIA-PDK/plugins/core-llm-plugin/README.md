# Core LLM Plugin

Questo plugin fornisce i nodi per l'integrazione con diversi modelli di linguaggio (LLM) nei workflow PramaIA. Questi nodi consentono di inviare prompt ai modelli e ricevere risposte generate.

## Nodi disponibili

### OpenAI

Questo nodo integra i modelli OpenAI (GPT-3.5, GPT-4, ecc.).

**Configurazione:**
- **Modello**: Il modello OpenAI da utilizzare
- **Token massimi**: Numero massimo di token nella risposta
- **Temperatura**: Controllo della creatività (0-1)

**Input:**
- **prompt**: Testo da inviare al modello
- **system** (opzionale): Messaggio di sistema

**Output:**
- **response**: Testo della risposta
- **full_response**: Risposta completa dall'API con tutti i metadati

### Anthropic

Questo nodo integra i modelli Anthropic Claude.

**Configurazione:**
- **Modello**: Il modello Anthropic da utilizzare
- **Token massimi**: Numero massimo di token nella risposta
- **Temperatura**: Controllo della creatività (0-1)

**Input:**
- **prompt**: Testo da inviare al modello
- **system** (opzionale): Messaggio di sistema

**Output:**
- **response**: Testo della risposta
- **full_response**: Risposta completa dall'API con tutti i metadati

### Google Gemini

Questo nodo integra i modelli Google Gemini.

**Configurazione:**
- **Modello**: Il modello Gemini da utilizzare
- **Token massimi**: Numero massimo di token nella risposta
- **Temperatura**: Controllo della creatività (0-1)

**Input:**
- **prompt**: Testo da inviare al modello
- **system** (opzionale): Messaggio di sistema

**Output:**
- **response**: Testo della risposta
- **full_response**: Risposta completa dall'API con tutti i metadati

### Ollama

Questo nodo integra modelli Ollama self-hosted.

**Configurazione:**
- **Modello**: Il modello Ollama da utilizzare
- **Endpoint**: URL dell'endpoint Ollama
- **Temperatura**: Controllo della creatività (0-1)

**Input:**
- **prompt**: Testo da inviare al modello
- **system** (opzionale): Messaggio di sistema

**Output:**
- **response**: Testo della risposta
- **full_response**: Risposta completa dall'API con tutti i metadati

## Utilizzo

Questi nodi sono tipicamente utilizzati dopo nodi di input o di elaborazione dati, per generare risposte basate sui dati elaborati.

## Esempi

### Workflow di risposta a domande
```
User Input → OpenAI → Text Output
```

### Workflow di generazione con contesto
```
File Input → Text Processor → Anthropic → Output
```
