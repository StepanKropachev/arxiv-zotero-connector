# ArXiv-Zotero Connector

A Python tool to automatically collect ArXiv papers and add them to your Zotero library based on specified keywords.

## Features

- Search ArXiv papers based on keywords
- Automatically create Zotero entries with full metadata
- Download PDF files and attach them to Zotero entries
- Organize papers into specific Zotero collections
- Configurable search parameters (time range, max results)
- Robust error handling and logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/arxiv-zotero-connector.git
cd arxiv-zotero-connector
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Zotero credentials:
```bash
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_API_KEY=your_api_key
COLLECTION_KEY=your_collection_key  # Optional
```

## Usage

```python
from zotero_connector import ArxivZoteroCollector

collector = ArxivZoteroCollector(
    zotero_library_id="your_library_id",
    zotero_api_key="your_api_key",
    collection_key="your_collection_key"  # Optional
)

keywords = [
    "multi-agent systems",
    "moral agents AI",
    "agent decision making"
]

successful, failed = collector.run_collection(
    keywords=keywords,
    max_results=5,
    days_back=7,
    download_pdfs=True
)
```

## Configuration

The main configuration parameters are:
- `keywords`: List of search terms for ArXiv
- `max_results`: Maximum number of papers to process
- `days_back`: How far back to search for papers
- `download_pdfs`: Whether to download and attach PDFs

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.