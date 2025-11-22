# TEST SUITE GUIDE

Guida rapida alla test suite di PramaIA - Batteria di test per validazione e debug.

## 📍 Ubicazione

```
tests/
├── __init__.py                    # Package marker
├── conftest.py                    # pytest configuration e fixtures
├── pytest.ini                     # pytest settings
├── requirements.txt               # dipendenze test
├── test_utils.py                  # Utility condivise
├── test_inventory.py              # Inventario sistema
├── test_crud_operations.py        # Operazioni CRUD
├── test_e2e_pipeline.py          # Test end-to-end
├── run_tests.py                   # Test runner (Python)
├── run_tests.ps1                  # Test runner (PowerShell)
└── TEST_SUITE_README.md           # Documentazione completa
```

## 🚀 Quick Start

### 1. Installare Dipendenze
```bash
cd tests
pip install -r requirements.txt
```

### 2. Eseguire Test
```bash
# Tutti i test
pytest tests/ -v -s

# Inventory (cosa c'è nel sistema)
pytest tests/test_inventory.py -v -s

# CRUD (creare/leggere/aggiornare/eliminare)
pytest tests/test_crud_operations.py -v -s

# End-to-End (flusso completo)
pytest tests/test_e2e_pipeline.py -v -s
```

### 3. Con Script Runner
```bash
# Python
python tests/run_tests.py inventory -v -s

# PowerShell
.\tests\run_tests.ps1 -Suite crud -Verbose -ShowOutput
```

## 📊 Cosa Testano

### test_inventory.py - ✅ Inventario Sistema
Verifica quanti e quali componenti sono disponibili:
- ✅ Workflow configurati
- ✅ Nodi PDK disponibili
- ✅ Event source registrati
- ✅ Trigger configurati
- ✅ Documenti nel sistema

**Output**: Tabelle con lista completa componenti

### test_crud_operations.py - 📝 Operazioni CRUD
Testa operazioni di creazione, lettura, aggiornamento, eliminazione:
- ✅ Creare documento
- ✅ Leggere metadati
- ✅ Aggiornare metadata
- ✅ Eliminare documenti
- ✅ Operazioni VectorStore
- ✅ Integrità database

**Output**: Verifiche che CRUD funziona correttamente

### test_e2e_pipeline.py - 🔄 End-to-End
Testa il flusso completo da file a search:
- ✅ Monitoraggio folder
- ✅ Processamento eventi
- ✅ Esecuzione trigger/workflow
- ✅ Embedding documento
- ✅ Ricerca semantica
- ✅ Sincronizzazione DB-VectorStore

**Output**: Verifica che il flusso completo funziona

## 🔧 Configurazione

### Variabili d'Ambiente
```bash
# Backend
BACKEND_URL=http://127.0.0.1:8000
DATABASE_URL=sqlite:///./PramaIAServer/backend/data/database.db

# PDK Server
PDK_SERVER_BASE_URL=http://127.0.0.1:3001

# VectorStore
VECTORSTORE_SERVICE_URL=http://127.0.0.1:8090

# Monitor Agent
MONITOR_AGENT_URL=http://127.0.0.1:8001

# LogService
PRAMAIALOG_URL=http://127.0.0.1:8081
```

## 📈 Utility e Helper

### Nella suite
- `ServiceHealthCheck.check_all()` - Verifica tutti i servizi
- `APIClient.get/post/put/delete()` - HTTP request
- `DatabaseHelper.query/execute()` - Query database
- `TestDataGenerator.generate_*()` - Crea dati test
- `TestReporter.print_*()` - Formatta output

## 🐛 Debugging

### Se fallisce un test
1. Verificare servizi: `pytest tests/test_inventory.py::TestWorkflowInventory::test_get_workflows_from_api -v`
2. Controllare logs: porta 8081
3. Verificare database: `sqlite3 database.db "SELECT COUNT(*) FROM workflows"`

### Comandi Utili
```bash
# Solo test falliti precedentemente
pytest tests/ --lf

# Stop al primo fallimento
pytest tests/ -x

# Verbose error
pytest tests/ --tb=long

# Specifico test
pytest tests/test_inventory.py::TestWorkflowInventory -v
```

## 📝 Aggiungere Nuovi Test

### Template
```python
from test_utils import APIClient, DatabaseHelper, TestReporter

class TestNewFeature:
    def test_my_feature(self):
        TestReporter.print_header("MY FEATURE TEST")
        
        # Test code
        response = APIClient.get("http://127.0.0.1:8000/api/endpoint")
        assert response.status_code == 200
        
        TestReporter.print_result("Result", "✅")
```

## 📊 Output Formato

I test producono output formattato:
```
================================================================================
  TEST NAME
================================================================================

✅ Result: value
📋 Data:
  - Item 1
  - Item 2

📊 Statistics:
Workflow | Active | Created
---------|--------|--------
wf1      | True   | 2025-11-18
```

## 🎯 Best Practices

1. **Eseguire dopo deployment**: `pytest tests/ -v`
2. **Eseguire prima di merge**: `pytest tests/ -x`
3. **Conservare report**: `pytest tests/ --html=report.html`
4. **Aggiornare quando cambiano API**: Mantenere test sincronizzati

## ⚙️ Configurazione Test

File: `pytest.ini`
```ini
[pytest]
addopts = -v -s
timeout = 300
markers = 
    inventory: Inventario test
    crud: CRUD test
    e2e: End-to-end test
```

## 🔄 Continuous Integration

Test suite è progettata per CI/CD:

```yaml
# GitHub Actions example
- name: Run Tests
  run: pytest tests/ -v --html=report.html

- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: test-report
    path: report.html
```

## 📚 Fixture Disponibili

In conftest.py:
- `check_services`: Verifica servizi all'inizio
- `test_data`: Generator di dati test
- `test_session`: Tracking risultati

## 🚨 Stato Atteso

| Scenario | Comportamento | Soluzione |
|----------|---------------|-----------|
| Servizi offline | Test skipped | Avviare servizi |
| Database vuoto | Test passa (dati generati) | Normale |
| VectorStore offline | Fallback a database | Avviare vectorstore |
| Trigger non eseguito | Test falisce | Verificare config trigger |

---

**Vedi**: `tests/TEST_SUITE_README.md` per documentazione completa  
**Aggiornato**: 18 Novembre 2025
