#!/usr/bin/env python3
"""
Inspect the LogService sqlite DB and print recent entries.

Usage: python inspect_logdb.py

Prints detected tables, their schema, row counts and last 20 rows (if any).
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
import json
import sys


def find_db_path():
    base = Path(__file__).resolve().parents[1]
    db = base / 'logs' / 'log_database.db'
    return db


def inspect_db(db_path: Path, limit: int = 20):
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return 2

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print(f"Inspecting DB: {db_path}\n")

    # list tables
    cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name")
    objs = cur.fetchall()
    if not objs:
        print("No tables or views found in DB.")
        return 0

    for row in objs:
        name = row['name']
        otype = row['type']
        print(f"--- {otype}: {name} ---")
        try:
            # schema
            cur.execute(f"PRAGMA table_info('{name}')")
            cols = [r['name'] for r in cur.fetchall()]
            if cols:
                print(f"Columns: {cols}")
            else:
                print("(no column info)")

            # count
            try:
                cur.execute(f"SELECT COUNT(*) as c FROM '{name}'")
                cnt = cur.fetchone()['c']
            except Exception:
                cnt = None
            print(f"Row count: {cnt}")

            if cnt and cnt > 0:
                order_col = 'id' if 'id' in cols else 'rowid'
                q = f"SELECT * FROM '{name}' ORDER BY {order_col} DESC LIMIT {limit}"
                cur.execute(q)
                rows = cur.fetchall()
                # print header
                header = cols if cols else rows[0].keys()
                print('\t'.join(header))
                for r in rows:
                    vals = [json.dumps(r[c], ensure_ascii=False) if c in r.keys() else 'null' for c in header]
                    print('\t'.join(vals))
        except Exception as e:
            print(f"Error reading table {name}: {e}")
        print()

    conn.close()
    return 0


def main():
    db = find_db_path()
    return inspect_db(db)


if __name__ == '__main__':
    sys.exit(main())
