#!/usr/bin/env python3
"""Export active workflows (metadata, nodes, connections) from the PramaIA DB as JSON.

Writes JSON to stdout. Safe to run locally.
"""
import os
import json
import sqlite3
import sys
from datetime import datetime


def find_db_path():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.normpath(os.path.join(here, '..', '..', 'PramaIAServer', 'backend', 'data', 'database.db')),
        os.path.normpath(os.path.join(here, '..', 'PramaIAServer', 'backend', 'data', 'database.db')),
        os.path.normpath(os.path.join(os.path.dirname(here), 'PramaIAServer', 'backend', 'data', 'database.db')),
        r'C:\PramaIA\PramaIAServer\backend\data\database.db'
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def fetch_table(conn, table, where=None, params=()):
    cur = conn.cursor()
    q = f"SELECT * FROM {table}"
    if where:
        q += f" WHERE {where}"
    q += " ORDER BY id"
    cur.execute(q, params)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def main():
    db_path = find_db_path()
    if not db_path:
        print(json.dumps({"error": "database not found"}))
        sys.exit(2)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # select active workflows
        cur = conn.cursor()
        cur.execute("SELECT * FROM workflows WHERE is_active=1 ORDER BY created_at")
        wf_rows = cur.fetchall()
        workflows = []
        for wf in wf_rows:
            wf = dict(wf)
            wid = wf.get('workflow_id') or wf.get('id')
            # fetch nodes
            nodes = []
            try:
                cur.execute("SELECT * FROM workflow_nodes WHERE workflow_id = ? ORDER BY id", (wid,))
                nrows = cur.fetchall()
                for n in nrows:
                    n = dict(n)
                    # try parse JSON fields
                    for k, v in list(n.items()):
                        if isinstance(v, str) and v.strip().startswith('{'):
                            try:
                                n[k] = json.loads(v)
                            except Exception:
                                pass
                    nodes.append(n)
            except Exception:
                nodes = []

            # fetch connections
            conns = []
            try:
                cur.execute("SELECT * FROM workflow_connections WHERE workflow_id = ? ORDER BY id", (wid,))
                crows = cur.fetchall()
                for c in crows:
                    conns.append(dict(c))
            except Exception:
                conns = []

            workflows.append({
                'workflow': wf,
                'nodes': nodes,
                'connections': conns,
            })

        out = {'exported_at': datetime.utcnow().isoformat() + 'Z', 'workflows': workflows}
        # write to workflows/exported_workflows.json using utf-8 to avoid Windows encoding issues
        dst_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflows')
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, 'exported_workflows.json')
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"Exported to {dst}")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
