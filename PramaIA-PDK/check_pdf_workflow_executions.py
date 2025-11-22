#!/usr/bin/env python3
"""
Script per verificare le esecuzioni del workflow PDF
"""

import sqlite3
import os
from datetime import datetime

# Percorso al database
db_path = os.path.join("..", "PramaIAServer", "backend", "db", "database.db")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("VERIFICA ESECUZIONI WORKFLOW PDF")
    print("=" * 50)
    
    # Controlla esecuzioni recenti del workflow PDF
    cursor.execute('''
        SELECT execution_id, status, started_at, completed_at, error_message 
        FROM workflow_executions 
        WHERE workflow_id = ? 
        ORDER BY started_at DESC 
        LIMIT 10
    ''', ('pdf_document_add_workflow',))
    
    executions = cursor.fetchall()
    
    if executions:
        print(f"Trovate {len(executions)} esecuzioni del workflow PDF:")
        print()
        for i, exec in enumerate(executions):
            exec_id, status, started, completed, error = exec
            print(f"{i+1}. ID: {exec_id}")
            print(f"   Status: {status}")
            print(f"   Avviato: {started}")
            print(f"   Completato: {completed or 'In corso/Non completato'}")
            print(f"   Errore: {error or 'Nessun errore'}")
            print()
    else:
        print("❌ Nessuna esecuzione trovata per il workflow PDF!")
        print("Questo potrebbe indicare che:")
        print("- Il workflow non si sta attivando automaticamente")
        print("- I trigger non sono configurati correttamente")
        print("- Non ci sono stati eventi PDF recenti")
    
    print("\nVERIFICA EVENTI PDF RECENTI")
    print("=" * 30)
    
    # Controlla eventi PDF recenti
    cursor.execute('''
        SELECT id, event_type, file_path, created_at 
        FROM pdf_monitor_events 
        ORDER BY created_at DESC 
        LIMIT 5
    ''')
    
    events = cursor.fetchall()
    
    if events:
        print(f"Trovati {len(events)} eventi PDF recenti:")
        print()
        for event in events:
            event_id, event_type, file_path, created_at = event
            print(f"- {event_type}: {file_path}")
            print(f"  Quando: {created_at}")
        print()
    else:
        print("❌ Nessun evento PDF trovato!")
        print("Questo indica che il sistema di monitoraggio PDF potrebbe non essere attivo.")
    
    print("\nVERIFICA TRIGGER ATTIVI")
    print("=" * 25)
    
    # Controlla trigger attivi per il workflow PDF
    cursor.execute('''
        SELECT name, event_type, source, active, conditions 
        FROM workflow_triggers 
        WHERE workflow_id = ? AND active = 1
    ''', ('pdf_document_add_workflow',))
    
    triggers = cursor.fetchall()
    
    if triggers:
        print(f"Trovati {len(triggers)} trigger attivi:")
        for trigger in triggers:
            name, event_type, source, active, conditions = trigger
            print(f"- {name}")
            print(f"  Tipo: {event_type} | Fonte: {source}")
            print(f"  Condizioni: {conditions}")
            print()
    else:
        print("❌ Nessun trigger attivo trovato!")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Errore nell'accesso al database: {e}")