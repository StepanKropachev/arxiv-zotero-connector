import arxiv
import aiohttp
import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import lru_cache
from pathlib import Path
from pyzotero import zotero
from typing import List, Dict, Optional, Tuple
import logging
import os
import pytz
import requests

from arxiv_config import ARXIV_TO_ZOTERO_MAPPING
from metadata_config import MetadataMapper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('arxiv_zotero.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ZoteroAPIError(Exception):
    """Custom exception for Zotero API errors"""

@lru_cache(maxsize=32)
def load_credentials(env_path: str = None) -> dict:
    """Load credentials from environment variables or .env file with caching"""
    try:
        if env_path and not os.path.exists(env_path):
            raise FileNotFoundError(f"Environment file not found: {env_path}")
        
        env_locations = [
            loc for loc in [
                env_path if env_path else None,
                '.env',
                Path.home() / '.arxiv-zotero' / '.env',
                Path('/etc/arxiv-zotero/.env')
            ] if loc and os.path.exists(loc)
        ]
        
        if env_locations:
            load_dotenv(env_locations[0])
            logger.info(f"Loaded environment from {env_locations[0]}")
        
        required_vars = ['ZOTERO_LIBRARY_ID', 'ZOTERO_API_KEY']
        credentials = {var: os.getenv(var) for var in required_vars}
        
        if None in credentials.values():
            missing = [k for k, v in credentials.items() if v is None]
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        return {
            'library_id': credentials['ZOTERO_LIBRARY_ID'],
            'api_key': credentials['ZOTERO_API_KEY'],
            'collection_key': os.getenv('COLLECTION_KEY')
        }
    except Exception as e:
        logger.error(f"Error loading credentials: {str(e)}")
        raise

class ArxivZoteroCollector:
    def __init__(self, zotero_library_id: str, zotero_api_key: str, collection_key: str = None):
        """Initialize the collector with optimized configurations"""
        self.zot = zotero.Zotero(zotero_library_id, 'user', zotero_api_key)
        self.collection_key = collection_key
        self.download_dir = Path.home() / 'Downloads' / 'arxiv_papers'
        self.metadata_mapper = MetadataMapper(ARXIV_TO_ZOTERO_MAPPING)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=20
        ))
        
        self.async_session = None
        self.request_times = deque(maxlen=10)
        self.min_request_interval = 0.1
        
        if collection_key:
            self._validate_collection()

    def _validate_collection(self):
        """Validate collection existence with caching"""
        try:
            collections = self.zot.collections()
            if not any(col['key'] == self.collection_key for col in collections):
                raise ValueError(f"Collection {self.collection_key} does not exist")
            logger.info(f"Successfully validated collection {self.collection_key}")
        except Exception as e:
            logger.error(f"Failed to validate collection {self.collection_key}: {str(e)}")
            raise

    def create_zotero_item(self, paper: Dict) -> Optional[str]:
        """Create a new item in Zotero using the metadata mapper"""
        try:
            template = self.zot.item_template('journalArticle')
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
            return None

    def add_to_collection(self, item_key: str) -> bool:
        """Add an item to the specified collection"""
        if not self.collection_key:
            return True

        try:
            item = self.zot.item(item_key)
            success = self.zot.addto_collection(self.collection_key, item)
            
            if success:
                logger.info(f"Successfully added item {item_key} to collection")
                return True
            else:
                logger.error(f"Failed to add item {item_key} to collection")
                return False

        except Exception as e:
            logger.error(f"Error adding to collection: {str(e)}")
            return False

    @staticmethod
    def _prepare_arxiv_metadata(result: arxiv.Result) -> Dict:
        """Optimized metadata preparation using dict comprehension"""
        try:
            authors = [author.name for author in getattr(result, 'authors', []) if hasattr(author, 'name')]
            
            arxiv_id = getattr(result, 'id', '') or (
                result.entry_id.split('/')[-1] if hasattr(result, 'entry_id') else ''
            )
            
            metadata = {
                'title': getattr(result, 'title', ''),
                'authors': authors,
                'arxiv_url': getattr(result, 'entry_id', ''),
                'abstract': getattr(result, 'summary', ''),
                'published': getattr(result, 'published', None),
                'arxiv_id': arxiv_id,
                'categories': getattr(result, 'categories', []),
                'primary_category': getattr(result, 'primary_category', None),
                'pdf_url': getattr(result, 'pdf_url', None),
                'doi': getattr(result, 'doi', None),
                'journal_ref': getattr(result, 'journal_ref', None),
                'comment': getattr(result, 'comment', None),
                'version': getattr(result, 'version', None),
                'license': getattr(result, 'license', None),
                'archive': 'arXiv',
                'libraryCatalog': 'arXiv.org'
            }
            
            return {k: v for k, v in metadata.items() if v is not None}
            
        except Exception as e:
            logger.error(f"Error preparing metadata for paper: {str(e)}")
            return {}

    async def _init_async_session(self):
        """Initialize async session if not exists"""
        if self.async_session is None:
            self.async_session = aiohttp.ClientSession()

    async def _download_paper_async(self, pdf_url: str, title: str) -> Optional[str]:
        """Asynchronous paper download"""
        try:
            await self._init_async_session()
            
            clean_title = "".join(x for x in title if x.isalnum() or x in (' ', '-', '_'))
            filepath = self.download_dir / f"{clean_title[:100]}.pdf"
            
            async with self.async_session.get(pdf_url) as response:
                if response.status == 200:
                    content = await response.read()
                    filepath.write_bytes(content)
                    logger.info(f"Successfully downloaded paper to {filepath}")
                    return str(filepath)
                else:
                    logger.error(f"Failed to download paper: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading paper: {str(e)}")
            return None

    def attach_pdf(self, item_key: str, pdf_path: str, max_retries: int = 3) -> bool:
        """Attach a PDF to a Zotero item with retries"""
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
                    asyncio.sleep(2 * retry_count)
                else:
                    logger.error("Failed to attach PDF after maximum retries")
                    return False

    async def _process_paper_async(self, paper: Dict, download_pdf: bool = True) -> bool:
        """Asynchronous paper processing"""
        try:
            item_key = self.create_zotero_item(paper)
            if not item_key:
                return False
                
            if self.collection_key:
                if not self.add_to_collection(item_key):
                    logger.warning(f"Failed to add item {item_key} to collection")
                
            if download_pdf and paper.get('pdf_url'):
                pdf_path = await self._download_paper_async(paper['pdf_url'], paper['title'])
                if pdf_path:
                    if not self.attach_pdf(item_key, pdf_path):
                        logger.warning(f"Failed to attach PDF for item {item_key}")
                        
            return True
            
        except Exception as e:
            logger.error(f"Error processing paper {paper['title']}: {str(e)}")
            return False

    def search_arxiv(self, keywords: List[str], max_results: int = 50, 
                    days_back: int = 7) -> List[Dict]:
        """Optimized arXiv search with parallel processing"""
        query = ' OR '.join(keywords)
        since_date = datetime.now(pytz.UTC) - timedelta(days=days_back)
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        papers = []
        client = arxiv.Client(
            page_size=100,
            delay_seconds=3,
            num_retries=5
        )
        
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for result in client.results(search):
                    paper_date = result.published.astimezone(pytz.UTC)
                    if paper_date >= since_date:
                        futures.append(
                            executor.submit(self._prepare_arxiv_metadata, result)
                        )
                
                for future in as_completed(futures):
                    paper_metadata = future.result()
                    if paper_metadata:
                        papers.append(paper_metadata)
                        
            return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv: {str(e)}")
            return []

    async def run_collection_async(self, keywords: List[str], max_results: int = 50,
                                 days_back: int = 7, download_pdfs: bool = True) -> Tuple[int, int]:
        """Asynchronous collection process"""
        try:
            papers = self.search_arxiv(keywords, max_results, days_back)
            logger.info(f"Found {len(papers)} papers matching your keywords")
            
            if not papers:
                return 0, 0
                
            successful = 0
            failed = 0
            
            async def process_paper(paper):
                nonlocal successful, failed
                try:
                    if await self._process_paper_async(paper, download_pdfs):
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"Error processing paper: {str(e)}")
                
            tasks = [process_paper(paper) for paper in papers]
            await asyncio.gather(*tasks)
                    
            logger.info(f"Collection complete. Successfully processed {successful} papers. Failed: {failed}")
            return successful, failed
            
        except Exception as e:
            logger.error(f"Error in run_collection: {str(e)}")
            return 0, 0
            
    async def close(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()
        if self.async_session:
            await self.async_session.close()

    def __del__(self):
        """Cleanup resources on deletion"""
        if self.session:
            self.session.close()

async def main():
    collector = None
    try:
        credentials = load_credentials()
        collector = ArxivZoteroCollector(
            zotero_library_id=credentials['library_id'],
            zotero_api_key=credentials['api_key'],
            collection_key=credentials['collection_key']
        )
        
        keywords = ["multi-agent systems"]
        successful, failed = await collector.run_collection_async(
            keywords=keywords,
            max_results=10,
            days_back=7,
            download_pdfs=True
        )
        
        logger.info(f"Script completed. Successfully processed: {successful}, Failed: {failed}")
        
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
    finally:
        if collector:
            await collector.close()
        
if __name__ == "__main__":
    asyncio.run(main())