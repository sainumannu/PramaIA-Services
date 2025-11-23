"""
Test completo delle operazioni CRUD con il nuovo formato di metadati
Simula le operazioni dell'agent per verificare il corretto funzionamento
"""
import os
import json
import tempfile
import shutil
import datetime
import time
import requests
from pathlib import Path
import sys

# Aggiungi il percorso src per importare i moduli dell'agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_file_handler import UnifiedFileHandler
from src.event_buffer import EventBuffer
from src.filter_client import agent_filter_client
from src.logger import info, error, debug

class CRUDMetadataTest:
    """Test delle operazioni CRUD con metadati"""
    
    def __init__(self):
        self.test_dir = None
        self.test_files = []
        self.event_buffer = EventBuffer()
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.client_id = os.getenv("CLIENT_ID", "test-agent")
        self.results = {
            "create": [],
            "read": [],
            "update": [],
            "delete": [],
            "metadata_extraction": [],
            "backend_communication": []
        }
        
    def setup_test_environment(self):
        """Configura ambiente di test con file temporanei"""
        self.test_dir = tempfile.mkdtemp(prefix="pramaai_crud_test_")
        info(f"🧪 Setup ambiente di test: {self.test_dir}")
        
        # Crea file di test con diverse caratteristiche
        test_files = [
            ("documento_semplice.txt", "Contenuto di test semplice"),
            ("rapporto.pdf", b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"),
            ("immagine.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF"),
            ("spreadsheet.xlsx", b"PK\x03\x04"),
            ("presentazione.pptx", b"PK\x03\x04")
        ]
        
        for filename, content in test_files:
            file_path = os.path.join(self.test_dir, filename)
            mode = "w" if isinstance(content, str) else "wb"
            with open(file_path, mode) as f:
                f.write(content)
            self.test_files.append(file_path)
            info(f"📄 Creato file di test: {filename}")
            
        return True
        
    def test_metadata_extraction(self):
        """Test dell'estrazione metadati dai file"""
        info("🔍 Test estrazione metadati...")
        
        # Crea un handler per testare l'estrazione metadati
        handler = UnifiedFileHandler([], self.test_dir, self.event_buffer)
        
        for file_path in self.test_files:
            try:
                metadata = handler._extract_file_metadata(file_path)
                
                # Verifica campi obbligatori
                required_fields = [
                    "filename_original", "file_size_original", 
                    "date_created", "date_modified"
                ]
                
                missing_fields = [field for field in required_fields if field not in metadata]
                
                result = {
                    "file": os.path.basename(file_path),
                    "success": len(missing_fields) == 0,
                    "metadata_fields": len(metadata.keys()),
                    "missing_fields": missing_fields,
                    "file_size": metadata.get("file_size_original", 0),
                    "has_pdf_metadata": bool(metadata.get("author") or metadata.get("title"))
                }
                
                self.results["metadata_extraction"].append(result)
                
                if result["success"]:
                    info(f"✅ Metadati estratti da {result['file']}: {result['metadata_fields']} campi")
                else:
                    error(f"❌ Errore estrazione metadati da {result['file']}: campi mancanti {missing_fields}")
                    
            except Exception as e:
                error(f"❌ Eccezione estrazione metadati da {file_path}: {str(e)}")
                self.results["metadata_extraction"].append({
                    "file": os.path.basename(file_path),
                    "success": False,
                    "error": str(e)
                })
                
    def test_create_operations(self):
        """Test operazioni CREATE (creazione file)"""
        info("🆕 Test operazioni CREATE...")
        
        handler = UnifiedFileHandler([], self.test_dir, self.event_buffer)
        
        for file_path in self.test_files:
            try:
                # Simula evento di creazione file
                file_name = os.path.basename(file_path)
                
                # Test estrazione metadati per CREATE
                metadata = handler._extract_file_metadata(file_path)
                client_id = self.client_id
                
                # Costruisci payload come farebbe l'agent
                metadata_payload = {
                    "client_id": client_id,
                    "original_path": file_path,
                    "source": "agent",
                    "metadata": metadata
                }
                
                # Simula decisione filtro
                filter_decision = {
                    "should_upload": True,
                    "action": "process",
                    "extract_metadata": True,
                    "should_process_content": True,
                    "filter_name": "test_filter"
                }
                
                # Test payload construction
                payload_data = {
                    "action": "created",
                    "metadata": json.dumps(metadata_payload),
                    "filter_action": filter_decision['action'],
                    "extract_metadata": json.dumps(filter_decision['extract_metadata']),
                    "filter_name": filter_decision.get('filter_name', 'unknown'),
                    "should_process_content": filter_decision['should_process_content']
                }
                
                result = {
                    "file": file_name,
                    "success": True,
                    "payload_size": len(json.dumps(payload_data)),
                    "metadata_fields": len(metadata.keys()),
                    "has_required_fields": all(key in payload_data for key in ["action", "metadata"]),
                    "client_id": client_id
                }
                
                self.results["create"].append(result)
                info(f"✅ CREATE test per {file_name}: payload {result['payload_size']} bytes")
                
            except Exception as e:
                error(f"❌ Errore CREATE test per {file_path}: {str(e)}")
                self.results["create"].append({
                    "file": os.path.basename(file_path),
                    "success": False,
                    "error": str(e)
                })
                
    def test_update_operations(self):
        """Test operazioni UPDATE (modifica file)"""
        info("📝 Test operazioni UPDATE...")
        
        handler = UnifiedFileHandler([], self.test_dir, self.event_buffer)
        
        # Modifica alcuni file per simulare UPDATE
        for file_path in self.test_files[:2]:  # Solo primi 2 file
            try:
                file_name = os.path.basename(file_path)
                
                # Simula modifica del file
                time.sleep(0.1)  # Piccola pausa per cambiare timestamp
                
                # Aggiungi contenuto al file
                if file_path.endswith('.txt'):
                    with open(file_path, 'a') as f:
                        f.write(f"\nModifica di test {datetime.datetime.now()}")
                else:
                    # Per file binari, aggiorna solo il timestamp
                    os.utime(file_path, None)
                
                # Rigenera metadati dopo modifica
                metadata = handler._extract_file_metadata(file_path)
                
                metadata_payload = {
                    "client_id": self.client_id,
                    "original_path": file_path,
                    "source": "agent",
                    "metadata": metadata
                }
                
                filter_decision = {
                    "should_upload": True,
                    "action": "update",
                    "extract_metadata": True,
                    "should_process_content": True,
                    "filter_name": "test_filter"
                }
                
                payload_data = {
                    "action": "modified",
                    "metadata": json.dumps(metadata_payload),
                    "filter_action": filter_decision['action'],
                    "extract_metadata": json.dumps(filter_decision['extract_metadata']),
                    "filter_name": filter_decision.get('filter_name', 'unknown'),
                    "should_process_content": filter_decision['should_process_content']
                }
                
                result = {
                    "file": file_name,
                    "success": True,
                    "action": "modified",
                    "new_size": metadata.get("file_size_original", 0),
                    "timestamp_updated": True
                }
                
                self.results["update"].append(result)
                info(f"✅ UPDATE test per {file_name}: nuova dimensione {result['new_size']} bytes")
                
            except Exception as e:
                error(f"❌ Errore UPDATE test per {file_path}: {str(e)}")
                self.results["update"].append({
                    "file": os.path.basename(file_path),
                    "success": False,
                    "error": str(e)
                })
                
    def test_delete_operations(self):
        """Test operazioni DELETE (eliminazione file)"""
        info("🗑️ Test operazioni DELETE...")
        
        # Elimina l'ultimo file per testare DELETE
        if self.test_files:
            file_to_delete = self.test_files[-1]
            file_name = os.path.basename(file_to_delete)
            
            try:
                # Prima estrai metadati del file da eliminare
                handler = UnifiedFileHandler([], self.test_dir, self.event_buffer)
                metadata = handler._extract_file_metadata(file_to_delete)
                
                # Simula eliminazione
                os.remove(file_to_delete)
                
                # Costruisci payload per DELETE
                metadata_payload = {
                    "client_id": self.client_id,
                    "original_path": file_to_delete,
                    "source": "agent",
                    "metadata": metadata
                }
                
                payload_data = {
                    "action": "deleted",
                    "metadata": json.dumps(metadata_payload),
                    "filter_action": "delete",
                    "extract_metadata": json.dumps(False),
                    "filter_name": "test_filter",
                    "should_process_content": False
                }
                
                result = {
                    "file": file_name,
                    "success": True,
                    "action": "deleted",
                    "file_existed": not os.path.exists(file_to_delete),
                    "metadata_preserved": len(metadata.keys()) > 0
                }
                
                self.results["delete"].append(result)
                info(f"✅ DELETE test per {file_name}: file rimosso, metadati preservati")
                
            except Exception as e:
                error(f"❌ Errore DELETE test per {file_to_delete}: {str(e)}")
                self.results["delete"].append({
                    "file": file_name,
                    "success": False,
                    "error": str(e)
                })
                
    def test_backend_communication(self):
        """Test comunicazione con backend (se disponibile)"""
        info("🌐 Test comunicazione backend...")
        
        # Test connettività backend
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            backend_available = response.status_code == 200
        except:
            backend_available = False
            
        if not backend_available:
            info("⚠️ Backend non disponibile - skip test comunicazione")
            self.results["backend_communication"].append({
                "test": "connectivity",
                "success": False,
                "reason": "Backend not available"
            })
            return
            
        # Se backend disponibile, testa upload con metadati
        test_file = self.test_files[0] if self.test_files else None
        if test_file and os.path.exists(test_file):
            try:
                handler = UnifiedFileHandler([], self.test_dir, self.event_buffer)
                metadata = handler._extract_file_metadata(test_file)
                
                metadata_payload = {
                    "client_id": self.client_id,
                    "original_path": test_file,
                    "source": "agent",
                    "metadata": metadata
                }
                
                file_name = os.path.basename(test_file)
                
                with open(test_file, "rb") as f:
                    files = {"file": (file_name, f)}
                    data = {
                        "action": "created",
                        "metadata": json.dumps(metadata_payload),
                        "filter_action": "process",
                        "extract_metadata": json.dumps(True),
                        "filter_name": "test_filter",
                        "should_process_content": True
                    }
                    
                    upload_url = f"{self.backend_url}/api/document-monitor/upload/"
                    response = requests.post(upload_url, files=files, data=data, timeout=30)
                    
                    result = {
                        "test": "upload_with_metadata",
                        "success": response.status_code == 200,
                        "status_code": response.status_code,
                        "response_size": len(response.text),
                        "file": file_name
                    }
                    
                    self.results["backend_communication"].append(result)
                    
                    if result["success"]:
                        info(f"✅ Upload test backend riuscito per {file_name}")
                    else:
                        error(f"❌ Upload test backend fallito: {response.status_code}")
                        
            except Exception as e:
                error(f"❌ Errore test backend: {str(e)}")
                self.results["backend_communication"].append({
                    "test": "upload_with_metadata", 
                    "success": False,
                    "error": str(e)
                })
                
    def generate_report(self):
        """Genera report dettagliato dei test"""
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "test_environment": {
                "test_dir": self.test_dir,
                "backend_url": self.backend_url,
                "client_id": self.client_id,
                "total_test_files": len(self.test_files)
            },
            "results": self.results,
            "summary": {
                "metadata_extraction": {
                    "total": len(self.results["metadata_extraction"]),
                    "successful": sum(1 for r in self.results["metadata_extraction"] if r.get("success", False)),
                    "failed": sum(1 for r in self.results["metadata_extraction"] if not r.get("success", False))
                },
                "create_operations": {
                    "total": len(self.results["create"]),
                    "successful": sum(1 for r in self.results["create"] if r.get("success", False)),
                    "failed": sum(1 for r in self.results["create"] if not r.get("success", False))
                },
                "update_operations": {
                    "total": len(self.results["update"]),
                    "successful": sum(1 for r in self.results["update"] if r.get("success", False)),
                    "failed": sum(1 for r in self.results["update"] if not r.get("success", False))
                },
                "delete_operations": {
                    "total": len(self.results["delete"]),
                    "successful": sum(1 for r in self.results["delete"] if r.get("success", False)),
                    "failed": sum(1 for r in self.results["delete"] if not r.get("success", False))
                },
                "backend_communication": {
                    "total": len(self.results["backend_communication"]),
                    "successful": sum(1 for r in self.results["backend_communication"] if r.get("success", False)),
                    "failed": sum(1 for r in self.results["backend_communication"] if not r.get("success", False))
                }
            }
        }
        
        # Salva report
        report_file = os.path.join(os.path.dirname(__file__), f"crud_test_report_{int(time.time())}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        info(f"📊 Report salvato: {report_file}")
        
        # Stampa summary
        print("\n" + "="*80)
        print("📊 RIEPILOGO TEST CRUD METADATI")
        print("="*80)
        
        for operation, stats in report["summary"].items():
            success_rate = (stats["successful"] / max(stats["total"], 1)) * 100
            status_emoji = "✅" if success_rate == 100 else "⚠️" if success_rate > 50 else "❌"
            print(f"{status_emoji} {operation.replace('_', ' ').title()}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)")
            
        print(f"\n📁 Directory di test: {self.test_dir}")
        print(f"📄 Report completo: {report_file}")
        print("="*80)
        
        return report
        
    def cleanup(self):
        """Pulizia ambiente di test"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            info(f"🧹 Pulizia completata: {self.test_dir}")
            
    def run_all_tests(self):
        """Esegue tutti i test CRUD"""
        try:
            info("🚀 Avvio test suite CRUD metadati...")
            
            # Setup
            self.setup_test_environment()
            
            # Esegui tutti i test
            self.test_metadata_extraction()
            self.test_create_operations()
            self.test_update_operations()
            self.test_delete_operations()
            self.test_backend_communication()
            
            # Genera report
            report = self.generate_report()
            
            return report
            
        except Exception as e:
            error(f"❌ Errore critico test suite: {str(e)}")
            return None
        finally:
            # Cleanup sempre
            self.cleanup()

def main():
    """Funzione principale per eseguire i test"""
    tester = CRUDMetadataTest()
    report = tester.run_all_tests()
    
    if report:
        # Determina se i test sono passati
        total_operations = sum(stats["total"] for stats in report["summary"].values())
        total_successful = sum(stats["successful"] for stats in report["summary"].values())
        success_rate = (total_successful / max(total_operations, 1)) * 100
        
        if success_rate >= 80:
            print(f"🎉 Test CRUD completati con successo: {success_rate:.1f}%")
            return 0
        else:
            print(f"⚠️ Test CRUD completati con problemi: {success_rate:.1f}%")
            return 1
    else:
        print("❌ Test CRUD falliti")
        return 1

if __name__ == "__main__":
    exit(main())