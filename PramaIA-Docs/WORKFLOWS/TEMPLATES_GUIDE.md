# Workflow Templates Guide

**Pre-built Workflow Patterns for Common Use Cases**

This guide provides ready-to-use workflow templates that you can copy, customize, and deploy for common automation scenarios.

---

## 📚 **Template Categories**

### **🔄 Document Processing**
- [Document Ingestion Pipeline](#document-ingestion-pipeline)
- [PDF Processing Workflow](#pdf-processing-workflow)
- [Batch Document Import](#batch-document-import)

### **🤖 RAG & AI**
- [RAG Query Processing](#rag-query-processing)
- [Content Generation Pipeline](#content-generation-pipeline)
- [Semantic Search Enhancement](#semantic-search-enhancement)

### **🛠️ System Operations**
- [File Monitor Automation](#file-monitor-automation)
- [Database Maintenance](#database-maintenance)
- [Health Check Pipeline](#health-check-pipeline)

### **🔗 Integration**
- [API Data Sync](#api-data-sync)
- [Cross-Service Communication](#cross-service-communication)
- [External System Integration](#external-system-integration)

---

## 📄 **Document Processing Templates**

### **Document Ingestion Pipeline**

**Purpose:** Automatically process uploaded documents through complete ingestion pipeline

**Trigger:** File upload event  
**Duration:** 2-5 minutes  
**Use Case:** Document knowledge base management

```json
{
  "workflow": {
    "id": "document-ingestion-pipeline",
    "name": "Document Ingestion Pipeline",
    "description": "Complete document processing from upload to searchable vectors",
    "version": "1.0.0"
  },
  "trigger": {
    "event_type": "file_uploaded",
    "conditions": {
      "file_type": ["pdf", "docx", "txt", "md"],
      "size_max_mb": 50
    }
  },
  "nodes": [
    {
      "id": "document_processor",
      "type": "generic_document_processor",
      "config": {
        "strategy": "auto_detect",
        "extract_metadata": true,
        "clean_text": true
      },
      "inputs": {
        "file_path": "{{trigger.file_path}}"
      }
    },
    {
      "id": "text_chunker",
      "type": "generic_text_processor", 
      "config": {
        "strategy": "semantic_chunking",
        "chunk_size": 1000,
        "overlap": 200
      },
      "inputs": {
        "text": "{{document_processor.extracted_text}}"
      }
    },
    {
      "id": "embedding_generator",
      "type": "generic_text_processor",
      "config": {
        "strategy": "generate_embeddings",
        "model": "sentence-transformers/all-MiniLM-L6-v2"
      },
      "inputs": {
        "text_chunks": "{{text_chunker.chunks}}"
      }
    },
    {
      "id": "vector_store",
      "type": "generic_vector_store_processor",
      "config": {
        "strategy": "upsert",
        "collection": "documents",
        "include_metadata": true
      },
      "inputs": {
        "embeddings": "{{embedding_generator.embeddings}}",
        "texts": "{{text_chunker.chunks}}",
        "metadata": "{{document_processor.metadata}}"
      }
    },
    {
      "id": "index_updater",
      "type": "generic_system_processor",
      "config": {
        "strategy": "update_search_index",
        "index_type": "document"
      },
      "inputs": {
        "document_id": "{{vector_store.document_id}}",
        "collection": "documents"
      }
    }
  ],
  "error_handling": {
    "retry_attempts": 3,
    "fallback_strategy": "log_and_continue",
    "notification": {
      "on_error": true,
      "recipients": ["admin@example.com"]
    }
  }
}
```

**Customization Options:**
- **Chunking Strategy:** Fixed size, semantic, paragraph-based
- **Embedding Model:** Different transformer models or OpenAI
- **Collection Name:** Target vector store collection
- **Metadata Extraction:** Custom metadata fields

---

### **PDF Processing Workflow**

**Purpose:** Specialized PDF processing with OCR and table extraction

**Trigger:** PDF file upload  
**Duration:** 3-8 minutes  
**Use Case:** Complex document analysis

```json
{
  "workflow": {
    "id": "advanced-pdf-processor",
    "name": "Advanced PDF Processing",
    "description": "Comprehensive PDF processing with OCR, tables, and images"
  },
  "trigger": {
    "event_type": "file_uploaded",
    "conditions": {
      "file_extension": ".pdf",
      "size_max_mb": 100
    }
  },
  "nodes": [
    {
      "id": "pdf_analyzer",
      "type": "generic_document_processor",
      "config": {
        "strategy": "pdf_comprehensive",
        "extract_tables": true,
        "extract_images": true,
        "ocr_enabled": true
      },
      "inputs": {
        "file_path": "{{trigger.file_path}}"
      }
    },
    {
      "id": "content_separator",
      "type": "generic_text_processor",
      "config": {
        "strategy": "content_type_separation",
        "separate_tables": true,
        "separate_images": true
      },
      "inputs": {
        "document_content": "{{pdf_analyzer.content}}"
      }
    },
    {
      "id": "text_processor",
      "type": "generic_text_processor",
      "config": {
        "strategy": "semantic_chunking",
        "chunk_size": 800,
        "overlap": 150,
        "preserve_context": true
      },
      "inputs": {
        "text": "{{content_separator.text_content}}"
      }
    },
    {
      "id": "table_processor",
      "type": "generic_document_processor",
      "config": {
        "strategy": "table_to_text",
        "include_headers": true,
        "format": "markdown"
      },
      "inputs": {
        "tables": "{{content_separator.tables}}"
      }
    },
    {
      "id": "unified_embeddings",
      "type": "generic_text_processor",
      "config": {
        "strategy": "batch_embeddings",
        "model": "sentence-transformers/all-mpnet-base-v2"
      },
      "inputs": {
        "text_items": [
          "{{text_processor.chunks}}",
          "{{table_processor.table_texts}}"
        ]
      }
    },
    {
      "id": "structured_storage",
      "type": "generic_vector_store_processor",
      "config": {
        "strategy": "structured_upsert",
        "collection": "pdf_documents",
        "metadata_mapping": {
          "content_type": "auto",
          "source_file": "{{trigger.file_name}}",
          "processing_date": "{{workflow.timestamp}}"
        }
      },
      "inputs": {
        "embeddings": "{{unified_embeddings.embeddings}}",
        "texts": "{{unified_embeddings.source_texts}}",
        "metadata": "{{pdf_analyzer.metadata}}"
      }
    }
  ]
}
```

---

## 🤖 **RAG & AI Templates**

### **RAG Query Processing**

**Purpose:** Process user queries through complete RAG pipeline

**Trigger:** Query API call  
**Duration:** 2-10 seconds  
**Use Case:** Question answering system

```json
{
  "workflow": {
    "id": "rag-query-processor",
    "name": "RAG Query Processing",
    "description": "Complete RAG pipeline from query to enhanced response"
  },
  "trigger": {
    "event_type": "query_received",
    "conditions": {
      "query_length_min": 10,
      "query_type": ["question", "search", "analysis"]
    }
  },
  "nodes": [
    {
      "id": "query_analyzer",
      "type": "generic_text_processor",
      "config": {
        "strategy": "query_analysis",
        "extract_intent": true,
        "extract_entities": true
      },
      "inputs": {
        "query": "{{trigger.query}}"
      }
    },
    {
      "id": "query_enhancer",
      "type": "generic_llm_processor",
      "config": {
        "strategy": "query_enhancement",
        "model": "gpt-3.5-turbo",
        "enhance_for_search": true
      },
      "inputs": {
        "original_query": "{{trigger.query}}",
        "intent": "{{query_analyzer.intent}}",
        "entities": "{{query_analyzer.entities}}"
      }
    },
    {
      "id": "context_retriever",
      "type": "generic_vector_store_processor",
      "config": {
        "strategy": "similarity_search",
        "collection": "documents",
        "top_k": 10,
        "score_threshold": 0.7
      },
      "inputs": {
        "query": "{{query_enhancer.enhanced_query}}",
        "filters": "{{query_analyzer.filters}}"
      }
    },
    {
      "id": "context_reranker",
      "type": "generic_text_processor",
      "config": {
        "strategy": "rerank_contexts",
        "rerank_model": "cross-encoder",
        "max_contexts": 5
      },
      "inputs": {
        "query": "{{trigger.query}}",
        "contexts": "{{context_retriever.results}}"
      }
    },
    {
      "id": "response_generator",
      "type": "generic_llm_processor",
      "config": {
        "strategy": "rag_response",
        "model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 1000,
        "include_sources": true
      },
      "inputs": {
        "query": "{{trigger.query}}",
        "contexts": "{{context_reranker.top_contexts}}",
        "intent": "{{query_analyzer.intent}}"
      }
    },
    {
      "id": "response_enhancer",
      "type": "generic_text_processor",
      "config": {
        "strategy": "response_formatting",
        "include_citations": true,
        "format": "markdown"
      },
      "inputs": {
        "response": "{{response_generator.response}}",
        "sources": "{{context_reranker.sources}}"
      }
    },
    {
      "id": "feedback_logger",
      "type": "generic_system_processor",
      "config": {
        "strategy": "log_interaction",
        "log_level": "info",
        "include_metrics": true
      },
      "inputs": {
        "query": "{{trigger.query}}",
        "response": "{{response_enhancer.formatted_response}}",
        "context_count": "{{context_reranker.context_count}}",
        "processing_time": "{{workflow.duration}}"
      }
    }
  ],
  "output": {
    "response": "{{response_enhancer.formatted_response}}",
    "sources": "{{response_enhancer.sources}}",
    "confidence": "{{response_generator.confidence}}",
    "processing_time": "{{workflow.duration}}"
  }
}
```

---

## 🛠️ **System Operations Templates**

### **File Monitor Automation**

**Purpose:** Automated file system monitoring and processing

**Trigger:** File system change  
**Duration:** 30 seconds - 2 minutes  
**Use Case:** Real-time document processing

```json
{
  "workflow": {
    "id": "file-monitor-automation",
    "name": "File System Monitor",
    "description": "Automated processing of file system changes"
  },
  "trigger": {
    "event_type": "file_system_change",
    "conditions": {
      "event_types": ["created", "modified"],
      "file_extensions": [".pdf", ".docx", ".txt", ".md"],
      "ignore_patterns": ["temp*", ".*", "_*"]
    }
  },
  "nodes": [
    {
      "id": "file_validator",
      "type": "generic_system_processor",
      "config": {
        "strategy": "file_validation",
        "check_integrity": true,
        "check_permissions": true,
        "virus_scan": false
      },
      "inputs": {
        "file_path": "{{trigger.file_path}}"
      }
    },
    {
      "id": "duplicate_checker",
      "type": "generic_system_processor",
      "config": {
        "strategy": "duplicate_detection",
        "hash_algorithm": "sha256",
        "check_content": true
      },
      "inputs": {
        "file_path": "{{trigger.file_path}}"
      }
    },
    {
      "id": "conditional_processor",
      "type": "generic_system_processor",
      "config": {
        "strategy": "conditional_execution",
        "condition": "{{duplicate_checker.is_unique}} && {{file_validator.is_valid}}"
      },
      "inputs": {
        "condition_result": "{{duplicate_checker.is_unique}}"
      }
    },
    {
      "id": "document_processor",
      "type": "generic_document_processor",
      "config": {
        "strategy": "auto_detect",
        "extract_metadata": true
      },
      "inputs": {
        "file_path": "{{trigger.file_path}}"
      },
      "conditions": {
        "execute_if": "{{conditional_processor.should_execute}}"
      }
    },
    {
      "id": "metadata_enricher",
      "type": "generic_text_processor",
      "config": {
        "strategy": "metadata_extraction",
        "extract_summary": true,
        "extract_keywords": true
      },
      "inputs": {
        "text": "{{document_processor.extracted_text}}",
        "file_info": "{{trigger.file_info}}"
      }
    },
    {
      "id": "archive_manager",
      "type": "generic_system_processor",
      "config": {
        "strategy": "file_archival",
        "archive_location": "./processed/",
        "preserve_structure": true,
        "compress": false
      },
      "inputs": {
        "source_file": "{{trigger.file_path}}",
        "metadata": "{{metadata_enricher.metadata}}"
      }
    }
  ]
}
```

### **Database Maintenance**

**Purpose:** Automated database cleanup and optimization

**Trigger:** Scheduled (daily)  
**Duration:** 5-30 minutes  
**Use Case:** System maintenance

```json
{
  "workflow": {
    "id": "database-maintenance",
    "name": "Database Maintenance",
    "description": "Automated database cleanup and optimization"
  },
  "trigger": {
    "event_type": "scheduled",
    "schedule": "0 2 * * *",  // Daily at 2 AM
    "timezone": "UTC"
  },
  "nodes": [
    {
      "id": "health_checker",
      "type": "generic_system_processor",
      "config": {
        "strategy": "health_check",
        "services": ["vectorstore", "database", "cache"]
      }
    },
    {
      "id": "log_cleaner",
      "type": "generic_system_processor",
      "config": {
        "strategy": "log_cleanup",
        "retention_days": 30,
        "compress_old_logs": true
      }
    },
    {
      "id": "cache_optimizer",
      "type": "generic_system_processor",
      "config": {
        "strategy": "cache_optimization",
        "clear_expired": true,
        "defragment": true
      }
    },
    {
      "id": "vector_optimizer",
      "type": "generic_vector_store_processor",
      "config": {
        "strategy": "optimize_collections",
        "recompute_indexes": true,
        "remove_orphaned": true
      }
    },
    {
      "id": "backup_creator",
      "type": "generic_system_processor",
      "config": {
        "strategy": "create_backup",
        "backup_location": "./backups/",
        "include_vectors": true,
        "compress": true
      }
    },
    {
      "id": "report_generator",
      "type": "generic_text_processor",
      "config": {
        "strategy": "maintenance_report",
        "format": "markdown",
        "include_metrics": true
      },
      "inputs": {
        "health_status": "{{health_checker.status}}",
        "cleanup_results": "{{log_cleaner.results}}",
        "optimization_results": "{{cache_optimizer.results}}",
        "backup_info": "{{backup_creator.info}}"
      }
    },
    {
      "id": "notification_sender",
      "type": "generic_system_processor",
      "config": {
        "strategy": "send_notification",
        "recipients": ["admin@example.com"],
        "notification_type": "email"
      },
      "inputs": {
        "subject": "Daily Maintenance Report",
        "content": "{{report_generator.report}}"
      }
    }
  ]
}
```

---

## 🔗 **Integration Templates**

### **API Data Sync**

**Purpose:** Synchronize data between external APIs and vector store

**Trigger:** API webhook or scheduled  
**Duration:** 1-10 minutes  
**Use Case:** External data integration

```json
{
  "workflow": {
    "id": "api-data-sync",
    "name": "API Data Synchronization",
    "description": "Sync external API data to vector store"
  },
  "trigger": {
    "event_type": "webhook",
    "webhook_config": {
      "endpoint": "/webhooks/data-sync",
      "authentication": "bearer_token"
    }
  },
  "nodes": [
    {
      "id": "api_fetcher",
      "type": "generic_system_processor",
      "config": {
        "strategy": "api_request",
        "method": "GET",
        "url": "{{trigger.api_endpoint}}",
        "headers": {
          "Authorization": "Bearer {{env.API_TOKEN}}"
        }
      }
    },
    {
      "id": "data_transformer",
      "type": "generic_text_processor",
      "config": {
        "strategy": "data_transformation",
        "transformation_rules": [
          {"field": "content", "operation": "clean_html"},
          {"field": "date", "operation": "parse_iso"},
          {"field": "tags", "operation": "normalize_array"}
        ]
      },
      "inputs": {
        "raw_data": "{{api_fetcher.response_data}}"
      }
    },
    {
      "id": "change_detector",
      "type": "generic_system_processor",
      "config": {
        "strategy": "change_detection",
        "comparison_field": "updated_at",
        "last_sync_file": "./sync_state.json"
      },
      "inputs": {
        "current_data": "{{data_transformer.transformed_data}}"
      }
    },
    {
      "id": "content_processor",
      "type": "generic_text_processor",
      "config": {
        "strategy": "batch_embeddings",
        "model": "sentence-transformers/all-MiniLM-L6-v2"
      },
      "inputs": {
        "texts": "{{change_detector.changed_items}}"
      }
    },
    {
      "id": "vector_updater",
      "type": "generic_vector_store_processor",
      "config": {
        "strategy": "batch_upsert",
        "collection": "external_data",
        "conflict_resolution": "update"
      },
      "inputs": {
        "embeddings": "{{content_processor.embeddings}}",
        "texts": "{{content_processor.texts}}",
        "metadata": "{{data_transformer.metadata}}"
      }
    },
    {
      "id": "sync_tracker",
      "type": "generic_system_processor",
      "config": {
        "strategy": "update_sync_state",
        "state_file": "./sync_state.json"
      },
      "inputs": {
        "last_sync": "{{workflow.timestamp}}",
        "items_processed": "{{vector_updater.processed_count}}"
      }
    }
  ]
}
```

---

## 🎯 **Template Usage**

### **How to Use Templates**

1. **Copy Template** - Copy the JSON configuration
2. **Customize Configuration** - Modify nodes, settings, and triggers
3. **Test Workflow** - Test with sample data
4. **Deploy** - Upload to workflow engine

### **Template Customization**

#### **Common Modifications**
```json
// Change processing strategy
"config": {
  "strategy": "your_preferred_strategy",
  "custom_parameter": "your_value"
}

// Modify trigger conditions
"trigger": {
  "event_type": "your_event",
  "conditions": {
    "your_condition": "your_value"
  }
}

// Add error handling
"error_handling": {
  "retry_attempts": 3,
  "fallback_strategy": "log_and_continue"
}
```

#### **Environment-Specific Settings**
```json
// Use environment variables
"config": {
  "api_key": "{{env.YOUR_API_KEY}}",
  "endpoint": "{{env.API_ENDPOINT}}",
  "collection": "{{env.COLLECTION_NAME}}"
}
```

---

## 📋 **Template Testing**

### **Testing Checklist**
- [ ] All required inputs are available
- [ ] Configuration parameters are valid
- [ ] Error handling works properly
- [ ] Performance meets requirements
- [ ] Output format matches expectations

### **Test Commands**
```bash
# Validate workflow JSON
curl -X POST http://localhost:3001/api/workflows/validate \
  -H "Content-Type: application/json" \
  -d @your-workflow.json

# Test workflow execution
curl -X POST http://localhost:3001/api/workflows/test \
  -H "Content-Type: application/json" \
  -d @your-workflow.json

# Monitor workflow execution
curl http://localhost:3001/api/workflows/{workflow_id}/status
```

---

## 🔧 **Advanced Template Features**

### **Conditional Execution**
```json
{
  "id": "conditional_node",
  "type": "generic_system_processor",
  "config": {
    "strategy": "conditional_execution"
  },
  "conditions": {
    "execute_if": "{{previous_node.success}} && {{trigger.priority}} > 5"
  }
}
```

### **Parallel Processing**
```json
{
  "parallel_group": {
    "nodes": [
      {"id": "processor_1", "type": "generic_text_processor"},
      {"id": "processor_2", "type": "generic_document_processor"}
    ],
    "wait_for_all": true,
    "timeout": 300
  }
}
```

### **Loop Processing**
```json
{
  "id": "batch_processor",
  "type": "generic_text_processor",
  "config": {
    "strategy": "batch_processing",
    "batch_size": 10,
    "parallel_batches": 3
  },
  "loop": {
    "iterate_over": "{{input.items}}",
    "max_iterations": 1000
  }
}
```

---

## 📚 **Related Documentation**

- [Workflow Creation Guide](../PDK/WORKFLOW_CREATION_GUIDE.md) - Complete workflow development
- [Node Reference](../PDK/NODES_REFERENCE.md) - Available node types and configurations
- [Best Practices](BEST_PRACTICES.md) - Workflow design best practices
- [Examples Directory](EXAMPLES/) - Real-world workflow implementations

---

## 🆘 **Template Support**

For additional templates or customization help:
- Review [Workflow Examples](EXAMPLES/) for more complex patterns
- Check [Best Practices](BEST_PRACTICES.md) for design guidelines
- See [PDK Documentation](../PDK/README.md) for node capabilities

**Template Repository:** [Workflow Examples](EXAMPLES/)  
**Custom Development:** [Plugin Development Guide](../PDK/PLUGIN_DEVELOPMENT_GUIDE.md)