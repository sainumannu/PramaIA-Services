"""
Test del logger per plugin Python del PDK.
Questo script testa che i plugin possano inviare log al LogService.
"""

import sys
import os

# Aggiungi il percorso dei plugin al PYTHONPATH
plugins_path = os.path.join(os.path.dirname(__file__), 'plugins')
sys.path.insert(0, plugins_path)

# Importa il logger comune
from common import logger

print("=== Test Logger Plugin Python PDK ===\n")

# Inizializza il logger per un plugin di test
print("--- Inizializzazione logger per plugin di test ---")
logger.init(plugin_name="test-plugin", module_name="test_module")

# Test log di diversi livelli
print("\n--- Test log standard ---")
logger.info("Test messaggio INFO dal plugin", details={
    "test_field": "test_value",
    "plugin_version": "1.0.0"
})

logger.warning("Test messaggio WARNING dal plugin", details={
    "warning_type": "test_warning"
})

logger.error("Test messaggio ERROR dal plugin", details={
    "error_code": "TEST001",
    "error_message": "Questo è un errore di test"
})

logger.debug("Test messaggio DEBUG dal plugin", details={
    "debug_info": "informazioni di debug dettagliate"
})

# Test log LIFECYCLE
print("\n--- Test log LIFECYCLE ---")
logger.lifecycle(
    "Documento elaborato dal plugin",
    details={
        "document_id": "test-doc-plugin-001",
        "file_name": "test-document.pdf",
        "file_hash": "plugin_hash_123456",
        "processing_result": "success",
        "lifecycle_event": "PLUGIN_PROCESSED"
    },
    context={
        "plugin_name": "test-plugin",
        "module_name": "test_module",
        "processing_time_ms": 1500
    }
)

logger.lifecycle(
    "File inviato a sistema esterno",
    details={
        "document_id": "test-doc-plugin-002",
        "file_name": "output.pdf",
        "destination": "external-system",
        "lifecycle_event": "TRANSMITTED"
    },
    context={
        "plugin_name": "test-plugin",
        "target_url": "http://example.com/api"
    }
)

print("\n--- Flush dei log ---")
logger.flush()

print("\n✅ Test completati. Verifica sul LogService dashboard se i log sono arrivati.")
print("   Dashboard: http://localhost:8081/dashboard")
print("   Filtra per progetto: PramaIA-PDK")
print("   Cerca modulo: plugin.test-plugin")
