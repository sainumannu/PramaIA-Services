#!/usr/bin/env python3
"""
🚀 GMAIL OPERAZIONI AVANZATE - DEMO
Dimostra operazioni aggiuntive facilmente implementabili
"""

import imaplib
import email
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class GmailAdvancedOperations:
    """Operazioni Gmail avanzate via IMAP"""
    
    def __init__(self, credentials_file="credentials/gmail_credentials.json"):
        """Inizializza con credenziali"""
        self.mail = None
        self.connected = False
        
        # Carica credenziali
        with open(credentials_file, 'r') as f:
            self.creds = json.load(f)
    
    def connect(self):
        """Connetti a Gmail IMAP"""
        try:
            self.mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
            self.mail.login(self.creds['username'], self.creds['app_password'])
            self.mail.select('INBOX')
            self.connected = True
            print("✅ Connesso a Gmail IMAP")
            return True
        except Exception as e:
            print(f"❌ Errore connessione: {e}")
            return False
    
    def disconnect(self):
        """Disconnetti da Gmail"""
        if self.mail and self.connected:
            self.mail.close()
            self.mail.logout()
            self.connected = False
            print("👋 Disconnesso da Gmail")
    
    def read_email_full(self, email_id: int) -> Dict[str, Any]:
        """
        🟢 OPERAZIONE 1: Leggi email completa
        Complessità: FACILE (30 min)
        """
        try:
            # Fetch email completa
            status, msg_data = self.mail.fetch(str(email_id), '(RFC822)')
            
            if status != 'OK':
                return {'error': 'Email non trovata'}
            
            # Parse email
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Estrai informazioni
            result = {
                'id': email_id,
                'subject': email_message.get('Subject', ''),
                'from': email_message.get('From', ''),
                'to': email_message.get('To', ''),
                'date': email_message.get('Date', ''),
                'body_plain': '',
                'body_html': '',
                'attachments': [],
                'size_bytes': len(msg_data[0][1])
            }
            
            # Estrai corpo email
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        result['body_plain'] = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif content_type == "text/html":
                        result['body_html'] = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif part.get_filename():  # Allegato
                        result['attachments'].append({
                            'filename': part.get_filename(),
                            'content_type': content_type,
                            'size': len(part.get_payload(decode=True) or b'')
                        })
            else:
                result['body_plain'] = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            return result
            
        except Exception as e:
            return {'error': f'Errore lettura email: {e}'}
    
    def search_emails(self, criteria: Dict[str, str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        🟢 OPERAZIONE 2: Ricerca avanzata email
        Complessità: FACILE (45 min)
        """
        try:
            search_terms = []
            
            # Costruisci criteri ricerca IMAP
            if 'from' in criteria:
                search_terms.extend(['FROM', f'"{criteria["from"]}"'])
            if 'subject' in criteria:
                search_terms.extend(['SUBJECT', f'"{criteria["subject"]}"'])
            if 'body' in criteria:
                search_terms.extend(['BODY', f'"{criteria["body"]}"'])
            if 'since_date' in criteria:
                search_terms.extend(['SINCE', criteria['since_date']])
            if 'before_date' in criteria:
                search_terms.extend(['BEFORE', criteria['before_date']])
            if 'unread_only' in criteria and criteria['unread_only']:
                search_terms.append('UNSEEN')
            
            # Esegui ricerca
            if not search_terms:
                search_terms = ['ALL']
            
            status, messages = self.mail.search(None, *search_terms)
            
            if status != 'OK':
                return []
            
            # Ottieni lista email IDs
            email_ids = messages[0].split()
            
            # Limita risultati
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            # Ottieni dettagli per ogni email
            results = []
            for email_id in email_ids:
                status, msg_data = self.mail.fetch(email_id, '(BODY[HEADER.FIELDS (SUBJECT FROM DATE)] FLAGS)')
                if status == 'OK':
                    headers = msg_data[0][1].decode('utf-8', errors='ignore')
                    flags = str(msg_data[1])
                    
                    results.append({
                        'id': int(email_id),
                        'headers_raw': headers,
                        'is_seen': '\\Seen' in flags,
                        'is_flagged': '\\Flagged' in flags
                    })
            
            return results
            
        except Exception as e:
            print(f"❌ Errore ricerca: {e}")
            return []
    
    def mark_as_read(self, email_ids: List[int]) -> Dict[str, Any]:
        """
        🟢 OPERAZIONE 3: Marca email come lette
        Complessità: FACILE (20 min)
        """
        try:
            success_count = 0
            failed_count = 0
            
            for email_id in email_ids:
                status = self.mail.store(str(email_id), '+FLAGS', '\\Seen')
                if status[0] == 'OK':
                    success_count += 1
                else:
                    failed_count += 1
            
            return {
                'success': success_count,
                'failed': failed_count,
                'total': len(email_ids)
            }
            
        except Exception as e:
            return {'error': f'Errore marcatura: {e}'}
    
    def mark_as_unread(self, email_ids: List[int]) -> Dict[str, Any]:
        """Marca email come non lette"""
        try:
            success_count = 0
            failed_count = 0
            
            for email_id in email_ids:
                status = self.mail.store(str(email_id), '-FLAGS', '\\Seen')
                if status[0] == 'OK':
                    success_count += 1
                else:
                    failed_count += 1
            
            return {
                'success': success_count,
                'failed': failed_count,
                'total': len(email_ids)
            }
            
        except Exception as e:
            return {'error': f'Errore marcatura: {e}'}
    
    def download_attachment(self, email_id: int, attachment_name: str, save_path: str = "downloads/") -> Dict[str, Any]:
        """
        🟡 OPERAZIONE 4: Download allegato
        Complessità: MEDIA (1 ora)
        """
        try:
            # Crea directory se non esiste
            os.makedirs(save_path, exist_ok=True)
            
            # Fetch email completa
            status, msg_data = self.mail.fetch(str(email_id), '(RFC822)')
            if status != 'OK':
                return {'error': 'Email non trovata'}
            
            # Parse email
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Cerca allegato
            for part in email_message.walk():
                if part.get_filename() == attachment_name:
                    # Salva allegato
                    file_path = os.path.join(save_path, attachment_name)
                    with open(file_path, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    
                    return {
                        'success': True,
                        'file_path': file_path,
                        'file_size': os.path.getsize(file_path)
                    }
            
            return {'error': f'Allegato {attachment_name} non trovato'}
            
        except Exception as e:
            return {'error': f'Errore download: {e}'}
    
    def get_folder_stats(self) -> Dict[str, Any]:
        """
        🟢 OPERAZIONE 5: Statistiche cartelle
        Complessità: FACILE (30 min)
        """
        try:
            stats = {}
            
            # Lista cartelle
            status, folders = self.mail.list()
            
            if status == 'OK':
                for folder in folders:
                    folder_name = folder.decode().split('"')[-2] if '"' in folder.decode() else folder.decode().split()[-1]
                    
                    # Seleziona cartella
                    try:
                        self.mail.select(folder_name)
                        
                        # Conta messaggi totali
                        status, total = self.mail.search(None, 'ALL')
                        total_count = len(total[0].split()) if status == 'OK' else 0
                        
                        # Conta messaggi non letti
                        status, unread = self.mail.search(None, 'UNSEEN')
                        unread_count = len(unread[0].split()) if status == 'OK' else 0
                        
                        stats[folder_name] = {
                            'total_emails': total_count,
                            'unread_emails': unread_count,
                            'read_emails': total_count - unread_count
                        }
                        
                    except:
                        stats[folder_name] = {'error': 'Cartella non accessibile'}
            
            # Torna a INBOX
            self.mail.select('INBOX')
            
            return stats
            
        except Exception as e:
            return {'error': f'Errore statistiche: {e}'}

def demo_operations():
    """Demo delle operazioni avanzate"""
    print("🚀 DEMO OPERAZIONI GMAIL AVANZATE")
    print("=====================================")
    
    # Inizializza
    gmail = GmailAdvancedOperations()
    
    if not gmail.connect():
        return
    
    try:
        # DEMO 1: Leggi email specifica
        print("\n📖 DEMO 1: Lettura email completa")
        print("-" * 40)
        email_detail = gmail.read_email_full(1)  # Prima email
        if 'error' not in email_detail:
            print(f"✅ Subject: {email_detail['subject'][:50]}...")
            print(f"✅ From: {email_detail['from'][:50]}...")
            print(f"✅ Size: {email_detail['size_bytes']:,} bytes")
            print(f"✅ Attachments: {len(email_detail['attachments'])}")
        else:
            print(f"❌ {email_detail['error']}")
        
        # DEMO 2: Ricerca avanzata
        print("\n🔍 DEMO 2: Ricerca email")
        print("-" * 40)
        search_results = gmail.search_emails({
            'from': 'gmail.com',
            'unread_only': False
        }, limit=3)
        print(f"✅ Trovate {len(search_results)} email da Gmail")
        for result in search_results[:2]:
            print(f"   📧 ID: {result['id']}, Letta: {result['is_seen']}")
        
        # DEMO 3: Statistiche cartelle
        print("\n📊 DEMO 3: Statistiche cartelle")
        print("-" * 40)
        folder_stats = gmail.get_folder_stats()
        for folder, stats in list(folder_stats.items())[:3]:
            if 'error' not in stats:
                print(f"📁 {folder}: {stats['total_emails']} totali, {stats['unread_emails']} non lette")
        
        print("\n🎉 DEMO COMPLETATA!")
        print("✅ Tutte le operazioni sono facilmente implementabili")
        print("⏱️  Tempo stimato implementazione: 2-3 ore")
        
    finally:
        gmail.disconnect()

if __name__ == "__main__":
    demo_operations()