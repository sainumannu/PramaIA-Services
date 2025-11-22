import sys
import os
import requests
import asyncio
from datetime import datetime

# Importa la funzione trigger_reconciliation dal servizio
try:
    from ..reconciliation_service import trigger_reconciliation
except ImportError:
    print("Impossibile importare trigger_reconciliation. Assicurati che reconciliation_service.py sia nella cartella src.")
    sys.exit(1)

def get_vectorstore_files(backend_url, folder_path):
    url = f"{backend_url.rstrip('/')}/api/documents/list"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # La risposta dovrebbe contenere una lista di documenti
            # Adatta la logica in base alla struttura effettiva
            if isinstance(data, dict) and "documents" in data:
                return data["documents"]
            elif isinstance(data, list):
                return data
            else:
                print(f"Formato risposta inatteso: {data}")
                return []
        else:
            print(f"Errore API vectorstore: {resp.status_code} - {resp.text}")
            return []
    except Exception as e:
        print(f"Errore richiesta vectorstore: {e}")
        return []

async def main(folder_path, backend_url, report_path=None):
    print(f"[INFO] Avvio riconciliazione per: {folder_path}")
    result = await trigger_reconciliation(folder_path)
    print(f"[INFO] Riconciliazione completata. Statistiche: {result.get('stats', {})}")
    print(f"[INFO] Verifica presenza file nel vectorstore...")
    files_in_vectorstore = get_vectorstore_files(backend_url, folder_path)
    # Normalizza i nomi dei file presenti nel vectorstore
    vectorstore_filenames = set()
    for doc in files_in_vectorstore:
        # Adatta in base alla struttura: cerca il campo filename o path
        if isinstance(doc, dict):
            fname = doc.get("filename") or doc.get("file_name") or doc.get("path") or doc.get("relative_path")
            if fname:
                vectorstore_filenames.add(fname)
        elif isinstance(doc, str):
            vectorstore_filenames.add(doc)

    report_lines = []
    for file_path in result.get('actions', []):
        fname = os.path.basename(file_path.get('file'))
        found = fname in vectorstore_filenames
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
