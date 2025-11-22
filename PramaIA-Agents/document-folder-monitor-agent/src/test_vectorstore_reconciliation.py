# This file has been moved to tests/test_vectorstore_reconciliation.py
import sys
import os
import requests
import asyncio
from datetime import datetime

# Importa la funzione trigger_reconciliation dal servizio

# Aggiungi la cartella src al path per importare reconciliation_service
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
try:
    from .reconciliation_service import trigger_reconciliation
except ImportError:
    print("Impossibile importare trigger_reconciliation da reconciliation_service.py in src. Verifica il percorso e la presenza del file.")
    sys.exit(1)

def get_vectorstore_files(backend_url, folder_path):
    import urllib.parse
    norm_path = folder_path.replace("\\", "/")
    encoded_path = urllib.parse.quote(norm_path)
    url = f"{backend_url.rstrip('/')}/api/folders/state?path={encoded_path}"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("files", {})
        else:
            print(f"Errore API vectorstore: {resp.status_code} - {resp.text}")
            return {}
    except Exception as e:
        print(f"Errore richiesta vectorstore: {e}")
        return {}

async def main(folder_path, backend_url, report_path=None):
    print(f"[INFO] Avvio riconciliazione per: {folder_path}")
    result = await trigger_reconciliation(folder_path)
    print(f"[INFO] Riconciliazione completata. Statistiche: {result.get('stats', {})}")
    print(f"[INFO] Verifica presenza file nel vectorstore...")
    files_in_vectorstore = get_vectorstore_files(backend_url, folder_path)
    report_lines = []
    for file_path in result.get('actions', []):
        fname = file_path.get('file')
        found = fname in files_in_vectorstore
        status = "OK" if found else "ASSENTE"
        line = f"{fname}: {status}"
        print(line)
        report_lines.append(line)
    if report_path:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        print(f"[INFO] Report salvato su {report_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test riconciliazione e verifica vectorstore")
    parser.add_argument("folder", help="Percorso della cartella da riconciliare")
    parser.add_argument("--backend", help="URL backend PramaIA", default="http://localhost:8000")
    parser.add_argument("--report", help="Percorso file report (opzionale)")
    args = parser.parse_args()
    asyncio.run(main(args.folder, args.backend, args.report))
