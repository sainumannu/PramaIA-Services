# Testing Documentation

**PramaIA Testing Framework - Quality Assurance**

Comprehensive testing strategies for all PramaIA components including services, plugins, workflows, and integrations.

---

## 🎯 **Testing Philosophy**

The PramaIA testing approach emphasizes:
- **Component Testing** - Individual service and plugin validation
- **Integration Testing** - Cross-service workflow verification
- **End-to-End Testing** - Complete user scenario validation
- **Performance Testing** - Load and reliability assessment

---

## 📖 **Testing Documentation Index**

### **Core Testing Guides**
- **[Test Suite Guide](TEST_SUITE_GUIDE.md)** - Complete testing framework overview
- **[Test Suite Index](TEST_SUITE_INDEX.md)** - Available test collections
- **[Integration Tests](INTEGRATION_TESTS.md)** - Cross-service testing

### **Specialized Testing**
- **[Upload/Retrieve Testing](../TEST_UPLOAD_RETRIEVE.md)** - Document processing workflows
- **[Vector Store Testing](../VECTORSTORE_QUERY_ANALYSIS.md)** - Vector database operations

---

## 🏗️ **Testing Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Unit Tests    │    │Integration Tests│    │  E2E Tests      │
│  (Components)   │    │  (Services)     │    │ (Full Flows)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Jest/PyTest     │    │ API Testing     │    │ Workflow Tests  │
│ Node Testing    │    │ Service Calls   │    │ User Scenarios  │
│ Plugin Testing  │    │ Data Flows      │    │ Performance     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🚀 **Quick Start Testing**

### **1. Run All Tests**
```bash
# Complete test suite
.\test_vectorstore_completo.ps1

# Quick validation tests  
.\quick_test.ps1

# Upload/retrieve workflow
.\test_upload_retrieve.ps1
```

### **2. Service-Specific Tests**
```bash
# VectorStore service tests
python test_generic_vector_store_processor.py

# Embedding tests
python test_embedding_creation.py

# Similarity testing
python test_similarity_debug.py
```

### **3. Integration Tests**
```bash
# Post-reset validation
python test_post_reset_complete.py

# End-to-end workflows
.\test_endpoints.sh
```

---

## 🧪 **Test Categories**

### **Unit Tests**
**Purpose:** Test individual components in isolation

**Coverage:**
- **Generic Processors** - All 5 universal processors
- **Plugin Nodes** - Individual plugin functionality  
- **Service APIs** - Endpoint validation
- **Utility Functions** - Helper and utility code

**Example:**
```python
# Test generic text processor
def test_text_chunking():
    processor = GenericTextProcessor({
        "strategy": "fixed_size",
        "chunk_size": 1000,
        "overlap": 200
    })
    
    chunks = processor.process("long text content...")
    assert len(chunks) > 0
    assert all(len(chunk) <= 1000 for chunk in chunks)
```

### **Integration Tests**
**Purpose:** Test service interactions and data flows

**Coverage:**
- **Service Communication** - API calls between services
- **Data Consistency** - Cross-service data validation
- **Workflow Execution** - Multi-step process testing
- **Error Handling** - Failure recovery testing

**Example:**
```python
# Test document upload → processing → retrieval
def test_document_pipeline():
    # Upload document
    upload_result = upload_document("test.pdf")
    
    # Wait for processing
    wait_for_processing(upload_result.id)
    
    # Test retrieval
    search_result = search_documents("test query")
    assert len(search_result.results) > 0
```

### **End-to-End Tests**
**Purpose:** Test complete user workflows

**Coverage:**
- **Document Processing** - Full document ingestion pipeline
- **RAG Workflows** - Query → retrieval → generation → response
- **System Administration** - Maintenance and monitoring
- **User Scenarios** - Real-world usage patterns

**Example:**
```powershell
# Complete upload/retrieve test
.\test_upload_retrieve.ps1
# - Uploads test documents
# - Waits for processing  
# - Performs similarity searches
# - Validates response quality
```

---

## 📋 **Available Test Suites**

### **Core Test Scripts**
| Script | Purpose | Runtime | Coverage |
|--------|---------|---------|----------|
| `test_vectorstore_completo.ps1` | Complete vectorstore validation | 5-10 min | Full VectorStore |
| `test_upload_retrieve.ps1` | Document pipeline testing | 3-5 min | Upload/Retrieval |
| `quick_test.ps1` | Fast validation checks | 1-2 min | Critical paths |
| `test_post_reset_complete.py` | Post-deployment validation | 2-3 min | System health |

### **Component Tests**
| Script | Component | Focus |
|--------|-----------|-------|
| `test_generic_vector_store_processor.py` | VectorStore Processor | Generic node testing |
| `test_embedding_creation.py` | Embedding Service | Vector generation |
| `test_similarity_debug.py` | Similarity Engine | Search accuracy |
| `debug_chromadb_content.py` | ChromaDB | Database content |

### **Service Tests**
| Service | Test Location | Key Tests |
|---------|---------------|-----------|
| VectorStore | `PramaIA-VectorstoreService/tests/` | API, storage, retrieval |
| Log Service | `PramaIA-LogService/tests/` | Logging, filtering, queries |
| PDK Server | `PramaIA-PDK/tests/` | Plugin loading, workflows |

---

## 🎯 **Test Configuration**

### **Environment Setup**
```bash
# Ensure all services are running
.\start-all.ps1

# Verify service health
curl http://localhost:3001/health  # PDK
curl http://localhost:3002/health  # VectorStore  
curl http://localhost:3003/health  # Log Service
```

### **Test Data**
- **Sample Documents** - PDF, DOCX, TXT files for processing tests
- **Test Queries** - Known queries with expected results
- **Mock APIs** - Simulated external service responses  
- **Performance Data** - Baseline metrics for comparison

### **Test Environment Variables**
```bash
TEST_VECTORSTORE_URL=http://localhost:3002
TEST_PDK_URL=http://localhost:3001
TEST_TIMEOUT=30000
TEST_LOG_LEVEL=INFO
```

---

## 📊 **Test Reporting**

### **Test Results**
Tests generate reports in:
- **Console Output** - Real-time test progress
- **Log Files** - Detailed execution logs
- **JSON Reports** - Structured test results
- **Coverage Reports** - Code coverage metrics

### **Performance Metrics**
Key metrics tracked:
- **Response Times** - API endpoint performance  
- **Throughput** - Documents processed per minute
- **Resource Usage** - Memory and CPU consumption
- **Error Rates** - Failure frequency and types

### **Quality Gates**
Tests must pass:
- **Code Coverage** - Minimum 80% coverage
- **Performance** - Response times under SLA
- **Reliability** - Error rate below 1%
- **Security** - No security vulnerabilities

---

## 🔧 **Debugging Tests**

### **Common Test Failures**
- **Service Not Running** - Check `.\start-all.ps1` execution
- **Port Conflicts** - Verify no other services on ports 3001-3004
- **Data Dependencies** - Ensure test data is available
- **Network Issues** - Check localhost connectivity

### **Debug Tools**
```bash
# Check service status
netstat -an | findstr :300

# Validate configurations
python debug_chromadb_content.py

# Test specific endpoints
curl -v http://localhost:3002/api/vectorstore/health
```

---

## 🔗 **Related Documentation**

- [Development Guide](../DEVELOPMENT_GUIDE.md) - Development environment setup
- [Services Documentation](../SERVICES/README.md) - Service-specific testing  
- [PDK Testing](../PDK/README.md) - Plugin and workflow testing
- [Implementation Status](../IMPLEMENTATION/IMPLEMENTATION_STATUS.md) - Feature testing status

---

## 🆘 **Testing Support**

### **CI/CD Integration**
- **GitHub Actions** - Automated testing on commits
- **Pre-commit Hooks** - Local validation before commits
- **Deployment Testing** - Post-deployment validation
- **Performance Monitoring** - Continuous performance tracking

### **Getting Help**
- **Test Failures** - Check logs in service directories
- **Performance Issues** - Review resource usage and optimization guides  
- **Integration Problems** - Verify service configurations and dependencies
- **Custom Tests** - See [Development Guide](../DEVELOPMENT_GUIDE.md) for test creation

**Test Dashboard:** `http://localhost:3001/test-dashboard`  
**Service Health:** `http://localhost:3001/health`