"""
Script per importare il workflow di interrogazione del vectorstore nel sistema PDK.
"""

# (Vedi versione aggiornata, già funzionante)

import json
import os
import sys
import sqlite3
from datetime import datetime
import traceback

WORKFLOW_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workflows", "query_vectorstore_workflow.json")

def find_db_path():
    # Forza il path del database corretto
    db_path = r"c:\PramaIA\PramaIAServer\backend\db\database.db"
    if os.path.exists(db_path):
        return db_path
    return None

DATABASE_PATH = find_db_path()

def import_workflow():
    print(f"Importazione del workflow da: {WORKFLOW_PATH}")
    if not os.path.exists(WORKFLOW_PATH):
        print(f"ERRORE: Il file del workflow non esiste: {WORKFLOW_PATH}")
        return False
    if not DATABASE_PATH or not os.path.exists(DATABASE_PATH):
        print(f"ERRORE: Database non trovato. Percorso: {DATABASE_PATH}")
        return False
    conn = None
    try:
        with open(WORKFLOW_PATH, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        workflow_id = workflow_data.get('workflow_id')
        name = workflow_data.get('name')
        description = workflow_data.get('description', '')
        is_active = workflow_data.get('is_active', True)
        is_public = workflow_data.get('is_public', True)
        category = workflow_data.get('category', '')
        tags = json.dumps(workflow_data.get('tags', []))
        created_at = datetime.now().isoformat()
        updated_at = created_at
        created_by = "admin"
        cursor.execute("SELECT id FROM workflows WHERE workflow_id = ?", (workflow_id,))
        existing_workflow = cursor.fetchone()
        if existing_workflow:
            workflow_db_id = existing_workflow[0]
            print(f"Il workflow '{name}' (ID: {workflow_id}) esiste già. Aggiornamento in corso...")
            cursor.execute("""
                UPDATE workflows
                SET name = ?, description = ?, is_active = ?, is_public = ?,
                    category = ?, tags = ?, updated_at = ?
                WHERE id = ?
            """, (name, description, is_active, is_public, category, tags, updated_at, workflow_db_id))
        else:
            print(f"Inserimento del nuovo workflow '{name}' (ID: {workflow_id})...")
            cursor.execute("""
                INSERT INTO workflows (
                    workflow_id, name, description, created_by, created_at, updated_at,
                    is_active, is_public, tags, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (workflow_id, name, description, created_by, created_at, updated_at,
                  is_active, is_public, tags, category))
            cursor.execute("SELECT id FROM workflows WHERE workflow_id = ?", (workflow_id,))
            workflow_db_id = cursor.fetchone()[0]
        cursor.execute("DELETE FROM workflow_nodes WHERE workflow_id = ?", (workflow_id,))
        cursor.execute("DELETE FROM workflow_connections WHERE workflow_id = ?", (workflow_id,))
        for node in workflow_data.get('nodes', []):
            node_id = node.get('node_id')
            node_type = node.get('node_type')
            node_name = node.get('name')
            node_description = node.get('description', '')
            config = json.dumps(node.get('config', {}))
            position = json.dumps(node.get('position', {}))
            width = node.get('width', 200)
            height = node.get('height', 100)
            cursor.execute("""
                INSERT INTO workflow_nodes (
                    node_id, workflow_id, node_type, name, description,
                    config, position, width, height, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (node_id, workflow_id, node_type, node_name, node_description,
                  config, position, width, height, created_at))
        for connection in workflow_data.get('connections', []):
            from_node_id = connection.get('from_node_id')
            to_node_id = connection.get('to_node_id')
            from_port = connection.get('from_port')
            to_port = connection.get('to_port')
            cursor.execute("""
                INSERT INTO workflow_connections (
                    workflow_id, from_node_id, to_node_id, from_port, to_port, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (workflow_id, from_node_id, to_node_id, from_port, to_port, created_at))
        conn.commit()
        print(f"Workflow '{name}' importato con successo!")
        return True
    except Exception as e:
        print(f"ERRORE durante l'importazione del workflow: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        if conn:
            try:
                conn.rollback()
            except:
                pass
        return False
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

if __name__ == "__main__":
    success = import_workflow()
    sys.exit(0 if success else 1)
