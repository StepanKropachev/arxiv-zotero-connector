import aiohttp
import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from pyzotero import zotero
from typing import List, Dict, Optional, Tuple
import logging
import os
import requests
import re
import unicodedata
from credentials import load_credentials, CredentialsError

from arxiv_config import ARXIV_TO_ZOTERO_MAPPING
from metadata_config import MetadataMapper
from search_params import ArxivSearchParams
from pdf_manager import PDFManager
from arxiv_client import ArxivClient

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
    pass

@lru_cache(maxsize=32)

class ArxivZoteroCollector:
    def __init__(self, zotero_library_id: str, zotero_api_key: str, collection_key: str = None):
        """Initialize the collector with API clients and configurations"""
        self.zot = zotero.Zotero(zotero_library_id, 'user', zotero_api_key)
        self.collection_key = collection_key
        self.metadata_mapper = MetadataMapper(ARXIV_TO_ZOTERO_MAPPING)
        self.pdf_manager = PDFManager()
        self.arxiv_client = ArxivClient()
        
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
        """Validate collection existence"""
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

    async def _process_paper_async(self, paper: Dict, download_pdfs: bool = True) -> bool:
        """Process a single paper asynchronously"""
        try:
            # Create main Zotero item
            item_key = self.create_zotero_item(paper)
            if not item_key:
                return False

            # Add to collection if specified
            if self.collection_key and not self.add_to_collection(item_key):
                return False

            # Handle PDF attachment if requested
            if download_pdfs:
                pdf_path, filename = await self.pdf_manager.download_pdf(
                    url=paper['pdf_url'],
                    title=paper['title']
                )
                
            if pdf_path and filename:
                try:
                    # Create attachment item template using PDFManager
                    attachment = self.zot.item_template('attachment', 'imported_file')
                    attachment.update(
                        self.pdf_manager.prepare_attachment_template(
                            filename=filename,
                            parent_item=item_key,
                            filepath=pdf_path
                        )
                    )
                    
                    # Upload the attachment
                    result = self.zot.upload_attachments([attachment])
                    
                    # Check if the attachment was created
                    if result:
                        has_attachment = (
                            len(result.get('success', [])) > 0 or 
                            len(result.get('unchanged', [])) > 0
                        )
                        if has_attachment:
                            logger.info(f"Successfully processed PDF attachment for item {item_key}")
                            return True
                        elif len(result.get('failure', [])) > 0:
                            logger.error(f"Failed to upload attachment. Response: {result}")
                            return False
                        else:
                            logger.warning(f"Unexpected attachment result: {result}")
                            return False
                    else:
                        logger.error("No result returned from upload_attachments")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error creating/uploading attachment: {str(e)}")
                    return False
            else:
                logger.error("Failed to download PDF")
                return False
                
                # Download the PDF
                if await self._download_pdf_async(paper['pdf_url'], pdf_path):
                    try:
                        # Create attachment item template
                        attachment = self.zot.item_template('attachment', 'imported_file')
                        attachment.update({
                            'title': filename,
                            'parentItem': item_key,
                            'contentType': 'application/pdf',
                            'filename': str(pdf_path)  # Use full path
                        })
                        
                        # Upload the attachment
                        result = self.zot.upload_attachments([attachment])
                        
                        # Check if the attachment was created (it will be in either success, failure, or unchanged)
                        if result:
                            has_attachment = (
                                len(result.get('success', [])) > 0 or 
                                len(result.get('unchanged', [])) > 0
                            )
                            if has_attachment:
                                logger.info(f"Successfully processed PDF attachment for item {item_key}")
                                return True
                            elif len(result.get('failure', [])) > 0:
                                logger.error(f"Failed to upload attachment. Response: {result}")
                                return False
                            else:
                                logger.warning(f"Unexpected attachment result: {result}")
                                return False
                        else:
                            logger.error("No result returned from upload_attachments")
                            return False
                            
                    except Exception as e:
                        logger.error(f"Error creating/uploading attachment: {str(e)}")
                        return False
                else:
                    logger.error("Failed to download PDF")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error processing paper: {str(e)}")
            return False

    def search_arxiv(self, search_params: ArxivSearchParams) -> List[Dict]:
        """Search arXiv using provided search parameters"""
        return self.arxiv_client.search_arxiv(search_params)

    async def run_collection_async(self, search_params: ArxivSearchParams, download_pdfs: bool = True) -> Tuple[int, int]:
        """Run collection process asynchronously using search parameters"""
        try:
            papers = self.search_arxiv(search_params)
            logger.info(f"Found {len(papers)} papers matching the criteria")
            
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
        await self.pdf_manager.close()

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
        
        # Example usage with ArxivSearchParams
        search_params = ArxivSearchParams(
            keywords=["multi-agent systems"],
            max_results=10,
            categories=["cs.AI"]
        )
        
        successful, failed = await collector.run_collection_async(
            search_params=search_params,
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