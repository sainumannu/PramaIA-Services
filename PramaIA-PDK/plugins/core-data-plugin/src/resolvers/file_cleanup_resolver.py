import os
import shutil
from datetime import datetime

def file_cleanup_resolver(inputs, config=None, context=None):

    """
    Esegue la rimozione o archiviazione di un file.
    inputs: dict con chiavi 'file_path', 'mode', 'backup_dir', 'log'
    config: dict opzionale con default_mode, default_backup_dir
    context: opzionale, info esecuzione
    """
    file_path = inputs.get('file_path')
    mode = inputs.get('mode') or (config.get('default_mode') if config else 'archive')
    backup_dir = inputs.get('backup_dir') or (config.get('default_backup_dir') if config else None)
    log = inputs.get('log', False)

    # Log ingresso nodo
    entry_msg = f"[FileCleanup] INGRESSO nodo: file_path={file_path}, mode={mode}, backup_dir={backup_dir}"
    if log and context and hasattr(context, 'logger'):
        context.logger.info(entry_msg)
    elif log:
        print(entry_msg)

    if not file_path or not os.path.isfile(file_path):
        msg = f"File non trovato: {file_path}"
        # Log uscita nodo (errore)
        exit_msg = f"[FileCleanup] USCITA nodo (errore): {msg}"
        if log and context and hasattr(context, 'logger'):
            context.logger.error(exit_msg)
        elif log:
            print(exit_msg)
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
        # Log uscita nodo (successo)
        exit_msg = f"[FileCleanup] USCITA nodo (successo): {msg}"
        if log and context and hasattr(context, 'logger'):
            context.logger.info(exit_msg)
        elif log:
            print(exit_msg)
        return {'result': msg}
    except Exception as e:
        msg = f"Errore: {str(e)}"
        # Log uscita nodo (errore)
        exit_msg = f"[FileCleanup] USCITA nodo (errore): {msg}"
        if log and context and hasattr(context, 'logger'):
            context.logger.error(exit_msg)
        elif log:
            print(exit_msg)
        return {'result': msg}
