"""Test per verificare quale versione di pramaialog viene caricata."""

import sys
import os

# Aggiungi il percorso dei plugin al PYTHONPATH
plugins_path = os.path.join(os.path.dirname(__file__), 'plugins')
sys.path.insert(0, plugins_path)

print("=== Debug Import pramaialog ===\n")

# Forza il reload del modulo
if 'pramaialog' in sys.modules:
    print(f"❌ pramaialog già in cache: {sys.modules['pramaialog']}")
    del sys.modules['pramaialog']
    print("✅ Rimosso dalla cache")

# Importa direttamente
try:
    from common import pramaialog
    print(f"\n✅ Importato da: {pramaialog.__file__}")
    print(f"\nMetodi disponibili:")
    methods = [m for m in dir(pramaialog.PramaIALogger) if not m.startswith('_')]
    for method in methods:
        print(f"  - {method}")
    
    # Verifica se lifecycle esiste
    if hasattr(pramaialog.PramaIALogger, 'lifecycle'):
        print(f"\n✅ Metodo 'lifecycle' PRESENTE")
    else:
        print(f"\n❌ Metodo 'lifecycle' ASSENTE")
        
except Exception as e:
    print(f"❌ Errore import: {e}")
    import traceback
    traceback.print_exc()
