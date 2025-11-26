# Workflow Templates per Nodi RAG Generici

Questa cartella contiene template di workflow che dimostrano come utilizzare i nodi RAG generici in diversi contesti e scenari.

## Chat Processing Workflow

Workflow per l'elaborazione di domande utenti in sistema di chat:

```json
{
  "name": "chat_processing_workflow",
  "description": "Elaborazione completa di domande utenti in chat",
  "version": "1.0.0",
  "nodes": [
    {
      "id": "query_analysis",
      "type": "generic_query_analyzer",
      "config": {
        "analysis_types": ["classification", "intent", "strategy"],
        "analysis_patterns": {
          "semantic": ["contenuto", "spiega", "cos'è", "come", "dimmi"],
          "metadata": ["quando", "autore", "tipo", "data", "formato"],
          "intent_search": ["trova", "cerca", "mostra"],
          "intent_info": ["cos'è", "cosa", "chi", "dove"]
        },
        "output_format": "detailed"
      }
    },
    {
      "id": "semantic_search", 
      "type": "generic_semantic_search",
      "config": {
        "backend_type": "vectorstore",
        "backend_config": {
          "base_url": "http://localhost:8090"
        },
        "max_results": 5,
        "include_snippets": true
      },
      "condition": "query_analysis.strategy.needs_semantic == true"
    },
    {
      "id": "metadata_search",
      "type": "generic_metadata_search", 
      "config": {
        "extractors": {
          "date_enabled": true,
          "file_type_enabled": true,
          "author_enabled": true
        },
        "max_results": 5
      },
      "condition": "query_analysis.strategy.needs_metadata == true"
    },
    {
      "id": "result_aggregation",
      "type": "generic_aggregator",
      "config": {
        "source_weights": {
          "semantic_search": 0.7,
          "metadata_search": 0.3
        },
        "output_format": "structured",
        "max_total_results": 10
      }
    }
  ],
  "flows": [
    {
      "from": "INPUT",
      "to": "query_analysis",
      "data_mapping": {
        "query": "question"
      }
    },
    {
      "from": "query_analysis",
      "to": "semantic_search", 
      "data_mapping": {
        "query": "original_query"
      }
    },
    {
      "from": "query_analysis",
      "to": "metadata_search",
      "data_mapping": {
        "query": "original_query" 
      }
    },
    {
      "from": "semantic_search",
      "to": "result_aggregation",
      "data_mapping": {
        "semantic_results": "*"
      }
    },
    {
      "from": "metadata_search", 
      "to": "result_aggregation",
      "data_mapping": {
        "metadata_results": "*"
      }
    },
    {
      "from": "result_aggregation",
      "to": "OUTPUT"
    }
  ]
}
```

## Document Analysis Workflow

Workflow per analisi automatica di documenti:

```json
{
  "name": "document_analysis_workflow",
  "description": "Analisi automatica di contenuto e metadati di documenti",
  "version": "1.0.0",
  "nodes": [
    {
      "id": "content_analyzer",
      "type": "generic_query_analyzer",
      "config": {
        "analysis_types": ["classification", "sentiment", "entities", "complexity"],
        "analysis_patterns": {
          "technical": ["error", "warning", "exception", "debug"],
          "business": ["revenue", "profit", "customer", "market"],
          "legal": ["contract", "agreement", "terms", "liability"],
          "financial": ["cost", "budget", "expense", "investment"]
        },
        "input_field": "document_content",
        "output_format": "detailed"
      }
    },
    {
      "id": "metadata_enrichment",
      "type": "generic_metadata_search",
      "config": {
        "extractors": {
          "date_enabled": true,
          "author_enabled": true,
          "size_enabled": true,
          "custom": {
            "category_extractor": {
              "field_patterns": {
                "department": {
                  "patterns": ["dept\\s+(\\w+)", "department\\s+(\\w+)"],
                  "type": "string"
                },
                "priority": {
                  "patterns": ["priority\\s+(\\d+)", "urgent", "high", "low"],
                  "type": "string"
                }
              }
            }
          }
        },
        "input_field": "document_content"
      }
    },
    {
      "id": "analysis_aggregation",
      "type": "generic_aggregator",
      "config": {
        "source_weights": {
          "content_analyzer": 0.6,
          "metadata_enrichment": 0.4
        },
        "scoring_method": "weighted_average",
        "output_format": "formatted_text",
        "format_templates": {
          "item_template": "• {category}: {content} (Score: {score})",
          "summary_template": "Document Analysis Complete: {count} insights extracted"
        }
      }
    }
  ]
}
```

## Search Results Merging Workflow

Workflow per unire risultati da motori di ricerca diversi:

```json
{
  "name": "search_merging_workflow", 
  "description": "Unisce risultati da fonti di ricerca multiple",
  "version": "1.0.0",
  "nodes": [
    {
      "id": "query_classification",
      "type": "generic_query_analyzer",
      "config": {
        "analysis_types": ["classification", "intent"],
        "analysis_patterns": {
          "academic": ["research", "study", "paper", "journal"],
          "commercial": ["buy", "price", "product", "shop"],
          "news": ["news", "article", "breaking", "today"],
          "technical": ["how to", "tutorial", "guide", "documentation"]
        },
        "output_format": "classification_only"
      }
    },
    {
      "id": "vectorstore_search",
      "type": "generic_semantic_search",
      "config": {
        "backend_type": "vectorstore",
        "backend_config": {
          "base_url": "http://localhost:8090"
        },
        "max_results": 10
      }
    },
    {
      "id": "elasticsearch_search",
      "type": "generic_semantic_search",
      "config": {
        "backend_type": "elasticsearch",
        "backend_config": {
          "base_url": "http://localhost:9200",
          "index": "documents"
        },
        "max_results": 10
      }
    },
    {
      "id": "external_api_search",
      "type": "generic_semantic_search",
      "config": {
        "backend_type": "http",
        "backend_config": {
          "base_url": "https://api.example.com",
          "endpoint": "/search",
          "payload_template": {
            "q": "{query}",
            "format": "json"
          },
          "response_mapping": {
            "results_field": "data.results",
            "id_field": "id",
            "content_field": "description",
            "score_field": "relevance"
          }
        }
      }
    },
    {
      "id": "unified_results",
      "type": "generic_aggregator",
      "config": {
        "source_weights": {
          "vectorstore_search": 0.5,
          "elasticsearch_search": 0.3,
          "external_api_search": 0.2
        },
        "enable_deduplication": true,
        "deduplication_field": "content",
        "similarity_threshold": 0.85,
        "max_total_results": 15,
        "scoring_method": "weighted_average"
      }
    }
  ]
}
```

## Analytics Pipeline Workflow

Workflow per pipeline di analytics con dati real-time e storici:

```json
{
  "name": "analytics_pipeline_workflow",
  "description": "Pipeline di analytics per combinare dati real-time e storici",
  "version": "1.0.0",
  "nodes": [
    {
      "id": "metric_analyzer",
      "type": "generic_query_analyzer",
      "config": {
        "analysis_types": ["classification", "entities"],
        "analysis_patterns": {
          "performance": ["response_time", "throughput", "latency"],
          "errors": ["error_rate", "failure", "exception"],
          "business": ["conversion", "revenue", "users"]
        },
        "input_field": "metric_query"
      }
    },
    {
      "id": "realtime_data",
      "type": "generic_semantic_search",
      "config": {
        "backend_type": "http",
        "backend_config": {
          "base_url": "http://localhost:3000",
          "endpoint": "/api/realtime/search",
          "headers": {
            "Authorization": "Bearer {api_token}"
          }
        },
        "default_search_params": {
          "time_range": "15m",
          "aggregation": "avg"
        }
      }
    },
    {
      "id": "historical_data",
      "type": "generic_metadata_search",
      "config": {
        "extractors": {
          "date_enabled": true,
          "custom": {
            "metric_extractor": {
              "field_patterns": {
                "metric_name": {
                  "patterns": ["metric\\s+(\\w+)", "(\\w+)_metric"],
                  "type": "string"
                },
                "time_period": {
                  "patterns": ["last\\s+(\\d+)\\s+(day|hour|minute)", "past\\s+(\\w+)"],
                  "type": "string"
                }
              }
            }
          }
        }
      }
    },
    {
      "id": "trend_analysis",
      "type": "generic_aggregator",
      "config": {
        "source_weights": {
          "realtime_data": 0.7,
          "historical_data": 0.3
        },
        "scoring_method": "weighted_average",
        "output_format": "formatted_text",
        "format_templates": {
          "item_template": "Trend: {metric} = {value} (Change: {change}%)",
          "summary_template": "Analytics Summary: {count} metrics analyzed"
        }
      }
    }
  ]
}
```

## E-commerce Product Search Workflow

Workflow per ricerca prodotti e-commerce multi-criterio:

```json
{
  "name": "ecommerce_search_workflow",
  "description": "Ricerca prodotti con criteri multipli per e-commerce",
  "version": "1.0.0", 
  "nodes": [
    {
      "id": "search_intent_analysis",
      "type": "generic_query_analyzer",
      "config": {
        "analysis_types": ["classification", "intent", "entities"],
        "analysis_patterns": {
          "product_search": ["cerca", "trova", "voglio", "comprare"],
          "comparison": ["confronta", "differenza", "meglio", "vs"],
          "price_focused": ["prezzo", "economico", "costoso", "offerta"],
          "feature_focused": ["caratteristiche", "specifiche", "funzioni"]
        },
        "custom_classifiers": {
          "price_extractor": {
            "patterns": {
              "budget": ["budget\\s+(\\d+)", "massimo\\s+(\\d+)", "fino\\s+a\\s+(\\d+)"],
              "range": ["tra\\s+(\\d+)\\s+e\\s+(\\d+)", "da\\s+(\\d+)\\s+a\\s+(\\d+)"]
            }
          }
        }
      }
    },
    {
      "id": "product_semantic_search",
      "type": "generic_semantic_search",
      "config": {
        "backend_type": "vectorstore",
        "backend_config": {
          "base_url": "http://localhost:8090"
        },
        "default_search_params": {
          "collection": "products",
          "limit": 20
        },
        "min_score": 0.3
      }
    },
    {
      "id": "product_metadata_filter",
      "type": "generic_metadata_search",
      "config": {
        "extractors": {
          "custom": {
            "price_range": {
              "field_patterns": {
                "min_price": {
                  "patterns": ["sopra\\s+(\\d+)", "più\\s+di\\s+(\\d+)"],
                  "type": "number"
                },
                "max_price": {
                  "patterns": ["sotto\\s+(\\d+)", "meno\\s+di\\s+(\\d+)"],
                  "type": "number"
                },
                "brand": {
                  "patterns": ["marca\\s+(\\w+)", "brand\\s+(\\w+)", "(\\w+)\\s+brand"],
                  "type": "string"
                },
                "category": {
                  "patterns": ["categoria\\s+(\\w+)", "tipo\\s+(\\w+)"],
                  "type": "string"
                }
              }
            }
          }
        },
        "data_source": {
          "type": "vectorstore",
          "config": {
            "base_url": "http://localhost:8090"
          }
        }
      }
    },
    {
      "id": "product_ranking",
      "type": "generic_aggregator", 
      "config": {
        "source_weights": {
          "product_semantic_search": 0.6,
          "product_metadata_filter": 0.4
        },
        "enable_deduplication": true,
        "deduplication_field": "product_id",
        "max_total_results": 12,
        "scoring_method": "weighted_average",
        "output_format": "structured"
      }
    }
  ]
}
```

## Utilizzo dei Template

### 1. Personalizzazione

Ogni template può essere personalizzato modificando:

- **Pattern di analisi**: Adattare alle lingue e domini specifici
- **Backend configuration**: Cambiare URL e parametri dei servizi
- **Pesi di aggregazione**: Modificare l'importanza relativa delle fonti
- **Filtri e soglie**: Regolare criteri di qualità e rilevanza

### 2. Estensibilità

I template possono essere estesi aggiungendo:

- **Nuovi estrattori**: Per criteri di metadati specifici del dominio
- **Backend personalizzati**: Connettori per API proprietarie
- **Logica di scoring**: Algoritmi di ranking personalizzati
- **Formati di output**: Template di presentazione specifici

### 3. Composabilità

I template dimostrano come:

- **Combinare nodi generici**: Creare pipeline complesse da componenti semplici
- **Riutilizzare configurazioni**: Pattern ripetibili per scenari simili  
- **Condizionare flussi**: Esecuzione dinamica basata sui risultati
- **Mappare dati**: Trasformazioni tra formati di nodi diversi

### 4. Best Practices

- **Naming Convention**: Usare nomi descrittivi per nodi e flussi
- **Error Handling**: Configurare fallback e timeout appropriati
- **Performance**: Bilanciare qualità vs velocità nei parametri
- **Monitoring**: Includere metadati per debugging e analytics

Questi template dimostrano la vera riutilizzabilità dei nodi RAG generici, mostrando come gli stessi componenti possono essere configurati per scenari completamente diversi.