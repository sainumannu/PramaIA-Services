#!/usr/bin/env python3
"""
Test per verificare la distribuzione dei log di errore per progetto
"""

import sqlite3
import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.log_manager import LogManager

def test_error_distribution():
    """Verifica quali progetti hanno log di errore"""
    try:
        log_manager = LogManager()
        
        print("=== DISTRIBUZIONE LOG DI ERRORE PER PROGETTO ===")
        
        # Query per contare log error per progetto
        query = """
        SELECT project, COUNT(*) as error_count
        FROM logs 
        WHERE level = 'error'
        GROUP BY project
        ORDER BY error_count DESC
        """
        
        with sqlite3.connect(log_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
            if results:
                print(f"Progetti con log di errore:")
                for project, count in results:
                    print(f"  {project}: {count} log di errore")
            else:
                print("Nessun log di errore trovato nel database!")
                
        print("\n=== TUTTI I LIVELLI PER PRAMAIASERVER ===")
        
        # Query per vedere tutti i livelli di PramaIAServer
        query2 = """
        SELECT level, COUNT(*) as count
        FROM logs 
        WHERE project = 'PramaIAServer'
        GROUP BY level
        ORDER BY count DESC
        """
        
        with sqlite3.connect(log_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query2)
            results2 = cursor.fetchall()
            
            if results2:
                print(f"Livelli log per PramaIAServer:")
                for level, count in results2:
                    print(f"  {level}: {count} log")
            else:
                print("Nessun log trovato per PramaIAServer!")
                
        print("\n=== TEST FILTRO COMBINATO WORKING EXAMPLE ===")
        
        # Trova un esempio di progetto + livello che dovrebbe funzionare
        query3 = """
        SELECT project, level, COUNT(*) as count
        FROM logs 
        WHERE level IN ('error', 'warning')
        GROUP BY project, level
        HAVING count > 0
        ORDER BY count DESC
        LIMIT 5
        """
        
        with sqlite3.connect(log_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query3)
            results3 = cursor.fetchall()
            
            if results3:
                print("Esempi di combinazioni progetto+livello che DOVREBBERO funzionare:")
                for project, level, count in results3:
                    print(f"  {project} + {level}: {count} log")
                    
                    # Test il primo esempio
                    if results3.index((project, level, count)) == 0:
                        print(f"\nTest filtro per {project} + {level}:")
                        logs = log_manager.get_logs(project=project, level=level, limit=3)
                        print(f"  Trovati {len(logs)} log (limit 3)")
                        for log in logs:
                            print(f"    - {log['timestamp']}: {log['message'][:50]}...")
                            
    except Exception as e:
        print(f"Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_error_distribution()