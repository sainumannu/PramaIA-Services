# Core RAG Plugin

Questo plugin fornisce i nodi essenziali per implementare sistemi RAG (Retrieval Augmented Generation) nei workflow PramaIA.

## Descrizione

Il plugin Core RAG contiene i componenti fondamentali per costruire flussi di lavoro basati su RAG:

- **Text Chunker**: Divide documenti di testo in chunk più piccoli per l'elaborazione
- **Text Embedder**: Converte testo in embedding vettoriali per ricerca semantica
- **Vector Store**: Salva e recupera embedding vettoriali da un database vettoriale
- **RAG Prompt Builder**: Costruisce prompt per LLM arricchiti con contesto recuperato

## Nodi disponibili

### Text Chunker

Il nodo Text Chunker divide un testo lungo in frammenti (chunk) più piccoli, essenziali per l'elaborazione e l'archiviazione efficiente in un sistema RAG.

**Input:**
- `text`: Testo da suddividere in chunk
- `metadata` (opzionale): Metadati da associare ai chunk

**Output:**
- `chunks`: Array di chunk di testo

**Configurazione:**
- `chunk_size`: Dimensione massima del chunk (in caratteri)
- `chunk_overlap`: Sovrapposizione tra chunk consecutivi
- `split_method`: Metodo di divisione (character, word, sentence, paragraph, recursive)
- `include_metadata`: Includere i metadati originali in ogni chunk
- `add_chunk_metadata`: Aggiungere metadati relativi al numero e posizione del chunk

### Text Embedder

Il nodo Text Embedder converte il testo in rappresentazioni vettoriali (embedding) che catturano il significato semantico, permettendo ricerche basate sulla similarità.

**Input:**
- `text`: Testo singolo da convertire in embedding
- `texts` (opzionale): Array di testi da convertire in embedding
- `metadata` (opzionale): Metadati da associare agli embedding

**Output:**
- `embeddings`: Array di embedding vettoriali
- `documents`: Array di documenti con testo e embedding

**Configurazione:**
- `model`: Tipo di modello di embedding (openai, sentence-transformers, huggingface, custom)
- `model_name`: Nome specifico del modello
- `openai_api_key`: Chiave API per OpenAI (se si usa il modello OpenAI)
- `dimensions`: Dimensioni dell'embedding
- `batch_size`: Numero di testi da elaborare in un batch
- `normalize`: Normalizzare i vettori di embedding

### Vector Store

Il nodo Vector Store gestisce il salvataggio e il recupero di embedding vettoriali da un database vettoriale.

**Input:**
- `operation`: Operazione da eseguire (store, search, delete)
- `documents`: Documenti da salvare (per operation=store)
- `query`: Query di ricerca testuale (per operation=search)
- `query_embedding`: Embedding della query (per operation=search)
- `ids`: ID dei documenti da eliminare (per operation=delete)

**Output:**
- `results`: Risultati dell'operazione
- `status`: Stato dell'operazione

**Configurazione:**
- `db_type`: Tipo di database vettoriale (chroma, faiss, qdrant, milvus, pinecone, redis)
- `collection_name`: Nome della collezione nel database
- `persist_directory`: Directory per la persistenza dei dati
- `default_operation`: Operazione predefinita
- `embedding_dimension`: Dimensione degli embedding
- `similarity_metric`: Metrica di similarità per la ricerca
- `top_k`: Numero di risultati da restituire
- `connection_string`: Stringa di connessione per database remoti
- `api_key`: Chiave API per database remoti

### RAG Prompt Builder

Il nodo RAG Prompt Builder costruisce prompt per LLM arricchiti con il contesto recuperato dal sistema RAG.

**Input:**
- `query`: Query o domanda dell'utente
- `context_documents`: Documenti di contesto recuperati
- `system_message` (opzionale): Messaggio di sistema personalizzato

**Output:**
- `prompt`: Prompt completo in formato testo
- `messages`: Array di messaggi formattati per API chat

**Configurazione:**
- `prompt_template`: Template per il prompt (usa {{query}} e {{context}})
- `system_message_template`: Template per il messaggio di sistema
- `context_format`: Formato per il contesto (numbered, newline, bullet, paragraph)
- `max_context_length`: Lunghezza massima del contesto
- `include_metadata`: Includere i metadati nel contesto
- `output_format`: Formato dell'output (text, messages, both)

## Dipendenze

- numpy (>=1.20.0)
- chromadb (>=0.4.0)
- openai (>=1.0.0)
- sentence-transformers (>=2.2.0)

## Esempio di utilizzo

Un tipico flusso RAG con questo plugin consiste in:

1. Utilizzare il Text Chunker per dividere documenti in chunk gestibili
2. Utilizzare il Text Embedder per convertire i chunk in embedding
3. Salvare gli embedding nel Vector Store
4. Per una query:
   - Convertire la query in embedding
   - Cercare documenti simili nel Vector Store
   - Utilizzare il RAG Prompt Builder per costruire un prompt con il contesto recuperato
   - Inviare il prompt a un modello LLM per ottenere una risposta
