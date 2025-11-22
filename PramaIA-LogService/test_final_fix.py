#!/usr/bin/env python3
"""
Test DEFINITIVO per verificare che i filtri combinati funzionino
"""

import sqlite3
import sys
import os

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.log_manager import LogManager

def test_final_fix():
    """Test finale per verificare che tutto funzioni"""
    try:
        log_manager = LogManager()
        
        print("=== TEST DOPO RIMOZIONE LOGICA LIFECYCLE ===")
        
        # 1. Test PramaIAServer + error (DEVE ESSERE VUOTO)
        logs1 = log_manager.get_logs(project="PramaIAServer", level="error", limit=10)
        print(f"1. PramaIAServer + error: {len(logs1)} log")
        if logs1:
            print("❌ ERRORE! Doveva essere vuoto!")
            for log in logs1:
                print(f"   - {log['project']} | {log['level']} | {log['message'][:30]}...")
        else:
            print("✅ CORRETTO: Lista vuota!")
            
        # 2. Test PramaIA-Agents + error (DEVE TROVARE QUALCOSA)
        logs2 = log_manager.get_logs(project="PramaIA-Agents", level="error", limit=3)
        print(f"2. PramaIA-Agents + error: {len(logs2)} log")
        if logs2:
            print("✅ CORRETTO: Trovati log di errore!")
            for log in logs2:
                print(f"   - {log['project']} | {log['level']} | {log['message'][:30]}...")
        else:
            print("❌ ERRORE! Doveva trovare log di errore!")
            
        # 3. Test PramaIAServer + info (DEVE TROVARE QUALCOSA)
        logs3 = log_manager.get_logs(project="PramaIAServer", level="info", limit=3)
        print(f"3. PramaIAServer + info: {len(logs3)} log")
        if logs3:
            print("✅ CORRETTO: Trovati log info!")
            for log in logs3:
                print(f"   - {log['project']} | {log['level']} | {log['message'][:30]}...")
        else:
            print("❌ ERRORE! Doveva trovare log info!")
            
        # 4. Test lifecycle (SE ESISTONO)
        logs4 = log_manager.get_logs(level="lifecycle", limit=3)
        print(f"4. Solo level=lifecycle: {len(logs4)} log")
        if logs4:
            print("✅ TROVATI log lifecycle!")
            for log in logs4:
                print(f"   - {log['project']} | {log['level']} | {log['message'][:30]}...")
        else:
            print("ℹ️  Nessun log esplicitamente marcato come 'lifecycle'")
            
        # 5. Test warning + progetto specifico
        logs5 = log_manager.get_logs(project="PramaIA-Agents", level="warning", limit=3)
        print(f"5. PramaIA-Agents + warning: {len(logs5)} log")
        if logs5:
            print("✅ TROVATI log warning!")
            for log in logs5:
                print(f"   - {log['project']} | {log['level']} | {log['message'][:30]}...")
        else:
            print("ℹ️  Nessun log warning per PramaIA-Agents")
            
        print("\n=== VERIFICA DATABASE COUNTS ===")
        
        with sqlite3.connect(log_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Count per progetto e livello
            cursor.execute("""
                SELECT project, level, COUNT(*) as count 
                FROM logs 
                GROUP BY project, level 
                ORDER BY project, level
            """)
            
            results = cursor.fetchall()
            print("Distribuzione reale nel database:")
            for project, level, count in results:
                print(f"  {project} | {level}: {count} log")
                
    except Exception as e:
        print(f"Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_fix()