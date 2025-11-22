#!/usr/bin/env python3
"""
Script per configurare i trigger per il workflow di analisi dei metadati PDF.
Questo è un esempio di script che accompagna il tutorial nella documentazione.
"""

import json
import sqlite3
import os
import uuid
from datetime import datetime

def setup_metadata_triggers(db_path):
    """Configura i trigger per il workflow di analisi dei metadati PDF"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Definizione dei trigger da configurare
    trigger_mappings = [
        {
            "workflow_id": "pdf_metadata_analysis_pipeline",
            "source": "pdf-monitor-event-source",
            "event_type": "pdf_file_added",
            "name": "Trigger Analisi Metadati per Nuovi PDF",
            "description": "Trigger per analizzare i metadati dei nuovi documenti PDF",
            "conditions": json.dumps({
                "fileSize": {
                    "operator": "greaterThan",
                    "value": 0
                }
            }),
            "target_node_id": "pdf_input_node"
        },
        {
            "workflow_id": "pdf_metadata_analysis_pipeline",
            "source": "pdf-monitor-event-source",
            "event_type": "pdf_file_modified",
            "name": "Trigger Analisi Metadati per PDF Modificati",
            "description": "Trigger per analizzare i metadati dei documenti PDF modificati",
            "conditions": json.dumps({
                "fileSize": {
                    "operator": "greaterThan",
                    "value": 0
                }
            }),
            "target_node_id": "pdf_input_node"
        }
    ]
    
    triggers_created = 0
    triggers_updated = 0
    
    try:
        # Per ogni trigger nella configurazione
        for trigger_config in trigger_mappings:
            workflow_id = trigger_config["workflow_id"]
            source = trigger_config["source"]
            event_type = trigger_config["event_type"]
            
            # Verifica che il workflow esista
            cursor.execute("SELECT id FROM workflows WHERE workflow_id = ?", (workflow_id,))
            workflow = cursor.fetchone()
            
            if not workflow:
                print(f"⚠️ Workflow '{workflow_id}' non trovato nel database, salto configurazione trigger...")
                continue
            
            # Verifica se il trigger esiste già
            cursor.execute("""
                SELECT id FROM workflow_triggers 
                WHERE workflow_id = ? AND source = ? AND event_type = ?
            """, (workflow_id, source, event_type))
            existing_trigger = cursor.fetchone()
            
            # Prepara i dati per il trigger
            name = trigger_config.get("name", f"Trigger {event_type}")
            description = trigger_config.get("description", "Trigger automatico")
            conditions = trigger_config.get("conditions", "{}")
            target_node_id = trigger_config.get("target_node_id", "")
            
            # Genera un ID univoco per il trigger
            trigger_id = str(uuid.uuid4())
            
            if existing_trigger:
                # Aggiorna il trigger esistente
                cursor.execute("""
                    UPDATE workflow_triggers 
                    SET name = ?, conditions = ?, active = 1, updated_at = ?, target_node_id = ?
                    WHERE id = ?
                """, (
                    name, 
                    conditions,
                    datetime.now().isoformat(), 
                    target_node_id,
                    existing_trigger[0]
                ))
                triggers_updated += 1
                print(f"🔄 Aggiornato trigger per {workflow_id} → {event_type}")
            else:
                # Crea un nuovo trigger
                cursor.execute("""
                    INSERT INTO workflow_triggers 
                    (id, name, event_type, source, workflow_id, conditions, 
                     active, created_at, updated_at, target_node_id)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """, (
                    trigger_id,
                    name,
                    event_type,
                    source,
                    workflow_id,
                    conditions,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    target_node_id
                ))
                triggers_created += 1
                print(f"✨ Creato nuovo trigger ID:{trigger_id} per {workflow_id} → {event_type}")
        
        conn.commit()
        print(f"\n✅ Configurazione completata: {triggers_created} trigger creati, {triggers_updated} trigger aggiornati")
        
    except Exception as e:
        print(f"❌ Errore durante la configurazione dei trigger: {str(e)}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def main():
    """Funzione principale"""
    print("🚀 Configurazione dei trigger per il workflow di analisi dei metadati PDF...")
    
    # Path al database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'PramaIAServer', 'backend', 'data', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return
    
    print(f"📂 Database trovato: {db_path}")
    
    # Configura i trigger
    setup_metadata_triggers(db_path)
    
    print("\n✨ Configurazione completata! Il workflow è ora collegato agli event source.")
    print("📝 Nota: Questo è un esempio di script che accompagna il tutorial nella documentazione.")
    print("    Per utilizzarlo, è necessario prima importare il workflow pdf_metadata_analysis_pipeline.json")

if __name__ == "__main__":
    main()
