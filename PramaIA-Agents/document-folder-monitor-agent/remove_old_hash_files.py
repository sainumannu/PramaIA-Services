"""
Script per eliminare tutti i file hash.db obsoleti
"""
import os
import shutil
from pathlib import Path

def remove_old_hash_files():
    """Elimina tutti i file hash.db obsoleti"""
    # Percorsi da controllare
    search_paths = [
        "PramaIA-Agents/document-folder-monitor-agent/src/file_hashes.db",
        "PramaIA-LogService/file_hashes.db",
        "file_hashes.db"  # Nel caso ci sia anche nella root
    ]
    
    # Il nuovo percorso corretto che NON dovrebbe essere eliminato
    correct_path = os.path.abspath("PramaIA-Agents/document-folder-monitor-agent/data/file_hashes.db")
    
    print("Eliminazione dei vecchi file di database hash obsoleti...")
    print(f"Il database corretto è: {correct_path}")
    print("=" * 60)
    
    files_removed = []
    
    # Cerca anche tutti i file_hashes.db nel sistema
    base_path = "."
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file == "file_hashes.db":
                full_path = os.path.join(root, file)
                abs_path = os.path.abspath(full_path)
                # Aggiungi solo se non è il percorso corretto
                if abs_path != correct_path and abs_path not in [os.path.abspath(p) for p in search_paths]:
                    search_paths.append(full_path)
    
    # Rimuovi i file obsoleti
    for path in search_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(path) and abs_path != correct_path:
            try:
                # Crea una copia di backup prima di eliminare
                backup_path = f"{path}.backup_{int(os.path.getmtime(path))}"
                print(f"Creazione backup di {path} in {backup_path}")
                shutil.copy2(path, backup_path)
                
                # Elimina il file
                os.remove(path)
                print(f"✅ Eliminato file obsoleto: {path}")
                files_removed.append(path)
            except Exception as e:
                print(f"❌ Errore durante l'eliminazione di {path}: {e}")
    
    # Riepilogo
    if files_removed:
        print("\nFile eliminati:")
        for file in files_removed:
            print(f"  - {file}")
        print(f"\nTotale: {len(files_removed)} file eliminati")
    else:
        print("\nNessun file hash obsoleto trovato da eliminare.")
    
    # Assicurati che la directory per il nuovo file esista
    correct_dir = os.path.dirname(correct_path)
    if not os.path.exists(correct_dir):
        print(f"\nCreazione directory per il nuovo database: {correct_dir}")
        os.makedirs(correct_dir, exist_ok=True)

if __name__ == "__main__":
    remove_old_hash_files()