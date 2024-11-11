import aiohttp
import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import os
import re
import unicodedata
from credentials import load_credentials, CredentialsError

from arxiv_config import ARXIV_TO_ZOTERO_MAPPING
from metadata_config import MetadataMapper
from search_params import ArxivSearchParams
from pdf_manager import PDFManager
from arxiv_client import ArxivClient
from zotero_client import ZoteroClient, ZoteroAPIError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('arxiv_zotero.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ArxivZoteroCollector:
    def __init__(self, zotero_library_id: str, zotero_api_key: str, collection_key: str = None):
        self.collection_key = collection_key
        self.zotero_client = ZoteroClient(zotero_library_id, zotero_api_key, collection_key)
        self.metadata_mapper = MetadataMapper(ARXIV_TO_ZOTERO_MAPPING)
        self.pdf_manager = PDFManager()
        self.arxiv_client = ArxivClient()        
        self.async_session = None

    def create_zotero_item(self, paper: Dict) -> Optional[str]:
        try:
            mapped_data = self.metadata_mapper.map_metadata(paper)
            return self.zotero_client.create_item('journalArticle', mapped_data)
        except ZoteroAPIError as e:
            logger.error(f"Error creating Zotero item: {str(e)}")
            return None

    def add_to_collection(self, item_key: str) -> bool:
        try:
            return self.zotero_client.add_to_collection(item_key)
        except ZoteroAPIError as e:
            logger.error(f"Error adding to collection: {str(e)}")
            return False

    async def _process_paper_async(self, paper: Dict, download_pdfs: bool = True) -> bool:
        """Process a single paper asynchronously"""
        try:
            # Create main Zotero item
            item_key = self.create_zotero_item(paper)
            if not item_key:
                logger.error("Failed to create main Zotero item")
                return False

            # Add to collection if specified
            if self.collection_key and not self.add_to_collection(item_key):
                logger.error(f"Failed to add item {item_key} to collection")
                # Consider if you want to delete the created item here
                return False

            # Handle PDF attachment if requested
            if download_pdfs:
                try:
                    # Download PDF
                    pdf_path, filename = await self.pdf_manager.download_pdf(
                        url=paper['pdf_url'],
                        title=paper['title']
                    )
                    
                    if not pdf_path or not filename:
                        logger.error("Failed to download PDF")
                        return False
                    
                    # Create and upload attachment
                    attachment_template = self.zotero_client.zot.item_template('attachment', 'imported_file')
                    attachment_template.update(
                        self.pdf_manager.prepare_attachment_template(
                            filename=filename,
                            parent_item=item_key,
                            filepath=pdf_path
                        )
                    )
                    
                    # Upload the attachment
                    result = self.zotero_client.zot.upload_attachments([attachment_template])
                    
                    if not result:
                        logger.error("No result returned from upload_attachments")
                        return False
                    
                    # Check attachment creation status
                    has_attachment = (
                        len(result.get('success', [])) > 0 or 
                        len(result.get('unchanged', [])) > 0
                    )
                    
                    if not has_attachment:
                        if len(result.get('failure', [])) > 0:
                            logger.error(f"Failed to upload attachment. Response: {result}")
                        else:
                            logger.warning(f"Unexpected attachment result: {result}")
                        return False
                    
                    logger.info(f"Successfully processed PDF attachment for item {item_key}")
                    
                except Exception as e:
                    logger.error(f"Error in PDF processing: {str(e)}")
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
        if self.async_session:
            await self.async_session.close()
        self.zotero_client.close()
        await self.pdf_manager.close()

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