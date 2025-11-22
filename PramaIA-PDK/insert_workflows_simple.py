"""
Script per importare i template di workflow nel database.
Versione semplificata con supporto base.
"""

import os
import json
import sqlite3
from datetime import datetime
import sys

# Percorso della directory dei workflow
WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows")

# Percorso del database PramaIA
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PramaIAServer", "backend", "db", "database.db")

def import_workflows():
    """Importa tutti i workflow dalla directory dei workflow nel database."""
    
    # Verifica che la directory dei workflow esista
    if not os.path.exists(WORKFLOWS_DIR):
        print(f"ERRORE: La directory dei workflow non esiste: {WORKFLOWS_DIR}")
        return False
    
    # Verifica che il database esista
    if not os.path.exists(DATABASE_PATH):
        print(f"ERRORE: Il database non esiste: {DATABASE_PATH}")
        return False
    
    # Ottieni tutti i file JSON nella directory dei workflow
    workflow_files = [f for f in os.listdir(WORKFLOWS_DIR) if f.endswith('.json')]
    
    if not workflow_files:
        print(f"ERRORE: Nessun file di workflow trovato in: {WORKFLOWS_DIR}")
        return False
    
    # Connessione al database
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Verifica se la tabella workflows esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflows'")
        if not cursor.fetchone():
            print("ERRORE: La tabella 'workflows' non esiste nel database.")
            return False
        
        # Importa ogni workflow
        imported_count = 0
        updated_count = 0
        
        for workflow_file in workflow_files:
            file_path = os.path.join(WORKFLOWS_DIR, workflow_file)
            
            try:
                # Carica il workflow dal file JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                
                # Estrai informazioni dal workflow
                workflow_id = workflow_data.get('workflow_id')
                if not workflow_id:
                    print(f"AVVISO: Il file {workflow_file} non contiene un workflow_id valido. Salto.")
                    continue
                
                name = workflow_data.get('name', '')
                description = workflow_data.get('description', '')
                is_active = workflow_data.get('is_active', True)
                is_public = workflow_data.get('is_public', True)
                category = workflow_data.get('category', '')
                tags = ','.join(workflow_data.get('tags', []))
                nodes = json.dumps(workflow_data.get('nodes', []))
                connections = json.dumps(workflow_data.get('connections', []))
                created_at = datetime.now().isoformat()
                updated_at = created_at
                
                # Verifica se il workflow esiste già
                cursor.execute("SELECT workflow_id FROM workflows WHERE workflow_id = ?", (workflow_id,))
                existing_workflow = cursor.fetchone()
                
                if existing_workflow:
                    # Aggiorna il workflow esistente
                    cursor.execute("""
                        UPDATE workflows
                        SET name = ?, description = ?, is_active = ?, is_public = ?,
                            category = ?, tags = ?, nodes = ?, connections = ?, updated_at = ?
                        WHERE workflow_id = ?
                    """, (name, description, is_active, is_public, category, tags, 
                          nodes, connections, updated_at, workflow_id))
                    updated_count += 1
                    print(f"Workflow aggiornato: {name} (ID: {workflow_id})")
                else:
                    # Inserisci il nuovo workflow
                    cursor.execute("""
                        INSERT INTO workflows (workflow_id, name, description, is_active, is_public,
                                             category, tags, nodes, connections, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (workflow_id, name, description, is_active, is_public, category, tags,
                          nodes, connections, created_at, updated_at))
                    imported_count += 1
                    print(f"Nuovo workflow importato: {name} (ID: {workflow_id})")
                
            except Exception as e:
                print(f"ERRORE durante l'importazione del workflow {workflow_file}: {str(e)}")
        
        # Salva le modifiche
        conn.commit()
        
        print(f"\nImportazione completata. {imported_count} nuovi workflow importati, {updated_count} workflow aggiornati.")
        return True
    
    except Exception as e:
        print(f"ERRORE durante l'importazione dei workflow: {str(e)}")
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = import_workflows()
    sys.exit(0 if success else 1)
