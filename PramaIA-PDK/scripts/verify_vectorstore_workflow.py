"""
Script per verificare se il workflow di interrogazione del vectorstore è stato importato correttamente.
"""

import os
import sys
import sqlite3
import json

def find_db_path():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.normpath(os.path.join(here, '..', 'PramaIAServer', 'backend', 'data', 'database.db')),
        os.path.normpath(os.path.join(here, '..', 'PramaIAServer', 'backend', 'db', 'database.db')),
        os.path.normpath(os.path.join(os.path.dirname(here), 'PramaIAServer', 'backend', 'data', 'database.db')),
        r'C:\PramaIA\PramaIAServer\backend\data\database.db'
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

DATABASE_PATH = find_db_path()

def verify_workflow_import():
    workflow_id = "query_vectorstore_workflow"
    if not DATABASE_PATH:
        print("ERRORE: Database non trovato.")
        return False
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,))
        workflow = cursor.fetchone()
        if not workflow:
            print(f"ERRORE: Il workflow '{workflow_id}' non è stato trovato nel database.")
            return False
        print(f"Workflow '{workflow_id}' trovato nel database.")
        cursor.execute("SELECT COUNT(*) FROM workflow_nodes WHERE workflow_id = ?", (workflow_id,))
        node_count = cursor.fetchone()[0]
        print(f"Numero di nodi: {node_count}")
        cursor.execute("SELECT COUNT(*) FROM workflow_connections WHERE workflow_id = ?", (workflow_id,))
        connection_count = cursor.fetchone()[0]
        print(f"Numero di connessioni: {connection_count}")
        cursor.execute("SELECT node_type, COUNT(*) FROM workflow_nodes WHERE workflow_id = ? GROUP BY node_type", (workflow_id,))
        node_types = cursor.fetchall()
        print("\nTipi di nodi:")
        for node_type, count in node_types:
            print(f"  - {node_type}: {count}")
        return True
    except Exception as e:
        print(f"ERRORE durante la verifica: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verify_workflow_import()
