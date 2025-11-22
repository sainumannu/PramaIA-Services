#!/usr/bin/env python3
"""
Test urgente per verificare che il filtro PramaIAServer + Error funzioni correttamente
"""

import sqlite3
import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.log_manager import LogManager

def test_filter_fix():
    """Test per verificare che il filtro PramaIAServer + Error restituisca lista vuota"""
    try:
        log_manager = LogManager()
        
        print("=== TEST FILTRO PramaIAServer + Error (DEVE ESSERE VUOTO) ===")
        
        # Test con LogManager
        logs = log_manager.get_logs(project="PramaIAServer", level="error", limit=10)
        print(f"LogManager - Log trovati per PramaIAServer + error: {len(logs)}")
        if logs:
            print("ERRORE! Doveva essere vuoto!")
            for log in logs:
                print(f"  - {log['level']}: {log['message'][:50]}...")
        else:
            print("✅ CORRETTO: Lista vuota come dovrebbe essere!")
            
        print("\n=== TEST QUERY SQL DIRETTA ===")
        
        # Test con query SQL diretta
        with sqlite3.connect(log_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Query diretta
            query = "SELECT * FROM logs WHERE project = ? AND level = ?"
            cursor.execute(query, ["PramaIAServer", "error"])
            results = cursor.fetchall()
            
            print(f"Query SQL diretta - Risultati: {len(results)}")
            if results:
                print("ERRORE! La query SQL diretta trova risultati!")
                for row in results:
                    print(f"  - ID: {row[0]}, Level: {row[3]}, Project: {row[2]}")
            else:
                print("✅ CORRETTO: Query SQL diretta restituisce lista vuota!")
                
        print("\n=== TEST ALTRE COMBINAZIONI ===")
        
        # Test PramaIA-Agents + error (dovrebbe trovare qualcosa)
        logs2 = log_manager.get_logs(project="PramaIA-Agents", level="error", limit=5)
        print(f"PramaIA-Agents + error: {len(logs2)} log trovati")
        if logs2:
            print("✅ CORRETTO: PramaIA-Agents ha log di errore!")
            for log in logs2:
                print(f"  - {log['timestamp']}: {log['message'][:50]}...")
        
        # Test PramaIAServer + info (dovrebbe trovare qualcosa)
        logs3 = log_manager.get_logs(project="PramaIAServer", level="info", limit=3)
        print(f"PramaIAServer + info: {len(logs3)} log trovati")
        if logs3:
            print("✅ CORRETTO: PramaIAServer ha log info!")
            
    except Exception as e:
        print(f"Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_filter_fix()