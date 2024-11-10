import arxiv
import requests
from pyzotero import zotero
import os
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional, Tuple
import pytz
import logging
from pathlib import Path
from dotenv import load_dotenv
from metadata_config import MetadataMapper
from arxiv_config import ARXIV_TO_ZOTERO_MAPPING

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('arxiv_zotero.log')
    ]
)
logger = logging.getLogger(__name__)

class ZoteroAPIError(Exception):
    """Custom exception for Zotero API errors"""
    pass

def load_credentials(env_path: str = None) -> dict:
    """
    Load credentials from environment variables or .env file
    Returns a dictionary containing the credentials
    """
    try:
        # If env_path is provided, load from that file
        if env_path:
            if not os.path.exists(env_path):
                raise FileNotFoundError(f"Environment file not found: {env_path}")
            load_dotenv(env_path)
        else:
            # Try to load from default locations
            env_locations = [
                '.env',
                Path.home() / '.arxiv-zotero' / '.env',
                Path('/etc/arxiv-zotero/.env')
            ]
            
            for loc in env_locations:
                if os.path.exists(loc):
                    load_dotenv(loc)
                    logger.info(f"Loaded environment from {loc}")
                    break

        # Required credentials
        required_vars = ['ZOTERO_LIBRARY_ID', 'ZOTERO_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        return {
            'library_id': os.getenv('ZOTERO_LIBRARY_ID'),
            'api_key': os.getenv('ZOTERO_API_KEY'),
            'collection_key': os.getenv('COLLECTION_KEY')  # Optional
        }

    except Exception as e:
        logger.error(f"Error loading credentials: {str(e)}")
        raise

class ArxivZoteroCollector:
    def __init__(self, zotero_library_id: str, zotero_api_key: str, collection_key: str = None):
        """
        Initialize the collector with Zotero credentials and metadata mapper.
        """
        self.zot = zotero.Zotero(zotero_library_id, 'user', zotero_api_key)
        self.collection_key = collection_key
        self.download_dir = os.path.expanduser('~/Downloads/arxiv_papers')
        self.metadata_mapper = MetadataMapper(ARXIV_TO_ZOTERO_MAPPING)
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Validate collection exists if provided
        if collection_key:
            try:
                collections = self.zot.collections()
                collection_exists = any(col['key'] == collection_key for col in collections)
                if not collection_exists:
                    raise ValueError(f"Collection {collection_key} does not exist")
                logger.info(f"Successfully validated collection {collection_key}")
            except Exception as e:
                logger.error(f"Failed to validate collection {collection_key}: {str(e)}")
                raise

    def _prepare_arxiv_metadata(self, result: arxiv.Result) -> Dict:
        """
        Convert arxiv.Result into a metadata dictionary suitable for mapping.
        Handles missing fields gracefully and ensures all required fields are present.
        """
        try:
            # Extract authors while handling possible missing data
            authors = []
            for author in getattr(result, 'authors', []):
                try:
                    authors.append(author.name)
                except AttributeError:
                    continue

            # Get the arXiv ID from the entry_id URL if available
            arxiv_id = getattr(result, 'id', '')
            if not arxiv_id and hasattr(result, 'entry_id'):
                # Extract ID from URL like 'http://arxiv.org/abs/2311.xxxxx'
                arxiv_id = result.entry_id.split('/')[-1]

            return {
                # Basic metadata (required fields)
                'title': getattr(result, 'title', ''),
                'authors': authors,
                'arxiv_url': getattr(result, 'entry_id', ''),
                'abstract': getattr(result, 'summary', ''),
                'published': getattr(result, 'published', None),
                'arxiv_id': arxiv_id,
                
                # Additional metadata (optional fields)
                'categories': getattr(result, 'categories', []),
                'primary_category': getattr(result, 'primary_category', None),
                'pdf_url': getattr(result, 'pdf_url', None),
                'doi': getattr(result, 'doi', None),
                'journal_ref': getattr(result, 'journal_ref', None),
                'comment': getattr(result, 'comment', None),
                'version': getattr(result, 'version', None),
                'license': getattr(result, 'license', None),
                
                # Add fields that have default values in config
                'archive': 'arXiv',  # Match default_value in config
                'libraryCatalog': 'arXiv.org'  # Match default_value in config
            }
        except Exception as e:
            logger.error(f"Error preparing metadata for paper: {str(e)}")
            return {}

    def create_zotero_item(self, paper: Dict) -> Optional[str]:
        """
        Create a new item in Zotero using the metadata mapper.
        Returns item key if successful, None otherwise.
        """
        try:
            template = self.zot.item_template('journalArticle')
            
            # Map metadata using the configured mapper
            mapped_data = self.metadata_mapper.map_metadata(paper)
            template.update(mapped_data)

            response = self.zot.create_items([template])
            
            if 'successful' in response and response['successful']:
                item_key = list(response['successful'].values())[0]['key']
                logger.info(f"Successfully created item with key: {item_key}")
                return item_key
            else:
                logger.error(f"Failed to create Zotero item. Response: {response}")
                return None

        except Exception as e:
            logger.error(f"Error creating Zotero item: {str(e)}")
            logger.debug("", exc_info=True)
            return None

    def add_to_collection(self, item_key: str) -> bool:
        """Add an item to the specified collection."""
        if not self.collection_key:
            return True

        try:
            logger.info(f"Adding item {item_key} to collection {self.collection_key}")
            item = self.zot.item(item_key)
            success = self.zot.addto_collection(self.collection_key, item)
            
            if success:
                logger.info("Successfully added item to collection")
                return True
            else:
                logger.error("Failed to add to collection")
                return False

        except Exception as e:
            logger.error(f"Error adding to collection: {str(e)}")
            logger.debug("", exc_info=True)
            return False

    def download_paper(self, pdf_url: str, title: str) -> Optional[str]:
        """Download a paper from arXiv."""
        try:
            clean_title = "".join(x for x in title if x.isalnum() or x in (' ', '-', '_'))
            filename = f"{clean_title[:100]}.pdf"
            filepath = os.path.join(self.download_dir, filename)

            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            logger.info(f"Successfully downloaded paper to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error downloading paper: {str(e)}")
            logger.debug("", exc_info=True)
            return None

    def attach_pdf(self, item_key: str, pdf_path: str, max_retries: int = 3) -> bool:
        """Attach a PDF to a Zotero item with retries."""
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info(f"Attempting to attach PDF (attempt {retry_count + 1}/{max_retries})")
                self.zot.attachment_simple([pdf_path], item_key)
                logger.info("PDF attached successfully")
                return True

            except Exception as e:
                retry_count += 1
                logger.error(f"Error attaching PDF (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    time.sleep(2 * retry_count)  # Exponential backoff
                else:
                    logger.error("Failed to attach PDF after maximum retries")
                    return False

    def search_arxiv(self, keywords: List[str], max_results: int = 50, 
                    days_back: int = 7) -> List[Dict]:
        """Search arXiv for papers matching keywords within the specified timeframe."""
        query = ' OR '.join(keywords)
        since_date = datetime.now(pytz.UTC) - timedelta(days=days_back)

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        papers = []
        client = arxiv.Client()
        
        try:
            for result in client.results(search):
                paper_date = result.published.astimezone(pytz.UTC)
                if paper_date >= since_date:
                    paper_metadata = self._prepare_arxiv_metadata(result)
                    papers.append(paper_metadata)
            return papers

        except Exception as e:
            logger.error(f"Error searching arXiv: {str(e)}")
            logger.debug("", exc_info=True)
            return []

    def process_paper(self, paper: Dict, download_pdf: bool = True) -> bool:
        """Process a single paper - create item, add to collection, and attach PDF."""
        try:
            # Step 1: Create Zotero item
            item_key = self.create_zotero_item(paper)
            if not item_key:
                return False

            # Step 2: Add to collection
            if self.collection_key:
                collection_success = self.add_to_collection(item_key)
                if not collection_success:
                    logger.warning(f"Failed to add item {item_key} to collection, but item was created")

            # Step 3: Handle PDF if requested
            if download_pdf and paper.get('pdf_url'):
                pdf_path = self.download_paper(paper['pdf_url'], paper['title'])
                if pdf_path:
                    pdf_success = self.attach_pdf(item_key, pdf_path)
                    if not pdf_success:
                        logger.warning("Failed to attach PDF, but item was created")

            return True

        except Exception as e:
            logger.error(f"Error processing paper {paper['title']}: {str(e)}")
            logger.debug("", exc_info=True)
            return False

    def run_collection(self, keywords: List[str], max_results: int = 50, 
                      days_back: int = 7, download_pdfs: bool = True) -> Tuple[int, int]:
        """Run the complete collection process."""
        try:
            papers = self.search_arxiv(keywords, max_results, days_back)
            logger.info(f"Found {len(papers)} papers matching your keywords")

            successful = 0
            failed = 0

            for paper in papers:
                try:
                    logger.info(f"Processing paper: {paper['title']}")
                    if self.process_paper(paper, download_pdfs):
                        successful += 1
                    else:
                        failed += 1
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    failed += 1
                    logger.error(f"Error processing paper {paper['title']}: {str(e)}")
                    continue

            logger.info(f"Collection complete. Successfully processed {successful} papers. Failed: {failed}")
            return successful, failed

        except Exception as e:
            logger.error(f"Error in run_collection: {str(e)}")
            logger.debug("", exc_info=True)
            return 0, 0

if __name__ == "__main__":
    try:
        # Load credentials from environment
        credentials = load_credentials()
        
        # Initialize collector with loaded credentials
        collector = ArxivZoteroCollector(
            zotero_library_id=credentials['library_id'],
            zotero_api_key=credentials['api_key'],
            collection_key=credentials['collection_key']
        )
        
        # Define search parameters
        keywords = [
            "multi-agent systems"
        ]

        # Run collection
        successful, failed = collector.run_collection(
            keywords=keywords,
            max_results=50,
            days_back=7,
            download_pdfs=True
        )

        logger.info(f"Script completed. Successfully processed: {successful}, Failed: {failed}")

    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        logger.debug("", exc_info=True)