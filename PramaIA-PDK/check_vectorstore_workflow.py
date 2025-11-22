"""
Script per verificare la presenza del workflow di interrogazione del vectorstore nel database PDK.
"""

import os
import sqlite3
import json

# Definisci il percorso del database PDK
PDK_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server", "pdk.db")

def check_workflow():
    """Verifica la presenza del workflow nel database PDK."""
    workflow_id = "query_vectorstore_workflow"
    conn = None
    
    # Verifica che il database esista
    if not os.path.exists(PDK_DB_PATH):
        print(f"ERRORE: Il database PDK non esiste: {PDK_DB_PATH}")
        return False
    
    try:
        # Connessione al database
        conn = sqlite3.connect(PDK_DB_PATH)
        cursor = conn.cursor()
        
        # Verifica se il workflow esiste
        cursor.execute("SELECT workflow_id, name, description, is_active, is_public FROM workflows WHERE workflow_id = ?", (workflow_id,))
        workflow = cursor.fetchone()
        
        if workflow:
            print(f"Il workflow '{workflow[1]}' (ID: {workflow[0]}) è presente nel database.")
            print(f"Descrizione: {workflow[2]}")
            print(f"Attivo: {'Sì' if workflow[3] else 'No'}")
            print(f"Pubblico: {'Sì' if workflow[4] else 'No'}")
            
            # Ottieni i nodi e le connessioni
            cursor.execute("SELECT nodes, connections FROM workflows WHERE workflow_id = ?", (workflow_id,))
            nodes_connections = cursor.fetchone()
            
            if nodes_connections:
                nodes = json.loads(nodes_connections[0])
                connections = json.loads(nodes_connections[1])
                
                print(f"\nIl workflow contiene {len(nodes)} nodi e {len(connections)} connessioni.")
                print("\nTipi di nodo presenti:")
                node_types = {}
                for node in nodes:
                    node_type = node.get('node_type', 'Sconosciuto')
                    node_types[node_type] = node_types.get(node_type, 0) + 1
                
                for node_type, count in node_types.items():
                    print(f"- {node_type}: {count}")
            
            return True
        else:
            print(f"Il workflow con ID '{workflow_id}' non è presente nel database.")
            
            # Elenca i workflow disponibili
            cursor.execute("SELECT workflow_id, name FROM workflows")
            workflows = cursor.fetchall()
            
            if workflows:
                print("\nWorkflow disponibili nel database:")
                for wf in workflows:
                    print(f"- {wf[0]}: {wf[1]}")
            else:
                print("Non ci sono workflow nel database.")
                
            return False
    
    except Exception as e:
        print(f"ERRORE durante la verifica del workflow: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    check_workflow()
