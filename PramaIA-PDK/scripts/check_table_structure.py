"""
Script per verificare la struttura della tabella workflows e delle tabelle correlate nel database PramaIA.
"""

import os
import sqlite3
import sys

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PramaIAServer", "backend", "db", "database.db")

def check_table_structure():
    """Verifica la struttura della tabella workflows e delle correlate."""
    if not os.path.exists(DATABASE_PATH):
        print(f"ERRORE: Il database non esiste: {DATABASE_PATH}")
        return False
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflows'")
        if not cursor.fetchone():
            print("ERRORE: La tabella 'workflows' non esiste nel database.")
            return False
        cursor.execute("PRAGMA table_info(workflows)")
        columns = cursor.fetchall()
        print("Struttura della tabella 'workflows':")
        print("-----------------------------------")
        print("| # | Nome | Tipo | NotNull | DefaultValue | PK |")
        print("-----------------------------------")
        for col in columns:
            cid, name, dtype, notnull, default_val, pk = col
            print(f"| {cid} | {name} | {dtype} | {notnull} | {default_val} | {pk} |")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%workflow%' OR name LIKE '%node%' OR name LIKE '%connection%')")
        related_tables = cursor.fetchall()
        if related_tables:
            print("\nTabelle correlate:")
            for table in related_tables:
                print(f"- {table[0]}")
                cursor.execute(f"PRAGMA table_info({table[0]})")
                rel_columns = cursor.fetchall()
                print(f"\nStruttura della tabella '{table[0]}':")
                print("-----------------------------------")
                print("| # | Nome | Tipo | NotNull | DefaultValue | PK |")
                print("-----------------------------------")
                for col in rel_columns:
                    cid, name, dtype, notnull, default_val, pk = col
                    print(f"| {cid} | {name} | {dtype} | {notnull} | {default_val} | {pk} |")
        return True
    except Exception as e:
        print(f"ERRORE durante la verifica della struttura della tabella: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = check_table_structure()
    sys.exit(0 if success else 1)
