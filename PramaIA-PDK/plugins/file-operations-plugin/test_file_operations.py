"""
Test suite per File Operations Plugin

Esegue test completi di tutte le operazioni sui file supportate.
"""

import os
import sys
import asyncio
import tempfile
import unittest
from pathlib import Path

# Aggiungi il path del src per import
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from file_operations_processor import FileOperationsProcessor

class TestFileOperationsProcessor(unittest.TestCase):
    """Test case per File Operations Processor."""
    
    def setUp(self):
        """Setup per ogni test."""
        self.processor = FileOperationsProcessor()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Crea file di test
        self.test_file = self.temp_path / "test_file.txt"
        self.test_file.write_text("Contenuto di test")
        
        # Crea cartella di test
        self.test_dir = self.temp_path / "test_directory"
        self.test_dir.mkdir()
        (self.test_dir / "nested_file.txt").write_text("File annidato")
    
    def tearDown(self):
        """Cleanup dopo ogni test."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
    
    async def test_file_info(self):
        """Test ottenimento informazioni file."""
        inputs = {
            'operation': 'file_info',
            'source_path': str(self.test_file)
        }
        
        result = await self.processor.process(inputs)
        
        self.assertTrue(result['success'])
        self.assertIn('file_info', result)
        self.assertEqual(result['file_info']['is_file'], True)
        self.assertIn('size_bytes', result['file_info'])
        print(f"✅ Test file_info: {result['message']}")
    
    async def test_create_directory(self):
        """Test creazione cartella."""
        new_dir = self.temp_path / "nuova_cartella"
        
        inputs = {
            'operation': 'create_dir',
            'source_path': str(new_dir)
        }
        
        result = await self.processor.process(inputs)
        
        self.assertTrue(result['success'])
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())
        print(f"✅ Test create_directory: {result['message']}")
    
    async def test_copy_file(self):
        """Test copia file."""
        dest_file = self.temp_path / "copia_test.txt"
        
        inputs = {
            'operation': 'copy',
            'source_path': str(self.test_file),
            'destination_path': str(dest_file),
            'overwrite': False
        }
        
        result = await self.processor.process(inputs)
        
        self.assertTrue(result['success'])
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(), "Contenuto di test")
        print(f"✅ Test copy_file: {result['message']}")
    
    async def test_move_file(self):
        """Test spostamento file."""
        # Crea file temporaneo per spostamento
        temp_file = self.temp_path / "da_spostare.txt"
        temp_file.write_text("Da spostare")
        
        dest_file = self.temp_path / "spostato.txt"
        
        inputs = {
            'operation': 'move',
            'source_path': str(temp_file),
            'destination_path': str(dest_file),
            'overwrite': False
        }
        
        result = await self.processor.process(inputs)
        
        self.assertTrue(result['success'])
        self.assertFalse(temp_file.exists())
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(), "Da spostare")
        print(f"✅ Test move_file: {result['message']}")
    
    async def test_create_zip(self):
        """Test creazione ZIP."""
        zip_file = self.temp_path / "test_archive.zip"
        
        inputs = {
            'operation': 'zip',
            'source_path': str(self.test_dir),
            'destination_path': str(zip_file),
            'zip_compression': 'best'
        }
        
        result = await self.processor.process(inputs)
        
        self.assertTrue(result['success'])
        self.assertTrue(zip_file.exists())
        self.assertGreater(zip_file.stat().st_size, 0)
        print(f"✅ Test create_zip: {result['message']}")
    
    async def test_extract_zip(self):
        """Test estrazione ZIP."""
        # Prima crea un ZIP
        zip_file = self.temp_path / "test_extract.zip"
        
        inputs_zip = {
            'operation': 'zip',
            'source_path': str(self.test_dir),
            'destination_path': str(zip_file),
            'zip_compression': 'fast'
        }
        
        await self.processor.process(inputs_zip)
        
        # Poi estrailo
        extract_dir = self.temp_path / "estratto"
        
        inputs_unzip = {
            'operation': 'unzip',
            'source_path': str(zip_file),
            'destination_path': str(extract_dir),
            'overwrite': True
        }
        
        result = await self.processor.process(inputs_unzip)
        
        self.assertTrue(result['success'])
        self.assertTrue(extract_dir.exists())
        self.assertTrue((extract_dir / "nested_file.txt").exists())
        print(f"✅ Test extract_zip: {result['message']}")
    
    async def test_delete_file(self):
        """Test eliminazione file (senza conferma GUI)."""
        # Crea file temporaneo per eliminazione
        temp_file = self.temp_path / "da_eliminare.txt"
        temp_file.write_text("Da eliminare")
        
        inputs = {
            'operation': 'delete',
            'source_path': str(temp_file),
            'confirm_delete': False  # Disabilita conferma per test automatico
        }
        
        result = await self.processor.process(inputs)
        
        self.assertTrue(result['success'])
        self.assertFalse(temp_file.exists())
        print(f"✅ Test delete_file: {result['message']}")
    
    async def test_invalid_operation(self):
        """Test operazione non valida."""
        inputs = {
            'operation': 'operazione_inesistente',
            'source_path': str(self.test_file)
        }
        
        result = await self.processor.process(inputs)
        
        self.assertFalse(result['success'])
        self.assertIn("non supportata", result['error'])
        print(f"✅ Test invalid_operation: {result['message']}")

async def run_all_tests():
    """Esegue tutti i test in modo asincrono."""
    print("🚀 Avvio test File Operations Plugin...")
    print("=" * 60)
    
    test_case = TestFileOperationsProcessor()
    
    # Lista di test da eseguire
    tests = [
        test_case.test_file_info,
        test_case.test_create_directory,
        test_case.test_copy_file,
        test_case.test_move_file,
        test_case.test_create_zip,
        test_case.test_extract_zip,
        test_case.test_delete_file,
        test_case.test_invalid_operation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            # Setup
            test_case.setUp()
            
            # Esegui test
            await test_func()
            passed += 1
            
            # Cleanup
            test_case.tearDown()
            
        except Exception as e:
            print(f"❌ Test {test_func.__name__} fallito: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"📊 Risultati test:")
    print(f"✅ Passati: {passed}")
    print(f"❌ Falliti: {failed}")
    print(f"📈 Totale: {passed + failed}")
    
    if failed == 0:
        print("🎉 Tutti i test sono passati!")
    else:
        print(f"⚠️  {failed} test hanno fallimenti")
    
    return failed == 0

def demo_interactive():
    """Demo interattiva per testare operazioni specifiche."""
    print("🎮 Demo Interattiva File Operations Plugin")
    print("=" * 50)
    
    # Test apertura Explorer (solo se su Windows)
    import platform
    if platform.system().lower() == 'windows':
        print("\\n📂 Test apertura Explorer...")
        
        async def test_explorer():
            processor = FileOperationsProcessor()
            
            # Apri Explorer sulla cartella corrente
            inputs = {
                'operation': 'open_explorer',
                'source_path': str(Path.cwd())
            }
            
            result = await processor.process(inputs)
            print(f"Risultato Explorer: {result['message']}")
        
        asyncio.run(test_explorer())

if __name__ == "__main__":
    # Esegui test completi
    success = asyncio.run(run_all_tests())
    
    # Demo interattiva se i test passano
    if success:
        print("\\n" + "=" * 60)
        demo_interactive()
    
    # Exit code
    sys.exit(0 if success else 1)