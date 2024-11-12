# ArXiv-Zotero Connector API Documentation

## Table of Contents
- [Core Components](#core-components)
  - [ArxivZoteroCollector](#arxivzoterocollector)
  - [ArxivSearchParams](#arxivsearchparams)
  - [PaperProcessor](#paperprocessor)
- [Clients](#clients)
  - [ArxivClient](#arxivclient)
  - [ZoteroClient](#zoteroclient)
- [Utilities](#utilities)
  - [PDFManager](#pdfmanager)
  - [MetadataMapper](#metadatamapper)
  - [Credentials](#credentials)

## Core Components

### ArxivZoteroCollector

The main orchestrator class that coordinates the collection and processing of ArXiv papers.

```python
class ArxivZoteroCollector:
    def __init__(self, 
                 zotero_library_id: str, 
                 zotero_api_key: str, 
                 collection_key: str = None)
```

#### Methods

```python
async def run_collection_async(
    self, 
    search_params: ArxivSearchParams, 
    download_pdfs: bool = True
) -> Tuple[int, int]:
    """
    Run collection process asynchronously using search parameters.
    
    Args:
        search_params: Search parameters for ArXiv query
        download_pdfs: Whether to download and attach PDFs
        
    Returns:
        Tuple[int, int]: (number of successful operations, number of failed operations)
    """
```

#### Example Usage

```python
from src.core.connector import ArxivZoteroCollector
from src.core.search_params import ArxivSearchParams

collector = ArxivZoteroCollector(
    zotero_library_id="your_library_id",
    zotero_api_key="your_api_key",
    collection_key="optional_collection_key"
)

search_params = ArxivSearchParams(
    keywords=["machine learning", "neural networks"],
    categories=["cs.AI", "cs.LG"],
    max_results=10
)

successful, failed = await collector.run_collection_async(
    search_params=search_params,
    download_pdfs=True
)
```

### ArxivSearchParams

Class for organizing and building ArXiv search queries.

```python
class ArxivSearchParams:
    def __init__(
        self,
        keywords: List[str] = None,
        title_search: str = None,
        categories: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        author: str = None,
        content_type: str = None,
        max_results: int = 50
    )
```

#### Methods

```python
def build_query(self) -> str:
    """
    Build the arXiv query string based on search parameters.
    
    Returns:
        str: Formatted arXiv API query string
    """
```

#### Example Usage

```python
from datetime import datetime
from src.core.search_params import ArxivSearchParams

search_params = ArxivSearchParams(
    keywords=["reinforcement learning"],
    title_search="survey",
    categories=["cs.AI"],
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2024, 1, 1),
    author="John Smith",
    content_type="journal",
    max_results=50
)

query = search_params.build_query()
```

### PaperProcessor

Handles the processing of individual papers, including metadata mapping and PDF management.

```python
class PaperProcessor:
    def __init__(self, 
                 zotero_client, 
                 metadata_mapper, 
                 pdf_manager)
```

#### Methods

```python
async def process_paper(
    self, 
    paper: Dict, 
    download_pdfs: bool = True
) -> bool:
    """
    Process a single paper asynchronously.
    
    Args:
        paper: Dictionary containing paper metadata
        download_pdfs: Whether to download and attach PDFs
        
    Returns:
        bool: True if processing was successful
    """
```

## Clients

### ArxivClient

Handles all ArXiv-specific operations including searching and retrieving paper metadata.

```python
class ArxivClient:
    def __init__(self)
```

#### Methods

```python
def search_arxiv(
    self, 
    search_params: ArxivSearchParams
) -> List[Dict]:
    """
    Search ArXiv using provided search parameters.
    
    Args:
        search_params: Search parameters for query
        
    Returns:
        List[Dict]: List of paper metadata dictionaries
    """

def filter_by_date(
    self, 
    result: arxiv.Result, 
    start_date: Optional[datetime], 
    end_date: Optional[datetime]
) -> bool:
    """
    Filter arxiv result by date range.
    
    Returns:
        bool: True if paper is within date range
    """
```

### ZoteroClient

Handles all Zotero-specific operations including creating items and managing attachments.

```python
class ZoteroClient:
    def __init__(self, 
                 library_id: str, 
                 api_key: str, 
                 collection_key: str = None)
```

#### Methods

```python
def create_item(
    self, 
    template_type: str, 
    metadata: Dict
) -> Optional[str]:
    """
    Create a new item in Zotero.
    
    Returns:
        Optional[str]: Item key if successful
    """

def upload_attachment(
    self, 
    parent_key: str, 
    filepath: Path, 
    filename: str
) -> bool:
    """
    Upload a file attachment to a Zotero item.
    
    Returns:
        bool: True if successful
    """

def check_duplicate(
    self, 
    identifier: str, 
    identifier_field: str = 'DOI'
) -> Optional[str]:
    """
    Check if an item already exists in the library.
    
    Returns:
        Optional[str]: Item key if found
    """
```

## Utilities

### PDFManager

Handles PDF download and management operations.

```python
class PDFManager:
    def __init__(self, download_dir: Path = None)
```

#### Methods

```python
async def download_pdf(
    self, 
    url: str, 
    title: str
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Download a PDF file and return its path and filename.
    
    Returns:
        Tuple[Optional[Path], Optional[str]]: (file path, filename) if successful
    """
```

### MetadataMapper

Handles mapping between ArXiv and Zotero metadata formats.

```python
class MetadataMapper:
    def __init__(self, mapping_config: Dict[str, Dict[str, Any]])
```

#### Methods

```python
def map_metadata(
    self, 
    source_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Map source metadata to Zotero format.
    
    Returns:
        Dict: Mapped metadata in Zotero format
    """
```

### Credentials

Utilities for handling credentials and environment variables.

```python
@lru_cache(maxsize=32)
def load_credentials(env_path: str = None) -> dict:
    """
    Load credentials from environment variables or .env file with caching.
    
    Returns:
        dict: Dictionary containing credentials
    
    Raises:
        FileNotFoundError: If env_path doesn't exist
        CredentialsError: If required credentials are missing
    """
```

### PaperSummarizer

Handles the generation of paper summaries using Google's Gemini API.

```python
class PaperSummarizer:
    def __init__(self, api_key: str, config: Dict):
        """
        Initialize the summarizer with Gemini API key and configuration.
        
        Args:
            api_key: Google API key for Gemini
            config: Configuration dictionary containing summarizer settings
        """
```

#### Methods

```python
async def summarize(
    self,
    pdf_path: Path,
    zotero_client=None,
    item_key: Optional[str] = None
) -> Optional[str]:
    """
    Summarize PDF content and optionally add to Zotero.
    
    Args:
        pdf_path: Path to the PDF file
        zotero_client: Optional ZoteroClient instance
        item_key: Optional Zotero item key to attach summary to
        
    Returns:
        Optional[str]: Generated summary if successful, None otherwise
    """
```

#### Example Usage

```python
from src.utils.summarizer import PaperSummarizer
from pathlib import Path

config = {
    'summarizer': {
        'enabled': True,
        'prompt': 'Summarize this academic paper. Include main objectives and conclusions.',
        'max_length': 300,
        'rate_limit_delay': 5
    }
}

summarizer = PaperSummarizer(
    api_key='your_gemini_api_key',
    config=config
)

# Generate summary
pdf_path = Path('path/to/paper.pdf')
summary = await summarizer.summarize(
    pdf_path=pdf_path,
    zotero_client=zotero_client,  # Optional
    item_key='ITEM_KEY'  # Optional
)
```

#### Configuration Options

The summarizer accepts the following configuration options in the `config['summarizer']` dictionary:

- `enabled` (bool): Whether summarization is enabled
- `prompt` (str): Custom prompt for the summarization task
- `max_length` (int): Maximum length of generated summary in characters
- `rate_limit_delay` (int): Delay between API requests in seconds

## Complete Example

Here's a complete example showing how to use the major components together:

```python
import asyncio
from datetime import datetime
from src.core.connector import ArxivZoteroCollector
from src.core.search_params import ArxivSearchParams
from src.utils.credentials import load_credentials
from src.utils.summarizer import PaperSummarizer

async def main():
    # Load credentials
    credentials = load_credentials()
    
    # Configure summarizer
    summarizer_config = {
        'summarizer': {
            'enabled': True,
            'prompt': 'Summarize this academic paper. Include: main objectives, methodology, key findings, and conclusions.',
            'max_length': 300,
            'rate_limit_delay': 5
        }
    }
    
    # Initialize summarizer
    summarizer = PaperSummarizer(
        api_key=credentials['gemini_api_key'],
        config=summarizer_config
    )
    
    # Initialize collector with summarizer
    collector = ArxivZoteroCollector(
        zotero_library_id=credentials['library_id'],
        zotero_api_key=credentials['api_key'],
        collection_key=credentials['collection_key'],
        summarizer=summarizer,
        config=summarizer_config
    )
    
    # Create search parameters
    search_params = ArxivSearchParams(
        keywords=["reinforcement learning", "deep learning"],
        categories=["cs.AI", "cs.LG"],
        start_date=datetime(2023, 1, 1),
        max_results=10
    )
    
    try:
        # Run collection process
        successful, failed = await collector.run_collection_async(
            search_params=search_params,
            download_pdfs=True
        )
        
        print(f"Collection complete. Success: {successful}, Failed: {failed}")
        
    finally:
        # Cleanup
        await collector.close()

if __name__ == "__main__":
    asyncio.run(main())
```

This documentation covers the main components and their usage. For more detailed information about specific features or configurations, please refer to the README.md file or the individual module docstrings.