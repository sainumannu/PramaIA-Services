"""
Script per pulire il database degli hash
"""
import os
import sys

# Aggiungi la directory src al percorso per poter importare i moduli
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, "src")
sys.path.append(script_dir)

# Importa il modulo FileHashTracker
from src.file_hash_tracker import FileHashTracker

def main():
    """Pulisce il database degli hash"""
    print("Pulizia del database degli hash...")
    
    # Esegue la pulizia utilizzando il metodo statico della classe
    success = FileHashTracker.clean_database()
    
    if success:
        print("Database degli hash pulito con successo.")
    else:
        print("Errore durante la pulizia del database degli hash.")
        
if __name__ == "__main__":
    main()