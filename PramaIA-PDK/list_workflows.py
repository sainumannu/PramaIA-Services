"""
Script per elencare i workflow presenti nel database di PramaIA.
Mostra anche i trigger associati a ciascun workflow.
"""

import os
import json
import sqlite3
import sys
import traceback
from datetime import datetime

# Percorso del database PramaIA
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PramaIAServer", "backend", "db", "database.db")

def debug_info():
    """Stampa informazioni di debug."""
    print("\n=== INFORMAZIONI DI DEBUG ===")
    print(f"Percorso corrente: {os.getcwd()}")
    print(f"Percorso database: {DATABASE_PATH}")
    print(f"Database esiste: {os.path.exists(DATABASE_PATH)}")
    
    if os.path.exists(DATABASE_PATH):
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tabelle nel database: {[t[0] for t in tables]}")
            conn.close()
        except Exception as e:
            print(f"Errore accesso database: {str(e)}")

def format_date(date_str):
    """Formatta una data ISO in un formato più leggibile."""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except:
        return date_str

def list_workflows():
    """Elenca tutti i workflow presenti nel database."""
    
    # Verifica che il database esista
    if not os.path.exists(DATABASE_PATH):
        print(f"ERRORE: Il database non esiste: {DATABASE_PATH}")
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
        
        # Ottieni le colonne effettive della tabella workflows
        cursor.execute("PRAGMA table_info(workflows)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Colonne nella tabella workflows: {columns}")
        
        # Costruisci una query che utilizza solo le colonne disponibili
        select_cols = []
        for col in ["workflow_id", "name", "is_active", "is_public", "category", "tags", "created_at", "updated_at"]:
            if col in columns:
                select_cols.append(col)
            else:
                print(f"Attenzione: La colonna '{col}' non esiste nella tabella workflows")
        
        # Aggiungi colonne di default per quelle mancanti
        has_description = "description" in columns
        
        # Costruisci la query
        query = f"SELECT {', '.join(select_cols)} FROM workflows ORDER BY "
        query += "updated_at DESC" if "updated_at" in columns else "created_at DESC" if "created_at" in columns else "workflow_id"
        
        # Recupera tutti i workflow
        cursor.execute(query)
        
        workflows = cursor.fetchall()
        
        if not workflows:
            print("Nessun workflow trovato nel database.")
            return True
        
        print(f"Trovati {len(workflows)} workflow nel database:\n")
        
        for workflow in workflows:
            # Crea un dizionario con i valori del workflow
            workflow_dict = {}
            for i, col in enumerate(select_cols):
                workflow_dict[col] = workflow[i]
            
            # Stampa le informazioni del workflow
            workflow_id = workflow_dict.get("workflow_id", "N/A")
            name = workflow_dict.get("name", "Senza nome")
            is_active = workflow_dict.get("is_active", 0)
            is_public = workflow_dict.get("is_public", 0)
            category = workflow_dict.get("category", "")
            tags = workflow_dict.get("tags", "")
            created_at = workflow_dict.get("created_at", "")
            updated_at = workflow_dict.get("updated_at", "")
            
            status = "✓ Attivo" if is_active else "✗ Inattivo"
            visibility = "Pubblico" if is_public else "Privato"
            
            print(f"{'=' * 80}")
            print(f"ID: {workflow_id}")
            print(f"Nome: {name} [{status}, {visibility}]")
            
            if has_description:
                description = workflow_dict.get("description", "")
                if description:
                    print(f"Descrizione: {description}")
            
            if category:
                print(f"Categoria: {category}")
            
            if tags:
                print(f"Tag: {tags}")
            
            try:
                if created_at:
                    print(f"Creato: {format_date(created_at)}")
                if updated_at:
                    print(f"Ultimo aggiornamento: {format_date(updated_at)}")
            except Exception as date_error:
                print(f"Data creazione: {created_at}")
                print(f"Data aggiornamento: {updated_at}")
                print(f"(Errore formattazione data: {str(date_error)})")
            
            # Verifica se la tabella workflow_triggers esiste
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_triggers'")
            if cursor.fetchone():
                # Recupera i trigger associati a questo workflow
                try:
                    cursor.execute("""
                        SELECT source, event_type, name, conditions, target_node_id
                        FROM workflow_triggers
                        WHERE workflow_id = ?
                    """, (workflow_id,))
                    
                    triggers = cursor.fetchall()
                    
                    if triggers:
                        print("\nTrigger associati:")
                        for i, trigger in enumerate(triggers, 1):
                            source, event_type, trigger_name, conditions, target_node_id = trigger
                            print(f"  {i}. {trigger_name} [{source} / {event_type}]")
                            print(f"     Target: {target_node_id}")
                            
                            if conditions:
                                try:
                                    cond_json = json.loads(conditions)
                                    print(f"     Condizioni: {json.dumps(cond_json, indent=2)}")
                                except:
                                    print(f"     Condizioni: {conditions}")
                    else:
                        print("\nNessun trigger associato a questo workflow.")
                except Exception as trigger_error:
                    print(f"\nErrore nel recupero dei trigger: {str(trigger_error)}")
            else:
                print("\nLa tabella workflow_triggers non esiste nel database.")
            
            print()
        
        return True
    
    except Exception as e:
        print(f"ERRORE durante l'elenco dei workflow: {str(e)}")
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        success = list_workflows()
        debug_info()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Errore critico durante l'esecuzione: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        debug_info()
        sys.exit(1)
