# PramaIA-Docs Index Update

Aggiornamento all'indice con i test guide.

## 📚 Documenti Disponibili

### 1. ECOSYSTEM_OVERVIEW.md
- Architettura ecosistema
- Stack tecnologico
- Configurazione e startup

### 2. EVENT_SOURCES_TRIGGERS_WORKFLOWS.md
- Sistema event-driven
- Trigger e workflow
- Operazioni comuni

### 3. DEVELOPMENT_GUIDE.md
- Creare nuovi nodi
- Creare nuovi event source
- Testing durante sviluppo

### 4. TEST_SUITE_GUIDE.md ⭐ NUOVO
- Guida rapida test suite
- Come eseguire i test
- Output e debugging

## 🧪 Test Suite - Struttura

```
tests/
├── Core Infrastructure
│   ├── __init__.py
│   ├── conftest.py (pytest fixtures)
│   ├── pytest.ini (configuration)
│   └── test_utils.py (shared utilities)
│
├── Test Suites
│   ├── test_inventory.py (what's in the system)
│   ├── test_crud_operations.py (create/read/update/delete)
│   └── test_e2e_pipeline.py (end-to-end flows)
│
├── Runners
│   ├── run_tests.py (Python runner)
│   └── run_tests.ps1 (PowerShell runner)
│
└── Documentation
    ├── requirements.txt
    └── TEST_SUITE_README.md (detailed docs)
```

## 🚀 Quick Commands

```bash
# Install dependencies
pip install -r tests/requirements.txt

# Run all tests
pytest tests/ -v -s

# Run specific suite
pytest tests/test_inventory.py -v -s
pytest tests/test_crud_operations.py -v -s
pytest tests/test_e2e_pipeline.py -v -s

# Using runners
python tests/run_tests.py inventory -v
.\tests\run_tests.ps1 -Suite crud -Verbose
```

## 📊 Test Coverage

### Inventory Tests
- Workflow count and details
- Node availability
- Event source configuration
- Trigger status
- Document count

### CRUD Tests
- Document create/read/update/delete
- Metadata management
- VectorStore operations
- Database statistics

### E2E Tests
- File monitoring pipeline
- Event processing
- Trigger execution
- Vectorstore integration
- Database synchronization
- Complete workflow: File → DB → VectorStore → Search

## 🔧 Test Utilities (test_utils.py)

### Classes Available
- `ServiceConfig` - Central configuration
- `ServiceHealthCheck` - Service availability
- `APIClient` - HTTP requests
- `DatabaseHelper` - Database operations
- `TestDataGenerator` - Test data creation
- `TestReporter` - Output formatting
- `Assertions` - Common assertions
- `TestSession` - Result tracking

### Example Usage
```python
from test_utils import APIClient, DatabaseHelper, TestReporter

# Check service
response = APIClient.get("http://127.0.0.1:8000/health")

# Query database
docs = DatabaseHelper.query_dict("SELECT * FROM documents LIMIT 10")

# Generate test data
data = TestDataGenerator.generate_document_data()

# Report result
TestReporter.print_result("Status", "✅")
```

## 📈 Running Tests with Options

```bash
# Verbose + Show output
pytest tests/ -vv -s

# Stop on first failure
pytest tests/ -x

# With coverage
pytest tests/ --cov=backend --cov-report=html

# With HTML report
pytest tests/ --html=report.html

# Only failed tests
pytest tests/ --lf
```

## 🎯 When to Use Each Test Suite

| Goal | Test Suite | Command |
|------|-----------|---------|
| See what's configured | inventory | `pytest tests/test_inventory.py` |
| Verify CRUD works | crud | `pytest tests/test_crud_operations.py` |
| Test full pipeline | e2e | `pytest tests/test_e2e_pipeline.py` |
| Everything | all | `pytest tests/` |

## 📍 File Locations

- **Tests**: `C:\PramaIA\tests\`
- **Docs**: `C:\PramaIA\PramaIA-Docs\`
- **Database**: `C:\PramaIA\PramaIAServer\backend\data\database.db`
- **VectorStore**: `C:\PramaIA\PramaIA-VectorstoreService\data\`

## 🔗 Related Documentation

- `PramaIA-Docs/ECOSYSTEM_OVERVIEW.md` - Architecture reference
- `PramaIA-Docs/EVENT_SOURCES_TRIGGERS_WORKFLOWS.md` - System flows
- `PramaIA-Docs/DEVELOPMENT_GUIDE.md` - Extending system
- `tests/TEST_SUITE_README.md` - Detailed test documentation

---

**Last Updated**: 18 Novembre 2025  
**Test Suite Version**: 1.0
