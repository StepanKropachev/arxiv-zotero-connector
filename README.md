# ArXiv-Zotero Connector

[![Python Version](https://img.shields.io/pypi/pyversions/arxiv-zotero-connector)](https://pypi.org/project/arxiv-zotero-connector/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Version](https://img.shields.io/pypi/v/arxiv-zotero-connector)](https://pypi.org/project/arxiv-zotero-connector/)

Automatically download, organize, and summarize arXiv papers directly into your Zotero library with AI-powered insights.

## 🚀 Features

- **Smart Search**: Search arXiv by keywords, authors, categories, or date ranges
- **Auto-Download**: Automatically download paper PDFs and attach them to Zotero entries
- **AI Summarization**: Generate concise summaries using Google's Gemini AI (optional)
- **Metadata Extraction**: Preserve complete paper metadata including authors, abstract, and publication details
- **Collection Support**: Organize papers into specific Zotero collections
- **Flexible Filtering**: Filter by journal papers, conference proceedings, or preprints
- **Batch Processing**: Process multiple papers efficiently with progress tracking

## 📋 Requirements

- Python 3.7 or higher
- Zotero account with API access
- Internet connection for downloading papers
- Google AI API key (optional, for summarization features)

## 🔧 Installation

### Install from PyPI

```bash
pip install arxiv-zotero-connector
```

### Install from GitHub

```bash
pip install git+https://github.com/StepanKropachev/arxiv-zotero-connector.git
```

### Development Installation

```bash
git clone https://github.com/StepanKropachev/arxiv-zotero-connector.git
cd arxiv-zotero-connector
pip install -e .
```

## ⚙️ Configuration

### 1. Get Zotero Credentials

1. **Library ID**: Visit [Zotero Settings](https://www.zotero.org/settings/keys) → Your user ID for API calls
2. **API Key**: 
   - Go to [Zotero Settings](https://www.zotero.org/settings/keys) → New Private Key
   - Grant all permissions and save the key
3. **Collection Key** (optional): 
   - Open your Zotero web library
   - Navigate to desired collection
   - Copy the key from the URL: `.../collections/XXXXXXXX`

### 2. Create Configuration File

Create a `.env` file in your working directory:

```env
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_API_KEY=your_api_key
COLLECTION_KEY=your_collection_key  # Optional
GOOGLE_API_KEY=your_gemini_api_key  # Optional, for AI summaries
```

## 📖 Usage

### Command Line Interface

Basic search:
```bash
arxiv-zotero --keywords "machine learning" --max-results 10
```

Advanced search with filters:
```bash
arxiv-zotero \
  --keywords "transformer" "attention" \
  --categories cs.AI cs.LG \
  --start-date 2023-01-01 \
  --max-results 20
```

Search by author:
```bash
arxiv-zotero --author "Yoshua Bengio" --start-date 2023-06-01
```

### Configuration File

Create `search_config.yaml`:
```yaml
keywords:
  - "reinforcement learning"
  - "deep learning"
categories:
  - "cs.AI"
  - "cs.LG"
max_results: 50
start_date: "2023-01-01"
content_type: "journal"  # journal, conference, or preprint

# AI Summarization settings (optional)
summarizer:
  enabled: true
  prompt: "Summarize this paper in 3 key points"
  max_length: 300
```

Run with config:
```bash
arxiv-zotero --config search_config.yaml
```

### Python API

```python
from arxiv_zotero import ArxivZoteroCollector, ArxivSearchParams
import asyncio

async def main():
    # Initialize collector
    collector = ArxivZoteroCollector(
        zotero_library_id="your_library_id",
        zotero_api_key="your_api_key",
        collection_key="optional_collection_key"
    )
    
    # Configure search
    search_params = ArxivSearchParams(
        keywords=["quantum computing", "quantum algorithms"],
        categories=["quant-ph", "cs.CC"],
        max_results=10,
        start_date=datetime(2023, 1, 1)
    )
    
    # Run collection
    successful, failed = await collector.run_collection_async(
        search_params=search_params,
        download_pdfs=True
    )
    
    print(f"Processed {successful} papers successfully, {failed} failed")

asyncio.run(main())
```

## 🎯 Examples

### Literature Review
```bash
arxiv-zotero \
  --keywords "neural architecture search" "AutoML" \
  --categories cs.LG \
  --content-type journal \
  --start-date 2022-01-01 \
  --max-results 100
```

### Conference Papers
```bash
arxiv-zotero \
  --keywords "ICLR" "NeurIPS" \
  --content-type conference \
  --start-date 2023-01-01
```

### Papers Without PDFs
```bash
arxiv-zotero --keywords "quantum" --no-pdf --max-results 50
```

## 🤖 AI Summarization

Enable AI-powered paper summaries by adding your Google AI API key:

```bash
arxiv-zotero \
  --keywords "large language models" \
  --summarizer-enabled \
  --summarizer-prompt "Explain this paper's contribution in simple terms" \
  --summary-length 500
```

## 📚 ArXiv Categories

Common categories include:
- **cs.AI**: Artificial Intelligence
- **cs.LG**: Machine Learning
- **cs.CL**: Computation and Language
- **cs.CV**: Computer Vision
- **stat.ML**: Machine Learning (Statistics)
- **math.OC**: Optimization and Control
- **quant-ph**: Quantum Physics

Full list: [arXiv Category Taxonomy](https://arxiv.org/category_taxonomy)

## 🛠️ Advanced Features

### Custom Metadata Fields

The tool preserves:
- Title, authors, abstract
- Publication date and journal references
- ArXiv ID and categories
- DOI (when available)
- Comments and version info

### Rate Limiting

The tool respects arXiv's rate limits automatically. For large batch operations, consider using:
```bash
arxiv-zotero --keywords "your search" --rate-limit 5
```

### Error Handling

Failed downloads are logged and can be retried:
- Check `arxiv_zotero.log` for details
- Papers are processed independently
- Partial failures don't stop the entire batch

## 🐛 Troubleshooting

### Common Issues

1. **"Collection not found"**: Verify your collection key or remove it to use the main library
2. **"API key invalid"**: Check your Zotero API key has proper permissions
3. **Import errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`
4. **PDF download fails**: Check your internet connection and disk space

### Debug Mode

For detailed logging:
```python
import logging
logging.getLogger('arxiv_zotero').setLevel(logging.DEBUG)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [arXiv API](https://arxiv.org/help/api) for providing access to paper metadata
- [Zotero](https://www.zotero.org/) for the excellent reference management platform
- [Google Gemini](https://deepmind.google/technologies/gemini/) for AI summarization capabilities

## 📬 Support

- 📧 Email: kropachev.st@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/StepanKropachev/arxiv-zotero-connector/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/StepanKropachev/arxiv-zotero-connector/discussions)

## 📈 Changelog

### Version 0.1.0 (2024-06-17)
- Initial release
- Core functionality for searching and collecting arXiv papers
- Zotero integration with metadata preservation
- AI-powered summarization support
- Command-line interface and Python API

---

Made with ❤️ by [Stepan Kropachev](https://github.com/StepanKropachev)
