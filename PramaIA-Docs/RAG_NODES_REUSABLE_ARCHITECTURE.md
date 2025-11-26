# Nodi RAG Riutilizzabili - Architettura Generica

## Panoramica

Questo documento descrive l'implementazione di nodi RAG veramente riutilizzabili nel plugin `core-rag-plugin`. I nodi sono progettati come componenti LEGO modulari che possono essere utilizzati in diversi workflow e contesti, non solo per il processing di chat.

## Principi di Design

### 1. Reusabilità Totale
- **Input/Output Standardizzati**: Tutti i nodi utilizzano formati di input/output consistenti
- **Configurazione Flessibile**: Comportamento personalizzabile tramite parametri di configurazione
- **Context-Agnostic**: I nodi non fanno assunzioni sul contesto specifico (chat, search, ecc.)

### 2. Modularità
- **Single Responsibility**: Ogni nodo ha una responsabilità specifica e ben definita
- **Loose Coupling**: I nodi non dipendono da implementazioni specifiche di altri componenti
- **Composabilità**: I nodi possono essere combinati in workflow complessi

### 3. Genericità
- **Parametrizzazione**: Logica configurabile tramite parametri invece di codice hardcoded
- **Pattern Matching**: Riconoscimento automatico di pattern e strutture dati
- **Fallback**: Meccanismi di fallback per gestire input diversi dal previsto

## Nodi Implementati

### 1. Generic Aggregator (`generic_aggregator`)

**Scopo**: Aggregatore completamente generico per combinare risultati da fonti multiple.

**Caratteristiche Generiche**:
- **Riconoscimento Automatico Fonti**: Rileva automaticamente le fonti di risultati nell'input
- **Normalizzazione Adattiva**: Standardizza formati di dati diversi in struttura comune
- **Scoring Configurabile**: Multipli metodi di scoring (weighted_average, max, product, sum)
- **Output Multipli**: Strutturato, testo formattato, o raw data
- **Deduplicazione Intelligente**: Rimozione duplicati basata su campi configurabili

**Esempi di Utilizzo**:
```json
// Chat workflow
{
  "source_weights": {"semantic_results": 0.7, "metadata_results": 0.3},
  "output_format": "structured"
}

// Search workflow  
{
  "source_weights": {"primary_search": 0.8, "fallback_search": 0.2},
  "output_format": "formatted_text"
}

// Analytics workflow
{
  "source_weights": {"real_time": 0.6, "historical": 0.4},
  "scoring_method": "max",
  "deduplication_field": "entity_id"
}
```

### 2. Chat Query Analyzer (`chat_query_analyzer`)

**Stato**: Da refactorizzare per genericità

**Obiettivo Refactoring**:
- Trasformare da "chat-specific" a "query analyzer" generico
- Configurare pattern di riconoscimento invece di keywords hardcoded
- Supportare diversi tipi di analisi (intent, sentiment, classification, ecc.)

### 3. Semantic Search (`semantic_search`)

**Stato**: Da refactorizzare per genericità

**Obiettivo Refactoring**:
- Disaccoppiare da VectorstoreService specifico
- Supportare connettori generici per diversi backend
- Configurare mapping di response invece di assumere formato fisso

### 4. Metadata Search (`metadata_search`)

**Stato**: Da refactorizzare per genericità

**Obiettivo Refactoring**:
- Generalizzare pattern di estrazione metadati
- Supportare schemi di metadati configurabili
- Separare parsing da esecuzione query

## Workflow di Esempio

### Chat Processing (Caso Specifico)
```json
{
  "nodes": [
    {
      "id": "query_analysis",
      "type": "generic_query_analyzer",
      "config": {
        "analysis_patterns": {
          "semantic": ["contenuto", "spiega", "cos'è"],
          "metadata": ["quando", "autore", "tipo"]
        },
        "output_format": "classification"
      }
    },
    {
      "id": "semantic_search",
      "type": "generic_semantic_search", 
      "config": {
        "backend_type": "vectorstore_service",
        "endpoint_config": {"base_url": "http://localhost:8090"}
      }
    },
    {
      "id": "aggregation",
      "type": "generic_aggregator",
      "config": {
        "source_weights": {"semantic_results": 0.7, "metadata_results": 0.3},
        "output_format": "structured",
        "enable_deduplication": true
      }
    }
  ]
}
```

### Document Analysis (Altro Contesto)
```json
{
  "nodes": [
    {
      "id": "content_extraction",
      "type": "generic_query_analyzer",
      "config": {
        "analysis_patterns": {
          "technical": ["error", "warning", "exception"],
          "business": ["revenue", "profit", "customer"]
        },
        "output_format": "entity_extraction"
      }
    },
    {
      "id": "final_aggregation",
      "type": "generic_aggregator",
      "config": {
        "source_weights": {"technical_analysis": 0.5, "business_analysis": 0.5},
        "scoring_method": "sum",
        "output_format": "formatted_text",
        "format_templates": {
          "item_template": "• {category}: {content}",
          "summary_template": "Analysis complete: {count} insights from {sources} sources"
        }
      }
    }
  ]
}
```

## Pattern di Configurazione

### 1. Source Weights (Pesi per Fonte)
```json
{
  "source_weights": {
    "primary_source": 0.8,    // Fonte principale
    "secondary_source": 0.2,  // Fonte secondaria
    "search_*": 0.6,          // Pattern matching per nomi
    "fallback_*": 0.1         // Pattern per fonti di backup
  }
}
```

### 2. Output Formats (Formati di Output)
```json
{
  "output_format": "structured",     // Oggetto completo con metadati
  // OR
  "output_format": "formatted_text", // Testo formattato per display
  // OR
  "output_format": "raw"             // Solo array di risultati
}
```

### 3. Scoring Methods (Metodi di Scoring)
```json
{
  "scoring_method": "weighted_average", // (score * weight)
  // OR
  "scoring_method": "max",              // max(score, weight)
  // OR  
  "scoring_method": "product",          // score * weight * boost
  // OR
  "scoring_method": "sum"               // score + weight + bonus
}
```

### 4. Deduplication Strategies (Strategie di Deduplicazione)
```json
{
  "enable_deduplication": true,
  "deduplication_field": "id",          // Campo per identificare duplicati
  "similarity_threshold": 0.8,          // Soglia di similarità
  "merge_strategy": "best_score"        // Come combinare duplicati
}
```

## Vantaggi della Nuova Architettura

### 1. **Riutilizzabilità Reale**
- Un singolo nodo può servire diversi workflow
- Configurazione sostituisce codice specifico
- Riduzione della duplicazione di logica

### 2. **Manutenibilità**
- Un bug fix beneficia tutti gli utilizzi
- Miglioramenti si propagano automaticamente  
- Testing centralizzato

### 3. **Flessibilità**
- Nuovi casi d'uso senza nuovi nodi
- Combinazioni creative di nodi esistenti
- Estensibilità tramite configurazione

### 4. **Composabilità**
- Workflow complessi da componenti semplici
- Pattern riutilizzabili per scenari simili
- Separazione delle responsabilità

## Roadmap Refactoring

### Fase 1: ✅ Completata
- [x] Implementazione Generic Aggregator
- [x] Documentazione pattern generici
- [x] Registrazione nel plugin

### Fase 2: 🔄 In Corso
- [ ] Refactoring Chat Query Analyzer → Generic Query Analyzer
- [ ] Refactoring Semantic Search → Generic Semantic Search  
- [ ] Refactoring Metadata Search → Generic Metadata Search

### Fase 3: 📋 Pianificata
- [ ] Testing con workflow diversi da chat
- [ ] Ottimizzazione performance per casi generici
- [ ] Documentazione esempi avanzati
- [ ] Template workflow riutilizzabili

## Testing e Validazione

Per validare la reale riutilizzabilità, ogni nodo refactorizzato deve superare questi test:

1. **Test Multi-Contesto**: Funziona in almeno 3 workflow diversi
2. **Test Zero-Hardcode**: Nessuna logica hardcoded per casi specifici
3. **Test Configurazione**: Comportamento completamente personalizzabile
4. **Test Composabilità**: Si integra bene con altri nodi generici

## Conclusioni

La nuova architettura trasforma i nodi da componenti specifici per chat a veri building blocks riutilizzabili. Questo approche fornisce:

- **Flessibilità** per nuovi casi d'uso
- **Efficienza** nello sviluppo di workflow
- **Consistenza** nell'ecosistema PramaIA
- **Scalabilità** per future estensioni

I nodi sono ora veramente "LEGO" che possono essere combinati creativamente per costruire qualsiasi tipo di pipeline di processing, non solo per chat ma per qualsiasi scenario che richieda aggregazione, analisi e ricerca su dati.