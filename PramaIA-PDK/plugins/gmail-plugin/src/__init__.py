"""
Email Reader Plugin Package

Plugin per lettura email multi-provider:
- Gmail API con OAuth2
- Outlook/Exchange con autenticazione
- Server IMAP generici
- Operazioni: list, read, search, attachments, folders

Autore: PramaIA Development Team
Versione: 1.0.0
"""

from .email_processor import EmailProcessor

__version__ = '1.0.0'
__author__ = 'PramaIA Development Team'

__all__ = ['EmailProcessor']