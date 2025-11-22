#!/usr/bin/env python3
"""
Generate Markdown documentation for exported workflows.

Reads `workflows/exported_workflows.json` for workflow structure and
reads the server sqlite `workflow_triggers` table to map triggers to workflows.

Writes per-workflow Markdown files into `docs/workflows/` and a README.md with
regeneration instructions.

Run from repository root or directly with Python.
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import sys


def find_paths():
    repo_root = Path(__file__).resolve().parents[1]
    exported_json = repo_root / "workflows" / "exported_workflows.json"
    # Default DB location used by the project
    db_path = Path("C:/PramaIA/PramaIAServer/backend/data/database.db")
    docs_dir = repo_root / "docs" / "workflows"
    return repo_root, exported_json, db_path, docs_dir


def load_export(exported_json: Path):
    if not exported_json.exists():
        print(f"Export file not found: {exported_json}")
        return None
    return json.loads(exported_json.read_text(encoding="utf-8"))


def load_triggers(db_path: Path):
    if not db_path.exists():
        print(f"DB not found at {db_path}, continuing without triggers mapping.")
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM workflow_triggers")
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    except Exception as e:
        print(f"Unable to read workflow_triggers: {e}")
        return []
    finally:
        conn.close()


def match_triggers_for_workflow(triggers, wf_record):
    # wf_record: dict with workflow metadata
    matches = []
    wf_text_id = wf_record.get("workflow_id")
    wf_db_id = wf_record.get("id")
    for t in triggers:
        for v in t.values():
            # match textual workflow id or numeric id
            if v == wf_text_id or v == wf_db_id or v == str(wf_db_id):
                matches.append(t)
                break
    return matches


def mk_md_for_workflow(item, triggers_for_wf):
    wf = item["workflow"]
    nodes = item.get("nodes", [])
    conns = item.get("connections", [])

    lines = []
    lines.append(f"# {wf.get('name', wf.get('workflow_id'))}")
    lines.append("")
    lines.append(f"**workflow_id:** `{wf.get('workflow_id')}`")
    lines.append("")
    if wf.get("description"):
        lines.append(wf.get("description"))
        lines.append("")

    # metadata
    lines.append("## Metadata")
    lines.append("")
    meta_keys = ["id", "created_by", "created_at", "updated_at", "is_active", "is_public", "category", "tags"]
    for k in meta_keys:
        if k in wf and wf[k] is not None:
            lines.append(f"- **{k}**: `{wf[k]}`")
    lines.append("")

    # triggers
    lines.append("## Triggers / Event sources")
    lines.append("")
    if triggers_for_wf:
        for t in triggers_for_wf:
            # pretty-print trigger row
            lines.append("- Trigger:")
            for k, v in t.items():
                lines.append(f"  - **{k}**: `{v}`")
            lines.append("")
    else:
        lines.append("No triggers found in DB for this workflow. Likely triggered by event-sources configured in the PDK or by code.")
        lines.append("")

    # nodes
    lines.append("## Nodes")
    lines.append("")
    for n in nodes:
        nid = n.get("node_id") or n.get("id")
        lines.append(f"### {n.get('name','(no name)')} — `{nid}`")
        if n.get("node_type"):
            lines.append(f"- **type**: `{n.get('node_type')}`")
        if n.get("description"):
            lines.append(f"- {n.get('description')}")
        conf = n.get("config")
        if conf:
            conf_json = json.dumps(conf, ensure_ascii=False, indent=2)
            lines.append("")
            lines.append("```json")
            lines.append(conf_json)
            lines.append("```")
        lines.append("")

    # connections
    lines.append("## Connections (edges)")
    lines.append("")
    for c in conns:
        lines.append(f"- `{c.get('from_node_id')}`:{c.get('from_port')} -> `{c.get('to_node_id')}`:{c.get('to_port')}")
    lines.append("")

    # operational notes
    lines.append("## Operational notes")
    lines.append("")
    lines.append("- Source events: typically produced by the document monitor event-source (see event-sources/document-monitor-event-source).")
    lines.append("- Vector store collection: `documents` is used by these workflows for storage and retrieval.")
    lines.append("")
    lines.append("---")
    lines.append(f"_Generated on {datetime.utcnow().isoformat()}Z_")
    lines.append("")
    return "\n".join(lines)


def main():
    repo_root, exported_json, db_path, docs_dir = find_paths()
    data = load_export(exported_json)
    if data is None:
        print("No export available. Aborting.")
        return 2

    triggers = load_triggers(db_path)

    docs_dir.mkdir(parents=True, exist_ok=True)

    # README
    readme_lines = []
    readme_lines.append("# Workflow documentation")
    readme_lines.append("")
    readme_lines.append("This folder contains generated documentation for workflows active in the runtime database. Files are generated from `workflows/exported_workflows.json` and the `workflow_triggers` table in the server DB.")
    readme_lines.append("")
    readme_lines.append("To regenerate:")
    readme_lines.append("```")
    readme_lines.append("python scripts/generate_workflow_docs.py")
    readme_lines.append("```")
    readme_lines.append("")

    # per-workflow files
    for item in data.get("workflows", []):
        wf = item.get("workflow", {})
        wf_text_id = wf.get("workflow_id")
        # find triggers for this workflow
        t_for = match_triggers_for_workflow(triggers, wf)
        md = mk_md_for_workflow(item, t_for)
        fname = docs_dir / f"{wf_text_id}.md"
        fname.write_text(md, encoding="utf-8")
        readme_lines.append(f"- [{wf.get('name')}](./{fname.name}) — `{wf_text_id}`")

    (docs_dir / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")
    print(f"Wrote docs to {docs_dir}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
