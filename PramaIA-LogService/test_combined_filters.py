#!/usr/bin/env python
"""
Script per testare la combinazione di filtri progetto + livello
"""

import sqlite3
import os

# Percorso al database
db_path = os.path.join(os.path.dirname(__file__), "logs", "log_database.db")

def test_combined_filters():
    """Test combinazione filtri progetto + livello"""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=== TEST COMBINAZIONE FILTRI ===\n")
    
    # 1. Vediamo tutti i progetti che hanno log di errore
    print("1. Progetti con log di errore:")
    cursor.execute("SELECT project, COUNT(*) as count FROM logs WHERE level = 'error' GROUP BY project ORDER BY count DESC")
    projects_with_errors = cursor.fetchall()
    for proj in projects_with_errors:
        print(f"   - {proj['project']}: {proj['count']} errori")
    
    print("\n" + "="*50 + "\n")
    
    # 2. Test filtro con progetto specifico
    if projects_with_errors:
        test_project = projects_with_errors[0]['project']
        print(f"2. Test filtro: project='{test_project}' AND level='error'")
        
        # Query senza esclusione lifecycle
        cursor.execute("SELECT COUNT(*) as count FROM logs WHERE project = ? AND level = ?", 
                      (test_project, 'error'))
        count_simple = cursor.fetchone()['count']
        print(f"   Query semplice: {count_simple} risultati")
        
        # Query con esclusione lifecycle (come nel codice attuale)
        cursor.execute("SELECT COUNT(*) as count FROM logs WHERE project = ? AND level = ? AND level NOT IN ('lifecycle', 'LIFECYCLE')", 
                      (test_project, 'error'))
        count_with_exclusion = cursor.fetchone()['count']
        print(f"   Query con esclusione lifecycle: {count_with_exclusion} risultati")
        
        if count_simple != count_with_exclusion:
            print("   ⚠️  PROBLEMA: Le due query danno risultati diversi!")
        else:
            print("   ✅ Le query danno lo stesso risultato")
    
    print("\n" + "="*50 + "\n")
    
    # 3. Test tutti i progetti
    print("3. Test filtro error per tutti i progetti:")
    cursor.execute("SELECT project, COUNT(*) as count FROM logs WHERE level = 'error' GROUP BY project")
    all_projects = cursor.fetchall()
    
    for proj in all_projects:
        project_name = proj['project']
        print(f"\n   Progetto: {project_name}")
        
        # Query con il filtro che usiamo nel codice
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM logs 
        WHERE project = ? AND level = ? AND level NOT IN ('lifecycle', 'LIFECYCLE')
        """, (project_name, 'error'))
        
        result = cursor.fetchone()
        print(f"   - Risultati con filtro attuale: {result['count']}")
        
        # Mostra alcuni esempi
        cursor.execute("""
        SELECT id, timestamp, message 
        FROM logs 
        WHERE project = ? AND level = ? 
        ORDER BY timestamp DESC LIMIT 3
        """, (project_name, 'error'))
        
        examples = cursor.fetchall()
        for i, example in enumerate(examples, 1):
            print(f"     {i}. {example['timestamp']}: {example['message'][:50]}...")
    
    conn.close()

if __name__ == "__main__":
    test_combined_filters()