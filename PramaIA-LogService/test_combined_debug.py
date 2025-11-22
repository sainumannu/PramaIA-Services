#!/usr/bin/env python3
"""
Test SPECIFICO per il doppio filtro project + level
"""

import sqlite3
import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.log_manager import LogManager

def test_combined_filters():
    """Test per verificare il comportamento dei filtri combinati"""
    try:
        log_manager = LogManager()
        
        print("=== TEST FILTRI SINGOLI ===")
        
        # Test filtro singolo project
        logs_project = log_manager.get_logs(project="PramaIAServer", limit=5)
        print(f"Solo project=PramaIAServer: {len(logs_project)} log")
        if logs_project:
            levels = set(log['level'] for log in logs_project)
            print(f"  Livelli trovati: {levels}")
        
        # Test filtro singolo level
        logs_level = log_manager.get_logs(level="error", limit=5)
        print(f"Solo level=error: {len(logs_level)} log")
        if logs_level:
            projects = set(log['project'] for log in logs_level)
            print(f"  Progetti trovati: {projects}")
            
        print("\n=== TEST FILTRO COMBINATO ===")
        
        # Test filtro combinato
        logs_combined = log_manager.get_logs(project="PramaIAServer", level="error", limit=10)
        print(f"PramaIAServer + error: {len(logs_combined)} log")
        
        if logs_combined:
            print("❌ ERRORE! Non dovrebbe trovare nulla!")
            for log in logs_combined:
                print(f"  - Project: {log['project']}, Level: {log['level']}, Message: {log['message'][:50]}...")
        else:
            print("✅ CORRETTO: Nessun risultato (come dovrebbe essere)")
            
        print("\n=== TEST QUERY SQL MANUALE ===")
        
        # Query SQL diretta per debug
        with sqlite3.connect(log_manager.db_path) as conn:
            cursor = conn.cursor()
            
            print("Query costruita dal LogManager:")
            query = "SELECT * FROM logs WHERE 1=1"
            params = []
            
            # Simula la logica del LogManager
            query += " AND project = ?"
            params.append("PramaIAServer")
            
            query += " AND level = ?"
            params.append("error")
            
            print(f"Query: {query}")
            print(f"Params: {params}")
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            print(f"Risultati query diretta: {len(results)}")
            
            if results:
                print("❌ PROBLEM! Query SQL diretta trova risultati:")
                for row in results:
                    print(f"  - ID: {row[0]}, Timestamp: {row[1]}, Project: {row[2]}, Level: {row[3]}")
            else:
                print("✅ Query SQL diretta: nessun risultato")
                
        print("\n=== DEBUG QUERY LOGMANAGER ===")
        
        # Patchiamo temporaneamente per vedere la query generata
        original_get_logs = log_manager.get_logs
        
        def debug_get_logs(*args, **kwargs):
            conn = log_manager._get_connection()
            cursor = conn.cursor()
            
            # Copia la logica di costruzione query dal LogManager
            query = "SELECT * FROM logs WHERE 1=1"
            params = []
            
            project = kwargs.get('project', None)
            level = kwargs.get('level', None)
            
            if project:
                query += " AND project = ?"
                params.append(project)
                
            if level:
                if level == "lifecycle":
                    query += " AND (level = ? OR level = ?)"
                    params.append("lifecycle")
                    params.append("info")
                else:
                    query += " AND level = ?"
                    params.append(level)
                    
            print(f"DEBUG Query effettiva: {query}")
            print(f"DEBUG Params effettivi: {params}")
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            print(f"DEBUG Risultati raw: {len(results)}")
            
            conn.close()
            
            # Chiama il metodo originale
            return original_get_logs(*args, **kwargs)
        
        log_manager.get_logs = debug_get_logs
        
        print("Chiamata con debug:")
        test_results = log_manager.get_logs(project="PramaIAServer", level="error")
        print(f"Risultati finali: {len(test_results)}")
            
    except Exception as e:
        print(f"Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_combined_filters()