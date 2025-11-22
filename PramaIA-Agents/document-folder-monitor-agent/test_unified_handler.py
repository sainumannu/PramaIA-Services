"""
Script di test per verificare il corretto funzionamento dell'handler unificato.
Questo script simula diversi eventi del filesystem e verifica che vengano gestiti correttamente.
"""
import os
import time
import shutil
import sys
from pathlib import Path
from tempfile import mkdtemp
from src.unified_file_handler import UnifiedFileHandler
from src.event_buffer import EventBuffer
from src.logger import info, warning, error, debug

# Configura livello di logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Crea una directory temporanea per i test
test_dir = mkdtemp(prefix="unified_handler_test_")
info(f"Directory di test creata: {test_dir}")

# Directory per i PDF di test
test_pdf_dir = os.path.join(test_dir, "pdfs")
os.makedirs(test_pdf_dir, exist_ok=True)

# Crea un event buffer di test
event_buffer = EventBuffer(db_path=os.path.join(test_dir, "test_events.db"))

# Crea documento di test
def create_test_pdf(name="test_document.pdf"):
    """Crea un file PDF di test"""
    pdf_path = os.path.join(test_pdf_dir, name)
    with open(pdf_path, "w") as f:
        f.write("Questo è un file di test che simula un PDF")
    return pdf_path

def test_handler_creation():
    """Test la creazione dell'handler unificato"""
    info("TEST: Creazione handler unificato")
    try:
        document_list = []
        handler = UnifiedFileHandler(document_list, test_pdf_dir, event_buffer)
        info("✅ Handler creato con successo")
        return handler
    except Exception as e:
        error(f"❌ Errore nella creazione dell'handler: {e}")
        return None

def test_on_created_event(handler):
    """Test dell'evento on_created"""
    info("TEST: Evento on_created")
    try:
        # Crea un file di test
        file_name = "created_test.pdf"
        pdf_path = create_test_pdf(file_name)
        
        # Simula un evento di creazione file
        class MockEvent:
            def __init__(self, src_path):
                self.src_path = src_path
                self.is_directory = False
        
        mock_event = MockEvent(pdf_path)
        handler.on_created(mock_event)
        info("✅ Evento on_created gestito")
        
        # Verifica che l'evento sia stato registrato nel buffer
        time.sleep(1)  # Attendi che l'evento venga processato
        events = event_buffer.get_recent_events(include_history=True)
        
        found = False
        for event in events:
            if event['file_name'] == file_name and event['event_type'] == 'created':
                found = True
                info(f"✅ Evento trovato nel buffer: {event}")
                break
        
        if not found:
            warning("⚠️ Evento non trovato nel buffer")
        
        return pdf_path
    except Exception as e:
        error(f"❌ Errore nel test on_created: {e}")
        return None

def test_on_modified_event(handler, file_path):
    """Test dell'evento on_modified"""
    info("TEST: Evento on_modified")
    try:
        # Modifica il file
        with open(file_path, "a") as f:
            f.write("\nModifica al file di test")
        
        # Simula un evento di modifica file
        class MockEvent:
            def __init__(self, src_path):
                self.src_path = src_path
                self.is_directory = False
        
        mock_event = MockEvent(file_path)
        handler.on_modified(mock_event)
        info("✅ Evento on_modified gestito")
        
        # Verifica che l'evento sia stato registrato nel buffer
        time.sleep(1)  # Attendi che l'evento venga processato
        events = event_buffer.get_recent_events(include_history=True)
        
        found = False
        file_name = os.path.basename(file_path)
        for event in events:
            if event['file_name'] == file_name and event['event_type'] == 'modified':
                found = True
                info(f"✅ Evento trovato nel buffer: {event}")
                break
        
        if not found:
            warning("⚠️ Evento non trovato nel buffer")
    except Exception as e:
        error(f"❌ Errore nel test on_modified: {e}")

def test_on_deleted_event(handler, file_path):
    """Test dell'evento on_deleted"""
    info("TEST: Evento on_deleted")
    try:
        file_name = os.path.basename(file_path)
        
        # Elimina il file
        os.remove(file_path)
        
        # Simula un evento di eliminazione file
        class MockEvent:
            def __init__(self, src_path):
                self.src_path = src_path
                self.is_directory = False
        
        mock_event = MockEvent(file_path)
        handler.on_deleted(mock_event)
        info("✅ Evento on_deleted gestito")
        
        # Verifica che l'evento sia stato registrato nel buffer
        time.sleep(1)  # Attendi che l'evento venga processato
        events = event_buffer.get_recent_events(include_history=True)
        
        found = False
        for event in events:
            if event['file_name'] == file_name and event['event_type'] == 'deleted':
                found = True
                info(f"✅ Evento trovato nel buffer: {event}")
                break
        
        if not found:
            warning("⚠️ Evento deleted non trovato nel buffer")
    except Exception as e:
        error(f"❌ Errore nel test on_deleted: {e}")

def test_on_moved_event(handler):
    """Test dell'evento on_moved"""
    info("TEST: Evento on_moved")
    try:
        # Crea un file di test
        src_name = "source_test.pdf"
        src_path = create_test_pdf(src_name)
        
        # Percorso di destinazione
        dest_name = "destination_test.pdf"
        dest_path = os.path.join(test_pdf_dir, dest_name)
        
        # Sposta il file
        shutil.move(src_path, dest_path)
        
        # Simula un evento di spostamento file
        class MockEvent:
            def __init__(self, src_path, dest_path):
                self.src_path = src_path
                self.dest_path = dest_path
                self.is_directory = False
        
        mock_event = MockEvent(src_path, dest_path)
        handler.on_moved(mock_event)
        info("✅ Evento on_moved gestito")
        
        # Verifica che l'evento sia stato registrato nel buffer
        time.sleep(1)  # Attendi che l'evento venga processato
        events = event_buffer.get_recent_events(include_history=True)
        
        found_moved = False
        for event in events:
            if (event['file_name'] == dest_name and 
                event['event_type'] == 'moved' and 
                event.get('source_file') == src_name):
                found_moved = True
                info(f"✅ Evento moved trovato nel buffer: {event}")
                break
        
        if not found_moved:
            warning("⚠️ Evento moved non trovato nel buffer")
    except Exception as e:
        error(f"❌ Errore nel test on_moved: {e}")

def test_filter_rules(handler):
    """Test delle regole di filtro"""
    info("TEST: Regole di filtro")
    try:
        # Crea un file che dovrebbe essere ignorato
        ignored_file = os.path.join(test_pdf_dir, ".DS_Store")
        with open(ignored_file, "w") as f:
            f.write("File di sistema macOS")
        
        # Verifica che venga ignorato
        should_ignore = handler._should_ignore_file(ignored_file)
        if should_ignore:
            info(f"✅ File {os.path.basename(ignored_file)} correttamente ignorato")
        else:
            warning(f"⚠️ File {os.path.basename(ignored_file)} non ignorato")
        
        # Test con un file PDF
        pdf_file = os.path.join(test_pdf_dir, "test.pdf")
        with open(pdf_file, "w") as f:
            f.write("Contenuto PDF")
        
        should_ignore = handler._should_ignore_file(pdf_file)
        if not should_ignore:
            info(f"✅ File PDF correttamente NON ignorato")
        else:
            warning(f"⚠️ File PDF erroneamente ignorato")
    except Exception as e:
        error(f"❌ Errore nel test delle regole di filtro: {e}")

def cleanup():
    """Pulizia delle risorse di test"""
    info(f"Pulizia directory di test: {test_dir}")
    try:
        shutil.rmtree(test_dir)
        info("✅ Pulizia completata")
    except Exception as e:
        error(f"❌ Errore durante la pulizia: {e}")

def run_tests():
    """Esegue tutti i test"""
    info("Inizio test dell'handler unificato")
    
    # Test creazione handler
    handler = test_handler_creation()
    if not handler:
        error("Test fallito: impossibile creare l'handler")
        return False
    
    # Test regole di filtro
    test_filter_rules(handler)
    
    # Test evento created
    created_file = test_on_created_event(handler)
    if not created_file:
        warning("Test on_created fallito, salto i test successivi")
    else:
        # Test evento modified
        test_on_modified_event(handler, created_file)
        
        # Test evento deleted
        test_on_deleted_event(handler, created_file)
    
    # Test evento moved
    test_on_moved_event(handler)
    
    info("Test completati")
    return True

if __name__ == "__main__":
    try:
        success = run_tests()
        cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        error(f"Errore non gestito durante i test: {e}")
        cleanup()
        sys.exit(1)