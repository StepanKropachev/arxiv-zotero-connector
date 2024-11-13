# 📚 ArXiv-Zotero Connector with AI Summarization

Automatically collect papers from ArXiv and organize them in your Zotero library with AI-powered paper summarization! Perfect for researchers, students, and academics who want to keep their paper collections and references organized.

## ✨ Features

- 🔍 Search ArXiv papers using keywords, authors, or categories
- 📥 Automatically download PDFs
- 🤖 AI-powered summarization of papers
- 📝 Add papers to Zotero with complete metadata
- 📁 Organize papers into collections
- 📅 Filter papers by date range
- 🎯 Search specific types of content (journals, conference papers, preprints)

## 🚀 Getting Started

### 1️⃣ Set Up

1. Install Python (version 3.7 or newer)
   - Download from [Python's website](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. Install Git
   - Download from [Git's website](https://git-scm.com/downloads)

### 2️⃣ Get Your Zotero Credentials 🔑

1. Get your Zotero Library ID:
   - Visit [Zotero Settings](https://www.zotero.org/settings/)
   - Navigate to "Feed Settings"
   - Find "Your user ID for use in API calls is XXXXXX"

2. Create your API Key:
   - In Zotero Settings, go to "API Settings"
   - Click "Create new private key"
   - Enable all permissions
   - Click "Save Key"
   - Copy the generated key

3. (Optional) Get a Collection Key:
   - Open your Zotero library in a web browser
   - Select the desired collection (folder)
   - The collection key is the last part of the URL (format: "XXX1XXX0")

### 3️⃣ Install the Connector

Open your terminal/command prompt and run:

```bash
# 1. Clone the repository
git clone https://github.com/StepanKropachev/arxiv-zotero-connector.git
cd arxiv-zotero-connector

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the environment
# On Windows:
.\.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### 4️⃣ Configure Your Credentials

1. Create a `.env` file in the project folder
2. Add your credentials:
```
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_API_KEY=your_api_key
COLLECTION_KEY=your_collection_key  # Optional
```

## 📖 Usage Methods

### 1️⃣ Command Line Interface (CLI)

Search for papers about "machine learning" in computer science:
```bash
python main.py --keywords "machine learning" --categories cs.AI --max-results 10
```

Search for recent papers by a specific author:
```bash
python main.py --author "John Smith" --start-date 2024-01-01
```

Download papers without PDFs:
```bash
python main.py --keywords "deep learning" --no-pdf
```

### 2️⃣ Configuration File

1. Create `my_search.yaml`:
```yaml
keywords:
  - "reinforcement learning"
  - "deep learning"
categories:
  - "cs.AI"
  - "cs.LG"
max_results: 20
start_date: "2024-01-01"
```

2. Run with config:
```bash
python main.py --config my_search.yaml
```

### 3️⃣ Python API

```python
from src.core.connector import ArxivZoteroCollector
from src.core.search_params import ArxivSearchParams
from src.utils.credentials import load_credentials

# Load credentials
credentials = load_credentials()

# Create collector
collector = ArxivZoteroCollector(
    zotero_library_id=credentials['library_id'],
    zotero_api_key=credentials['api_key'],
    collection_key=credentials['collection_key']  # Optional
)

# Configure search
search_params = ArxivSearchParams(
    keywords=["artificial intelligence"],
    categories=["cs.AI"],
    max_results=10
)

# Run collection
successful, failed = await collector.run_collection_async(
    search_params=search_params,
    download_pdfs=True
)
```

## 🎛️ Search Options

- `--keywords` or `-k`: Search terms
- `--title` or `-t`: Search in titles only
- `--categories` or `-c`: ArXiv categories
- `--author` or `-a`: Author name
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--max-results` or `-m`: Maximum papers to retrieve
- `--no-pdf`: Skip PDF downloads

## 📑 Popular ArXiv Categories

- `cs.AI`: Artificial Intelligence
- `cs.LG`: Machine Learning
- `cs.CL`: Computation and Language
- `cs.CV`: Computer Vision
- `physics.comp-ph`: Computational Physics
- `math.NA`: Numerical Analysis
- `q-bio`: Quantitative Biology

## 🤖 AI Paper Summarizer

### 🔑 Setup Instructions

1. Get your Gemini API Key:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add to `.env`:
   ```
   GOOGLE_API_KEY=your_api_key
   ```

2. Configure in `my_search.yaml`:
   ```yaml
   summarizer:
     enabled: true
     prompt: "Your custom prompt here"
     max_length: 300
     rate_limit_delay: 5
   ```

### ⚙️ Summarizer Options

- `--summarizer-enabled`: Toggle summarization
- `--summarizer-prompt`: Custom AI prompt
- `--summary-length`: Maximum summary length
- `--rate-limit`: API request delay (seconds)

## 🎯 Example Use Cases

### 📚 Research Examples

#### Literature Review
```bash
python main.py \
  --keywords "survey" "review" "deep learning" \
  --categories cs.AI cs.LG \
  --start-date 2023-01-01 \
  --content-type journal
```

#### Latest Research
```bash
python main.py \
  --keywords "transformer" "attention mechanism" \
  --categories cs.CL \
  --start-date 2024-01-01 \
  --max-results 20
```

#### Conference Papers
```bash
python main.py \
  --keywords "reinforcement learning" \
  --content-type conference \
  --start-date 2023-06-01 \
  --end-date 2024-01-01
```

### 🤖 Summarizer Examples

#### Simple Explanations
```bash
python main.py \
  --keywords "quantum computing" \
  --summarizer-prompt "Explain this research paper as if you're talking to a high school student" \
  --max-results 5
```

#### Multilingual Summaries
```bash
python main.py \
  --keywords "machine learning" \
  --summarizer-prompt "Summarize this paper in Russian, focusing on methodology and results" \
  --max-results 3
```

#### Social Media Briefs
```bash
python main.py \
  --keywords "artificial intelligence" "ethics" \
  --summarizer-prompt "Create a Twitter-style thread (5 tweets max) explaining the key findings" \
  --start-date 2024-01-01
```

## ❓ Troubleshooting

### 🔧 Common Issues

#### Command Line Issues
- **"Command not found" error:**
  - Verify correct directory
  - Confirm Python installation
  - Try `python3` instead of `python`

#### Authentication Issues
- **Credentials not working:**
  - Verify Library ID and API key
  - Check `.env` file formatting
  - Confirm API permissions

#### Download Issues
- **Downloads failing:**
  - Check internet connection
  - Verify available disk space
  - Reduce `max_results`

#### Performance Issues
- **Program seems slow:**
  - Consider ArXiv rate limits
  - Be patient with large downloads
  - Reduce `max_results`

### 🤖 AI Summarizer Issues

#### API Issues
- **"API Key Invalid" error:**
  - Verify GEMINI_API_KEY in `.env`
  - Check API key permissions
  - Confirm key validity

#### Rate Limiting
- **Rate Limit Issues:**
  - Increase `rate_limit_delay`
  - Reduce batch size
  - Monitor API quotas

#### Output Quality
- **Summary Quality:**
  - Refine prompts
  - Adjust `max_length`
  - Use specific instructions

## 📫 Support

- 🐛 Report bugs via GitHub Issues
- 💡 Share suggestions for improvement
- 🤝 Contributions welcome!

## 📜 License

MIT License - Free to use and modify!
