"""
Test del logger per plugin Python del PDK con debug esteso.
"""

import sys
import os
import time

# Aggiungi il percorso dei plugin al PYTHONPATH
plugins_path = os.path.join(os.path.dirname(__file__), 'plugins')
sys.path.insert(0, plugins_path)

# Abilita debug per requests
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)

# Importa il logger comune
from common import logger

print("=== Test Logger Plugin Python PDK (Debug Mode) ===\n")

# Inizializza il logger per un plugin di test
print("--- Inizializzazione logger ---")
plugin_logger = logger.init(plugin_name="test-plugin-debug", module_name="test_module")
print(f"Logger type: {type(plugin_logger)}")
print(f"Logger methods: {[m for m in dir(plugin_logger) if not m.startswith('_')]}")

# Test singolo log INFO
print("\n--- Test log INFO ---")
try:
    result = logger.info("Test messaggio INFO dal plugin", details={
        "test_field": "test_value",
        "plugin_version": "1.0.0"
    })
    print(f"Result: {result}")
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()

# Aspetta un po' prima di flushare
print("\n--- Attesa 2 secondi ---")
time.sleep(2)

# Flush esplicito
print("\n--- Flush dei log ---")
try:
    logger.flush()
    print("✅ Flush completato")
except Exception as e:
    print(f"❌ Errore flush: {e}")
    import traceback
    traceback.print_exc()

# Altra attesa
print("\n--- Attesa 2 secondi ---")
time.sleep(2)

print("\n✅ Test completato.")
