#!/usr/bin/env python3
"""
Script per configurare i trigger degli eventi Document Monitor.

Questo script collega automaticamente i workflow di monitoraggio documenti
agli event source appropriati, creando i trigger necessari nel database.
"""

import json
import sqlite3
import os
import uuid
from datetime import datetime

def setup_event_triggers(db_path):
    """Configura i trigger degli eventi per i workflow di monitoraggio documenti"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Definizione dei trigger da configurare con mappatura ai workflow esistenti
    trigger_mappings = [
        {
            "workflow_id": "document_ingest_optimized_pipeline",  # Workflow esistente per importazione documenti
            "source": "document-monitor-event-source",
            "event_type": "document_file_modified",
            "name": "Trigger documenti modificati",
            "description": "Trigger per aggiornamento documenti modificati",
            "conditions": json.dumps({
                "fileSize": {
                    "operator": "greaterThan",
                    "value": 0
                }
            }),
            "target_node_id": "document_input_node"  # Nodo di input del workflow esistente
        },
        {
            "workflow_id": "document_ingest_optimized_pipeline",  # Riutilizziamo lo stesso workflow
            "source": "document-monitor-event-source",
            "event_type": "document_file_deleted",
            "name": "Trigger documenti eliminati",
            "description": "Trigger per pulizia documenti eliminati",
            "conditions": json.dumps({}),
            "target_node_id": "document_input_node"
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

def check_event_sources(db_path):
    """Verifica i trigger configurati nel database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica se ci sono trigger per eventi di documenti
        cursor.execute("""
            SELECT id, name, event_type, source, workflow_id, active 
            FROM workflow_triggers
            WHERE source LIKE 'document%'
        """)
        
        document_triggers = cursor.fetchall()
        
        if document_triggers:
            print(f"✅ Trovati {len(document_triggers)} trigger per eventi documento:")
            for trigger in document_triggers:
                trigger_id, name, event_type, source, workflow_id, active = trigger
                status = "ATTIVO" if active else "INATTIVO"
                print(f"  • {trigger_id}: {name} ({event_type} da {source}) → {workflow_id} - Stato: {status}")
        else:
            print("⚠️ Nessun trigger per eventi documento trovato!")
        
        # Verifica se ci sono record di eventi documento nella tabella document_monitor_events
        try:
            cursor.execute("SELECT COUNT(*) FROM document_monitor_events")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"\n✅ Trovati {count} record nella tabella document_monitor_events")
                
                # Mostra gli ultimi 3 eventi
                cursor.execute("""
                    SELECT id, timestamp, file_name, event_type, status, document_id
                    FROM document_monitor_events
                    ORDER BY timestamp DESC
                    LIMIT 3
                """)
                
                events = cursor.fetchall()
                print("  Ultimi eventi:")
                for event in events:
                    event_id, timestamp, file_name, event_type, status, document_id = event
                    print(f"  • ID:{event_id} - {timestamp} - {event_type} - {file_name} ({status})")
            else:
                print("\n⚠️ Nessun evento documento registrato nella tabella document_monitor_events")
        except sqlite3.OperationalError:
            print("\n⚠️ Tabella document_monitor_events non trovata o non accessibile")
        
    except Exception as e:
        print(f"❌ Errore durante la verifica dei trigger: {str(e)}")
    finally:
        conn.close()

def main():
    """Funzione principale"""
    print("🚀 Configurazione dei trigger per gli event source Document Monitor...")
    
    # Path al database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'PramaIAServer', 'backend', 'data', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database non trovato: {db_path}")
        return
    
    print(f"📂 Database trovato: {db_path}")
    
    # Verifica gli event source
    print("\n📡 Verifica event source...")
    check_event_sources(db_path)
    
    # Configura i trigger
    print("\n⚙️ Configurazione trigger degli eventi...")
    setup_event_triggers(db_path)
    
    print("\n✨ Configurazione completata! I workflow sono ora collegati agli event source.")
    print("📝 Nota: Per testare il sistema, aggiungi o modifica documenti nelle cartelle monitorate.")

if __name__ == "__main__":
    main()
