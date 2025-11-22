#!/usr/bin/env python
"""
Script per testare direttamente le query di filtro per livello nel database
"""

import sqlite3
import os

# Percorso al database
db_path = os.path.join(os.path.dirname(__file__), "logs", "log_database.db")

def test_level_filtering():
    """Test diretto delle query di filtro per livello"""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=== TEST FILTRO LIVELLI ===\n")
    
    # 1. Vediamo tutti i livelli presenti nel database
    print("1. Livelli presenti nel database:")
    cursor.execute("SELECT DISTINCT level, COUNT(*) as count FROM logs GROUP BY level ORDER BY count DESC")
    levels = cursor.fetchall()
    for level in levels:
        print(f"   - {level['level']}: {level['count']} log")
    
    print("\n" + "="*50 + "\n")
    
    # 2. Test filtro per 'error'
    print("2. Test filtro per 'error':")
    cursor.execute("SELECT level, COUNT(*) as count FROM logs WHERE level = 'error' GROUP BY level")
    error_logs = cursor.fetchall()
    if error_logs:
        for log in error_logs:
            print(f"   - Livello: {log['level']}, Count: {log['count']}")
    else:
        print("   - Nessun log con livello 'error' trovato")
    
    # Test anche con la query modificata
    print("   Con esclusione lifecycle:")
    cursor.execute("SELECT level, COUNT(*) as count FROM logs WHERE level = 'error' AND level NOT IN ('lifecycle', 'LIFECYCLE') GROUP BY level")
    error_logs_filtered = cursor.fetchall()
    if error_logs_filtered:
        for log in error_logs_filtered:
            print(f"   - Livello: {log['level']}, Count: {log['count']}")
    else:
        print("   - Nessun log con livello 'error' trovato (con filtro)")
    
    print("\n" + "="*50 + "\n")
    
    # 3. Test filtro per 'warning'
    print("3. Test filtro per 'warning':")
    cursor.execute("SELECT level, COUNT(*) as count FROM logs WHERE level = 'warning' GROUP BY level")
    warning_logs = cursor.fetchall()
    if warning_logs:
        for log in warning_logs:
            print(f"   - Livello: {log['level']}, Count: {log['count']}")
    else:
        print("   - Nessun log con livello 'warning' trovato")
    
    print("\n" + "="*50 + "\n")
    
    # 4. Test filtro per 'lifecycle'
    print("4. Test filtro per 'lifecycle':")
    cursor.execute("SELECT level, COUNT(*) as count FROM logs WHERE level = 'lifecycle' GROUP BY level")
    lifecycle_logs = cursor.fetchall()
    if lifecycle_logs:
        for log in lifecycle_logs:
            print(f"   - Livello: {log['level']}, Count: {log['count']}")
    else:
        print("   - Nessun log con livello 'lifecycle' trovato")
    
    print("\n" + "="*50 + "\n")
    
    # 5. Vediamo alcuni esempi di log per ogni livello
    print("5. Esempi di log per livello:")
    for level_info in levels:
        level = level_info['level']
        print(f"\n   Esempi per livello '{level}':")
        cursor.execute("SELECT id, timestamp, project, module, message FROM logs WHERE level = ? LIMIT 3", (level,))
        examples = cursor.fetchall()
        for i, example in enumerate(examples, 1):
            print(f"      {i}. {example['timestamp']} - {example['project']} - {example['module']}")
            print(f"         Messaggio: {example['message'][:80]}...")
    
    print("\n" + "="*50 + "\n")
    
    # 6. Test la query specifica che usiamo in log_manager.py
    print("6. Test query come in log_manager.py:")
    
    # Simuliamo la query per level='error'
    level_str = 'error'
    query = "SELECT * FROM logs WHERE 1=1 AND level = ? AND level NOT IN ('lifecycle', 'LIFECYCLE') ORDER BY timestamp DESC LIMIT 10"
    print(f"   Query: {query}")
    print(f"   Parametri: ['{level_str}']")
    
    cursor.execute(query, (level_str,))
    results = cursor.fetchall()
    print(f"   Risultati trovati: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"      {i}. {result['level']} - {result['timestamp']} - {result['message'][:50]}...")
    
    conn.close()

if __name__ == "__main__":
    test_level_filtering()