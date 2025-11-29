"""
File Operations Plugin Package

Plugin per operazioni avanzate sui file del sistema:
- Apertura Explorer/Finder
- Copia/spostamento file e cartelle
- Eliminazione con conferma
- Creazione/estrazione archivi ZIP
- Informazioni sui file
- Creazione cartelle

Autore: PramaIA Development Team
Versione: 1.0.0
"""

from .file_operations_processor import FileOperationsProcessor

__version__ = '1.0.0'
__author__ = 'PramaIA Development Team'

__all__ = ['FileOperationsProcessor']