# PramaIA Nodes Documentation Index

Questo indice contiene la documentazione dettagliata di tutti i nodi disponibili nel sistema PramaIA PDK, organizzati per plugin e categoria funzionale.

## Struttura Documentazione Nodi

Ogni nodo è documentato con:
- **Panoramica Funzionale**: Scopo e funzionalità principali
- **Configurazione Dettagliata**: Parametri e schema di configurazione
- **Input/Output Specifications**: Formati dati di input e output
- **Implementazione Tecnica**: Dettagli implementativi
- **Esempi di Utilizzo**: Casi d'uso pratici e configurazioni
- **Error Handling**: Gestione errori e strategie di recovery
- **Performance Considerations**: Ottimizzazioni e metriche performance
- **Integration Notes**: Integrazione con servizi e dipendenze

## Plugin: document-semantic-complete-plugin

### Nodi di Input
- **document_input_node** - Ricezione file documento per elaborazione semantica
- **query_input_node** - Ricezione query utente per ricerca semantica

### Nodi di Processing
- **pdf_text_extractor** - Estrazione testo da file PDF
- **text_chunker** - Divisione testo in chunk per elaborazione
- **text_embedder** - Generazione embeddings vettoriali per chunk
- **[chroma_vector_store](NODES/chroma_vector_store_node.md)** - Salvataggio embeddings nel database vettoriale ✅
- **[chroma_retriever](NODES/chroma_retriever_node.md)** - Ricerca semantica nel database vettoriale ✅
- **llm_processor** - Generazione risposta usando LLM con contesto

### Nodi di Output
- **document_results_formatter** - Formattazione risposta finale

## Plugin: core-rag-plugin

### Nodi RAG
- **text_chunker** - Divisione testi in chunk
- **text_embedder** - Conversione testo in embeddings
- **vector_store** - Gestione database vettoriali
- **rag_prompt_builder** - Costruzione prompt RAG per LLM

## Plugin: core-llm-plugin

### Nodi LLM
- **openai_chat** - Integrazione OpenAI Chat API
- **ollama_chat** - Integrazione Ollama locale
- **anthropic_chat** - Integrazione Anthropic Claude
- **gemini_chat** - Integrazione Google Gemini

## Plugin: core-data-plugin

### Nodi Dati
- **json_processor** - Elaborazione dati JSON
- **csv_processor** - Elaborazione file CSV
- **xml_processor** - Elaborazione documenti XML
- **data_transformer** - Trasformazione dati generica

## Plugin: internal-processors-plugin

### Processori Interni
- **metadata_processor** - Gestione metadati documenti
- **event_processor** - Elaborazione eventi sistema
- **workflow_processor** - Gestione stati workflow

## Plugin: pdf-monitor-plugin

### Monitoraggio PDF
- **pdf_monitor** - Monitoraggio directory per nuovi PDF
- **pdf_validator** - Validazione file PDF
- **pdf_metadata_extractor** - Estrazione metadati PDF

## Linee Guida Documentazione

### Template Documentazione
Ogni nodo deve seguire il template standard:

```markdown
# Documentazione Nodo: [Nome Nodo] ([id_nodo])

## Panoramica Funzionale
- Descrizione scopo principale
- Funzionalità chiave
- Posizione nella pipeline

## Configurazione Dettagliata
- Schema JSON di configurazione
- Parametri obbligatori e opzionali
- Valori default e range validi

## Input/Output Specifications
- Formati dati attesi
- Strutture JSON/oggetti
- Validazioni e constraints

## Implementazione Tecnica
- Classe principale processore
- Flusso di elaborazione
- Algoritmi utilizzati

## Esempi di Utilizzo
- Configurazioni comuni
- Casi d'uso tipici
- Integration patterns

## Error Handling
- Tipi di errori gestiti
- Strategie di recovery
- Logging errori

## Performance Considerations
- Metriche performance
- Ottimizzazioni implementate
- Configurazioni per scaling

## Integration Notes
- Dipendenze servizi
- API utilizzate
- Environment variables
```

### Convenzioni Documentazione

1. **File Naming**: `{node_id}_node.md`
2. **Directory**: `PramaIA-Docs/NODES/`
3. **Links**: Riferimenti incrociati tra nodi correlati
4. **Esempi**: Codice funzionante e testato
5. **Versioning**: Changelog e roadmap future

### Status Documentazione

| Plugin | Nodi Documentati | Nodi Totali | Status |
|--------|------------------|-------------|--------|
| document-semantic-complete-plugin | 2/9 | 9 | 🔄 In Progress |
| core-rag-plugin | 0/4 | 4 | ⏳ Pending |
| core-llm-plugin | 0/4 | 4 | ⏳ Pending |
| core-data-plugin | 0/4 | 4 | ⏳ Pending |
| internal-processors-plugin | 0/3 | 3 | ⏳ Pending |
| pdf-monitor-plugin | 0/3 | 3 | ⏳ Pending |

### Legenda Status
- ✅ **Completato**: Documentazione completa e aggiornata
- 🔄 **In Progress**: Documentazione in corso
- ⏳ **Pending**: Documentazione da iniziare
- ⚠️ **Needs Update**: Documentazione obsoleta

## Contribuire alla Documentazione

### Processo di Documentazione
1. **Analisi Nodo**: Studio implementazione e funzionalità
2. **Template Application**: Applicazione template standard
3. **Testing Examples**: Verifica esempi e configurazioni
4. **Review**: Revisione tecnica e linguistica
5. **Publication**: Aggiornamento indice e link

### Guidelines di Stile
- **Linguaggio**: Italiano tecnico chiaro e preciso
- **Esempi**: Pratici e immediatamente utilizzabili
- **Codice**: Sintassi evidenziata e commentata
- **Diagrammi**: UML o flowchart per flussi complessi
- **References**: Link a documentazione esterna

### Tools per Documentazione
- **Markdown**: Formato standard per documentazione
- **JSON Schema**: Validazione configurazioni nodi
- **PlantUML**: Diagrammi architetturali
- **Swagger/OpenAPI**: Documentazione API servizi

---

*Questa documentazione è mantenuta dal team PramaIA. Per contributi o segnalazioni, aprire issue nel repository PramaIA-Services.*