import aiohttp
import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class PDFManager:
    """Class to handle all PDF-related operations for arXiv papers"""
    
    def __init__(self, download_dir: Path = None):
        """
        Initialize PDFManager
        
        Args:
            download_dir: Directory to save PDFs. Defaults to ~/Downloads/arxiv_papers
        """
        self.download_dir = download_dir or Path.home() / 'Downloads' / 'arxiv_papers'
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.async_session = None
        
    def _sanitize_filename(self, title: str, max_length: int = 100) -> str:
        """
        Convert paper title to a safe filename while preserving original casing.
        
        Args:
            title: Paper title to convert
            max_length: Maximum length of the resulting filename
                
        Returns:
            str: Sanitized filename
        """
        # Normalize unicode characters
        filename = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode()
        
        # Replace non-alphanumeric characters with spaces, preserving case
        filename = re.sub(r'[^\w\s-]', ' ', filename)
        
        # Replace multiple spaces with single space and strip
        filename = ' '.join(filename.split())
        
        # Truncate if too long, but try to break at word boundary
        if len(filename) > max_length:
            filename = filename[:max_length]
            last_space = filename.rfind(' ')
            if last_space > max_length * 0.8:  # Only truncate at space if it's not too short
                filename = filename[:last_space]
        
        # Replace problematic characters (if any remain) with safe alternatives
        filename = filename.replace('/', '-').replace('\\', '-')
        
        return filename

    def get_unique_filepath(self, title: str) -> Path:
        """
        Generate a unique filepath for a paper PDF.
        
        Args:
            title: Paper title
            
        Returns:
            Path: Unique filepath for the PDF
        """
        filename = f"{self._sanitize_filename(title)}.pdf"
        pdf_path = self.download_dir / filename
        
        # If file already exists, add a number suffix
        counter = 1
        while pdf_path.exists():
            filename = f"{self._sanitize_filename(title)} ({counter}).pdf"
            pdf_path = self.download_dir / filename
            counter += 1
            
        return pdf_path

    async def download_pdf(self, url: str, title: str) -> Tuple[Optional[Path], Optional[str]]:
        """
        Download a PDF file and return its path and filename.
        
        Args:
            url: URL of the PDF to download
            title: Title of the paper (for filename generation)
            
        Returns:
            Tuple[Optional[Path], Optional[str]]: Tuple of (file path, filename) if successful,
                                                (None, None) if download fails
        """
        if not self.async_session:
            self.async_session = aiohttp.ClientSession()

        try:
            pdf_path = self.get_unique_filepath(title)
            
            async with self.async_session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    pdf_path.write_bytes(content)
                    logger.info(f"Successfully downloaded PDF to {pdf_path}")
                    return pdf_path, pdf_path.name
                else:
                    logger.error(f"Failed to download PDF. Status: {response.status}")
                    return None, None

        except Exception as e:
            logger.error(f"Error downloading PDF: {str(e)}")
            return None, None

    def prepare_attachment_template(self, filename: str, parent_item: str, filepath: Path) -> dict:
        """
        Prepare a Zotero attachment item template.
        
        Args:
            filename: Name of the PDF file
            parent_item: Key of the parent Zotero item
            filepath: Full path to the PDF file
            
        Returns:
            dict: Zotero attachment item template
        """
        return {
            'title': filename,
            'parentItem': parent_item,
            'contentType': 'application/pdf',
            'filename': str(filepath)
        }

    async def close(self):
        """Cleanup resources"""
        if self.async_session:
            await self.async_session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()