import os
import shutil
from datetime import datetime

def resolve_file_cleanup(inputs, config=None):
    """
    Esegue la rimozione o archiviazione di un file.
    inputs: dict con chiavi 'file_path', 'mode', 'backup_dir', 'log'
    config: dict opzionale con default_mode, default_backup_dir
    """
    file_path = inputs.get('file_path')
    mode = inputs.get('mode') or (config.get('default_mode') if config else 'archive')
    backup_dir = inputs.get('backup_dir') or (config.get('default_backup_dir') if config else None)
    log = inputs.get('log', False)
    result = {}

    if not file_path or not os.path.isfile(file_path):
        msg = f"File non trovato: {file_path}"
        if log:
            print(msg)
        return {'result': msg}

    try:
        if mode == 'delete':
            os.remove(file_path)
            msg = f"File eliminato: {file_path}"
        elif mode == 'archive' and backup_dir:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            base = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archived_name = f"{base}.{timestamp}.bak"
            dest = os.path.join(backup_dir, archived_name)
            shutil.move(file_path, dest)
            msg = f"File archiviato in {dest}"
        else:
            msg = "Modalità non valida o backup_dir mancante."
        if log:
            print(msg)
        return {'result': msg}
    except Exception as e:
        msg = f"Errore: {str(e)}"
        if log:
            print(msg)
        return {'result': msg}
