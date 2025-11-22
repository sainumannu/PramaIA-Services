#!/usr/bin/env python3
"""
Test per verificare il flusso di eventi di cancellazione file
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.log_manager import LogManager

def analyze_deletion_flow():
    """Analizza il flusso di log per eventi di cancellazione"""
    try:
        log_manager = LogManager()
        
        print("=== ANALISI FLUSSO CANCELLAZIONE FILE ===")
        
        # Cerca log recenti (ultime 2 ore)
        cutoff_time = (datetime.now() - timedelta(hours=2)).isoformat()
        
        with sqlite3.connect(log_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Log dall'Agent (dovrebbero esserci)
            print("\n1. LOG DALL'AGENT:")
            cursor.execute("""
                SELECT timestamp, level, message, details
                FROM logs 
                WHERE project = 'PramaIA-Agents' 
                AND timestamp > ?
                AND (message LIKE '%eliminat%' OR message LIKE '%delet%' OR message LIKE '%rimov%' OR message LIKE '%removed%')
                ORDER BY timestamp DESC
                LIMIT 10
            """, (cutoff_time,))
            
            agent_logs = cursor.fetchall()
            if agent_logs:
                print(f"Trovati {len(agent_logs)} log dall'Agent:")
                for log in agent_logs:
                    print(f"  {log[0]} | {log[1]} | {log[2][:80]}...")
            else:
                print("❌ Nessun log di cancellazione dall'Agent")
                
            # 2. Log dal PramaIAServer (dovrebbero esserci ma mancano)
            print("\n2. LOG DAL PRAMAIASERVER:")
            cursor.execute("""
                SELECT timestamp, level, message, details
                FROM logs 
                WHERE project = 'PramaIAServer' 
                AND timestamp > ?
                AND (message LIKE '%eliminat%' OR message LIKE '%delet%' OR message LIKE '%rimov%' OR message LIKE '%removed%' OR message LIKE '%evento%' OR message LIKE '%workflow%')
                ORDER BY timestamp DESC
                LIMIT 10
            """, (cutoff_time,))
            
            server_logs = cursor.fetchall()
            if server_logs:
                print(f"Trovati {len(server_logs)} log dal PramaIAServer:")
                for log in server_logs:
                    print(f"  {log[0]} | {log[1]} | {log[2][:80]}...")
            else:
                print("❌ NESSUN log di cancellazione dal PramaIAServer - PROBLEMA!")
                
            # 3. Tutti i log recenti dal PramaIAServer per vedere cosa riceve
            print("\n3. TUTTI I LOG RECENTI PRAMAIASERVER:")
            cursor.execute("""
                SELECT timestamp, level, message
                FROM logs 
                WHERE project = 'PramaIAServer' 
                AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 15
            """, (cutoff_time,))
            
            all_server_logs = cursor.fetchall()
            if all_server_logs:
                print(f"Ultimi {len(all_server_logs)} log dal PramaIAServer:")
                for log in all_server_logs:
                    print(f"  {log[0]} | {log[1]} | {log[2][:80]}...")
            else:
                print("❌ NESSUN log recente dal PramaIAServer - IL SERVER È ATTIVO?")
                
            # 4. Cerca eventi di ricezione HTTP/API
            print("\n4. LOG DI RICEZIONE EVENTI HTTP:")
            cursor.execute("""
                SELECT timestamp, level, message, details
                FROM logs 
                WHERE project = 'PramaIAServer' 
                AND timestamp > ?
                AND (message LIKE '%POST%' OR message LIKE '%request%' OR message LIKE '%endpoint%' OR message LIKE '%ricevuto%')
                ORDER BY timestamp DESC
                LIMIT 10
            """, (cutoff_time,))
            
            http_logs = cursor.fetchall()
            if http_logs:
                print(f"Trovati {len(http_logs)} log HTTP:")
                for log in http_logs:
                    print(f"  {log[0]} | {log[1]} | {log[2][:80]}...")
            else:
                print("❌ Nessun log di ricezione HTTP - L'AGENT INVIA GLI EVENTI?")
                
        # 5. Verifica se il server è in esecuzione
        print("\n5. VERIFICA STATO SERVER:")
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ PramaIAServer risponde su porta 8000")
            else:
                print(f"⚠️  PramaIAServer risponde ma status: {response.status_code}")
        except Exception as e:
            print(f"❌ PramaIAServer non risponde: {e}")
            
    except Exception as e:
        print(f"Errore durante l'analisi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_deletion_flow()