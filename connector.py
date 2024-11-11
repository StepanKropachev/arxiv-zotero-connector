import asyncio
from typing import List, Dict, Tuple
import logging
from credentials import load_credentials

from arxiv_config import ARXIV_TO_ZOTERO_MAPPING
from metadata_config import MetadataMapper
from search_params import ArxivSearchParams
from pdf_manager import PDFManager
from arxiv_client import ArxivClient
from zotero_client import ZoteroClient
from paper_processor import PaperProcessor

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
        self.paper_processor = PaperProcessor(
        self.zotero_client,
        self.metadata_mapper,
        self.pdf_manager
    )
        self.arxiv_client = ArxivClient()        
        self.async_session = None
        
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
                    if await self.paper_processor.process_paper(paper, download_pdfs):
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