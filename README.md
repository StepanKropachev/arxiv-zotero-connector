# ArXiv-Zotero Connector

A high-performance Python tool to automatically collect ArXiv papers and add them to your Zotero library with rich metadata support.

## Features

- Asynchronous paper processing for improved performance
- Intelligent metadata mapping with configurable field definitions
- Advanced search capabilities for ArXiv papers based on keywords
- Automated Zotero entry creation with comprehensive metadata handling
- Parallel PDF download and attachment system
- Smart collection organization in Zotero
- Configurable search parameters (time range, max results)
- Connection pooling and rate limiting for robust API interaction
- Comprehensive error handling and logging

## Architecture

The connector uses a modular architecture with these key components:

- `MetadataMapper`: Flexible metadata field mapping system
- `ArxivZoteroCollector`: Core collection and processing engine
- Configuration modules for easy customization:
  - `metadata_config.py`: Core mapping infrastructure
  - `arxiv_config.py`: ArXiv-specific field mappings

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/arxiv-zotero-connector.git
cd arxiv-zotero-connector
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Unix/MacOS:
source .venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up your credentials by creating a `.env` file in the project directory:
```bash
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_API_KEY=your_api_key
COLLECTION_KEY=your_collection_key  # Optional
```

### How to get your_library_id
1. Go to https://www.zotero.org/settings/
2. Navigate to *Security* in the left side-bar
3. Scroll down to *Applications*
4. Find your User ID in: "Your user ID for use in API calls is XXXXXX"

### How to get your_api_key
1. Go to https://www.zotero.org/settings/
2. Navigate to *Security* in the left side-bar
3. Scroll down to *Applications*
4. Click *Create new private key*
5. Name it and grant all read/write permissions
6. Save the generated key

### How to get your_collection_key
1. Open your Zotero web library
2. Click on the target folder in the sidebar
3. The collection key is in the URL (format: XXX1XXX0)
   
## Usage

```python
from connector import ArxivZoteroCollector
from metadata_config import MetadataMapper
from arxiv_config import ARXIV_TO_ZOTERO_MAPPING

# Initialize the metadata mapper
metadata_mapper = MetadataMapper(ARXIV_TO_ZOTERO_MAPPING)

# Initialize the collector
collector = ArxivZoteroCollector(
    zotero_library_id=credentials['library_id'],
    zotero_api_key=credentials['api_key'],
    collection_key=credentials['collection_key'],  # Optional
    metadata_mapper=metadata_mapper
)

keywords = [
    "multi-agent systems",
    "moral agents AI",
    "agent decision making"
]

# Asynchronously collect papers
successful, failed = await collector.run_collection(
    keywords=keywords,
    max_results=5,
    days_back=7,
    download_pdfs=True,
    concurrent_downloads=3  # Control concurrent operations
)
```

## Configuration Parameters

### Core Parameters
- `keywords`: List of search terms for ArXiv
- `max_results`: Maximum number of papers to process
- `days_back`: How far back to search for papers
- `download_pdfs`: Whether to download and attach PDFs

### Performance Tuning
- `concurrent_downloads`: Number of concurrent paper downloads (default: 3)
- `request_delay`: Delay between API requests in seconds (default: 1)
- `max_retries`: Maximum number of retry attempts for failed requests (default: 3)

## Metadata Configuration

You can customize metadata mapping by modifying `arxiv_config.py`:

```python
ARXIV_TO_ZOTERO_MAPPING = {
    'id': 'archiveLocation',
    'primary_category': 'extra',
    'title': 'title',
    # Add custom mappings here
}
```

## Error Handling and Logs

The system provides comprehensive logging in `zotero_collector.log`:
- Operation tracking with async context
- Detailed error messages and stack traces
- API response monitoring
- Performance metrics

## Roadmap

- [ ] Intelligent paper summarization with AI integration
- [ ] CRON job functionality for automated collection
- [ ] User interface for easy configuration
- [ ] Advanced storage management
- [ ] Custom metadata transformation rules
- [ ] Batch processing improvements

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License