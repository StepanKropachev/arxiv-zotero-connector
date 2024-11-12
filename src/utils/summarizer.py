import google.generativeai as genai
import logging
import time
from pathlib import Path
from typing import Optional, Dict
import PyPDF2
import asyncio

logger = logging.getLogger(__name__)

class PaperSummarizer:
    def __init__(self, api_key: str, config: Dict):
        """Initialize the summarizer with Gemini API key and configuration"""
        self.config = config.get('summarizer', {})
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.rate_limit_delay = self.config.get('rate_limit_delay', 60)  # Delay between requests in seconds
        self.last_request_time = 0
        
    async def _read_pdf(self, pdf_path: Path) -> str:
        """Read text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() + '\n'
                return text
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {str(e)}")
            return ''

    async def _enforce_rate_limit(self):
        """Enforce rate limiting between API requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit_delay:
            delay = self.rate_limit_delay - time_since_last_request
            await asyncio.sleep(delay)
        self.last_request_time = time.time()

    async def summarize(self, pdf_path: Path, zotero_client=None, item_key: Optional[str] = None) -> Optional[str]:
        """Summarize PDF content and optionally add to Zotero"""
        try:
            # Read PDF content
            text = await self._read_pdf(pdf_path)
            if not text:
                return None

            # Enforce rate limit
            await self._enforce_rate_limit()

            # Get summary prompt from config or use default
            prompt = self.config.get('prompt', 
                'Summarize this academic paper. Include: main objectives, methodology, key findings, and conclusions. Keep it concise.')
            max_length = self.config.get('max_length', 500)

            # Generate summary
            response = self.model.generate_content(
                f"{prompt}\n\nText: {text[:8000]}"  # Limit input text to avoid token limits
            )
            summary = response.text[:max_length]

            # Save summary to file
            summary_path = pdf_path.with_suffix('.summary.txt')
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"Summary of: {pdf_path.name}\n\n{summary}")

            # Add note to Zotero if client and item_key provided
            if zotero_client and item_key:
                note_template = zotero_client.zot.item_template('note')
                note_template['note'] = f"<p><strong>AI Generated Summary:</strong></p><p>{summary}</p>"
                note_template['parentItem'] = item_key
                zotero_client.zot.create_items([note_template])

            return summary

        except Exception as e:
            logger.error(f"Error summarizing paper: {str(e)}")
            return None