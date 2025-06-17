"""ArXiv-Zotero Connector - Automatically collect papers from ArXiv and organize them in Zotero"""

from .core.connector import ArxivZoteroCollector
from .core.search_params import ArxivSearchParams
from .utils.credentials import load_credentials, CredentialsError
from .utils.pdf_manager import PDFManager
from .utils.summarizer import PaperSummarizer

__version__ = "0.1.0"
__author__ = "Stepan Kropachev"
__email__ = "kropachev.st@gmail.com"

__all__ = [
    "ArxivZoteroCollector",
    "ArxivSearchParams",
    "load_credentials",
    "CredentialsError",
    "PDFManager",
    "PaperSummarizer",
]
