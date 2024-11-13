# 📚 ArXiv-Zotero Connector with AI Summarization

Automatically collect papers from ArXiv and organize them in your Zotero library with AI-powered paper summarization! Perfect for researchers, students, and academics who want to keep their paper collections and references organized.

## ✨ What Can It Do?

- 🔍 Search ArXiv papers using keywords, authors, or categories
- 📥 Automatically download PDFs
- 🤖 AI-powered summarization of papers
- 📝 Add papers to Zotero with complete metadata
- 📁 Organize papers into collections
- 📅 Filter papers by date range
- 🎯 Search specific types of content (journals, conference papers, preprints)

## 🚀 Quick Start Guide

### Step 1: Set Up Your Computer

1. Make sure you have Python installed (version 3.7 or newer)
   - Download from [Python's website](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"

2. Install Git if you don't have it
   - Download from [Git's website](https://git-scm.com/downloads)

### Step 2: Get Your Zotero Credentials 🔑

1. Get your Zotero Library ID:
   - Go to [Zotero Settings](https://www.zotero.org/settings/)
   - Click on "Feed Settings"
   - Your Library ID is the number in "Your user ID for use in API calls is XXXXXX"

2. Create your API Key:
   - Still in Zotero Settings, go to "API Settings"
   - Click "Create new private key"
   - Check all the permissions boxes
   - Click "Save Key"
   - Copy the key that appears - you'll need it later!

3. (Optional) Get a Collection Key:
   - Open your Zotero library in a web browser
   - Click on the collection (folder) you want to use
   - Look at the URL - the collection key is the last part (looks like "XXX1XXX0")

### Step 3: Install the Connector

Open your terminal/command prompt and run these commands:

```bash
# 1. Get the code
git clone https://github.com/StepanKropachev/Arxiv-Zotero-Connector.git
cd arxiv-zotero-connector

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the environment
# On Windows:
.\.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# 4. Install required packages
pip install -r requirements.txt
```

### Step 4: Set Up Your Credentials

1. Create a file named `.env` in the project folder
2. Add your credentials like this:
```
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_API_KEY=your_api_key
COLLECTION_KEY=your_collection_key  # Optional
```

## 📖 How to Use

### Method 1: Using Command Line (Easiest)

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

### Method 2: Using a Configuration File

1. Create a file named `my_search.yaml`:
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

2. Run using the config file:
```bash
python main.py --config my_search.yaml
```

### Method 3: Using Python Code

```python
from src.core.connector import ArxivZoteroCollector
from src.core.search_params import ArxivSearchParams
from src.utils.credentials import load_credentials

# Load your credentials
credentials = load_credentials()

# Create the collector
collector = ArxivZoteroCollector(
    zotero_library_id=credentials['library_id'],
    zotero_api_key=credentials['api_key'],
    collection_key=credentials['collection_key']  # Optional
)

# Set up your search
search_params = ArxivSearchParams(
    keywords=["artificial intelligence"],
    categories=["cs.AI"],
    max_results=10
)

# Run the collection
successful, failed = await collector.run_collection_async(
    search_params=search_params,
    download_pdfs=True
)
```

## 📝 Common Search Options

- `--keywords` or `-k`: Words to search for
- `--title` or `-t`: Search in paper titles only
- `--categories` or `-c`: ArXiv categories (like cs.AI, physics.comp-ph)
- `--author` or `-a`: Author name
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--max-results` or `-m`: Maximum number of papers to get
- `--no-pdf`: Skip downloading PDFs

## 🗂️ Popular ArXiv Categories

- `cs.AI`: Artificial Intelligence
- `cs.LG`: Machine Learning
- `cs.CL`: Computation and Language
- `cs.CV`: Computer Vision
- `physics.comp-ph`: Computational Physics
- `math.NA`: Numerical Analysis
- `q-bio`: Quantitative Biology

## 🤖 AI Paper Summarizer (Optional)

You can add a powerful AI summarization to your workflow! You can automatically generate summaries of your papers using Google's Gemini API and attach those to your collection items in Zotero.

### 🔑 Setting Up the Summarizer

1. Get your Gemini API Key:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add it to your `.env` file:
   
   ```
   GOOGLE_API_KEY=your_api_key
   ```

2. Configure summarization in `my_search.yaml`:
   ```yaml
   summarizer:
     enabled: true  # Turn summarization on/off
     prompt: "Your custom prompt here"
     max_length: 300  # Maximum summary length
     rate_limit_delay: 5  # Delay between API requests
   ```

### ⚙️ Advanced Summarizer Options

- `--summarizer-enabled`: Enable/disable summarization
- `--summarizer-prompt`: Custom prompt for the AI
- `--summary-length`: Maximum length of summaries
- `--rate-limit`: Time between API requests (seconds)

## 🔍 Example Use Cases

### Case 1: Literature Review
```bash
python main.py \
  --keywords "survey" "review" "deep learning" \
  --categories cs.AI cs.LG \
  --start-date 2023-01-01 \
  --content-type journal
```

### Case 2: Latest Research
```bash
python main.py \
  --keywords "transformer" "attention mechanism" \
  --categories cs.CL \
  --start-date 2024-01-01 \
  --max-results 20
```

### Case 3: Conference Papers
```bash
python main.py \
  --keywords "reinforcement learning" \
  --content-type conference \
  --start-date 2023-06-01 \
  --end-date 2024-01-01
```
### ✨ Summarizer Use Cases

#### Case 4: Simple Explanations
```bash
python main.py \
  --keywords "quantum computing" \
  --summarizer-prompt "Explain this research paper as if you're talking to a high school student" \
  --max-results 5
```

#### Case 5: Multilingual Summaries
```bash
python main.py \
  --keywords "machine learning" \
  --summarizer-prompt "Summarize this paper in Russian, focusing on methodology and results" \
  --max-results 3
```

#### Case 6: Social Media Briefs
```bash
python main.py \
  --keywords "artificial intelligence" "ethics" \
  --summarizer-prompt "Create a Twitter-style thread (5 tweets max) explaining the key findings" \
  --start-date 2024-01-01
```

## ❓ Troubleshooting

### Common Issues:

1. **"Command not found" error:**
   - Make sure you're in the right directory
   - Check if Python is installed correctly
   - Try using `python3` instead of `python`

2. **Credentials not working:**
   - Double-check your Library ID and API key
   - Make sure there are no spaces in your `.env` file
   - Check if your API key has the right permissions

3. **Downloads failing:**
   - Check your internet connection
   - Make sure you have enough disk space
   - Try reducing `max_results`

4. **Program seems stuck:**
   - ArXiv has rate limits
   - For large downloads, be patient
   - Try reducing `max_results`

### ⚠️ AI-summarizer Troubleshooting

1. **"API Key Invalid" error:**
   - Check if GEMINI_API_KEY is correctly set in .env
   - Verify API key permissions
   - Ensure key hasn't expired

2. **Rate Limit Issues:**
   - Increase rate_limit_delay in config
   - Process fewer papers at once
   - Check Gemini API quotas

3. **Summary Quality:**
   - Adjust your prompt for better results
   - Try different max_length values
   - Use more specific instructions

## 📫 Need Help?

- 🐛 Found a bug? Open an issue on GitHub
- 💡 Have a suggestion? I'd love to hear it!
- 🤝 Want to contribute? You're more then welcome!

## 📜 License

MIT License - Feel free to use and modify!