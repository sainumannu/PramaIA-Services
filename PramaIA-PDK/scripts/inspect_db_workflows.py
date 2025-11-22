#!/usr/bin/env python3
"""Inspect the local PramaIA SQLite database and print schema + workflows info.

This script will:
 - locate the likely database file used by PramaIAServer
 - print the list of tables/views
 - print schema for `workflows` (and other key tables if present)
 - show up to N workflow rows and attempt to parse JSON columns to extract node lists

Usage:
  python inspect_db_workflows.py

It only reads the database.
"""
import os
import sys
import json
import sqlite3
from datetime import datetime


def find_db_path():
    # Forza il path del database corretto
    db_path = r"c:\PramaIA\PramaIAServer\backend\db\database.db"
    if os.path.exists(db_path):
        return db_path
    return None


def list_tables(conn):
    cur = conn.cursor()
    cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")
    return cur.fetchall()


def pragma_table_info(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info('{table}')")
    return cur.fetchall()


def inspect_workflows_table(conn, table='workflows', limit=10):
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        total = cur.fetchone()[0]
    except Exception:
        print(f"Table '{table}' not present or not accessible.")
        return

    print(f"\nFound table '{table}' with {total} rows (showing up to {limit})")

    cols = pragma_table_info(conn, table)
    col_names = [c[1] for c in cols]
    print('\nColumns: ' + ', '.join(col_names))

    # Choose a sensible subset of columns to display
    prefer = ['id', 'workflow_id', 'name', 'is_active', 'active', 'created_at', 'updated_at', 'data', 'workflow_json', 'json']
    chosen = [c for c in prefer if c in col_names]
    if not chosen:
        chosen = col_names[:6]

    qcols = ', '.join(chosen)
    try:
        cur.execute(f"SELECT {qcols} FROM {table} ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
    except Exception:
        try:
            cur.execute(f"SELECT {qcols} FROM {table} LIMIT ?", (limit,))
            rows = cur.fetchall()
        except Exception as e:
            print(f"Failed to query rows from {table}: {e}")
            return

    for r in rows:
        row = dict(zip(chosen, r))
        print('\n---')
        print(json.dumps(row, default=str, ensure_ascii=False, indent=2))

        # Try to parse any JSON-like string columns to extract nodes
        for k, v in row.items():
            if isinstance(v, str) and v.strip().startswith('{'):
                try:
                    data = json.loads(v)
                    nodes = None
                    if isinstance(data, dict):
                        nodes = data.get('nodes') or data.get('workflow', {}).get('nodes')
                        if nodes is None:
                            # search nested dicts for 'nodes'
                            for vv in data.values():
                                if isinstance(vv, dict) and 'nodes' in vv:
                                    nodes = vv.get('nodes')
                                    break
                    if nodes is not None:
                        print(f"  parsed JSON column '{k}': nodes_count={len(nodes)} sample={nodes[:5]}")
                except Exception:
                    pass


def main():
    print(f"inspect_db_workflows.py started at {datetime.now().isoformat()}")
    db_path = find_db_path()
    if not db_path:
        print("ERROR: database file not found in candidate locations.\nCandidates attempted in script.")
        sys.exit(2)

    print(f"Using database: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        print('\nTables and views:')
        for name, typ in list_tables(conn):
            print(f" - {name} ({typ})")

        key_tables = ['workflows', 'workflow_triggers', 'workflow_executions']
        for t in key_tables:
            cols = pragma_table_info(conn, t)
            if cols:
                print(f"\nSchema for {t}:")
                for cid, name, ctype, notnull, dflt, pk in cols:
                    print(f" - {name} {ctype} notnull={notnull} pk={pk} default={dflt}")

        # Inspect workflows table if present
        inspect_workflows_table(conn, 'workflows', limit=10)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
