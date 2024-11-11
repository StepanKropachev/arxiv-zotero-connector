# Import clients from this directory
from .arxiv_client import ArxivClient
from .zotero_client import ZoteroClient

# Import core and utils without causing circular dependencies
from ..core.search_params import ArxivSearchParams
from ..utils.credentials import load_credentials, CredentialsError

__all__ = [
    'ArxivClient',          # arXiv API client
    'ZoteroClient',         # Zotero API client
    'ArxivSearchParams',    # Class for configuring arXiv searches
    'load_credentials',     # Utility function for loading credentials
    'CredentialsError'      # Custom exception for credential handling
]

# Package metadata
__version__ = '0.1.0'
__author__ = 'Your Name'
__email__ = 'your.email@example.com'