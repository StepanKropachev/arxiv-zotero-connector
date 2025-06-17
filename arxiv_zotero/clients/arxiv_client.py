import arxiv
from datetime import datetime
import logging
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from typing import List, Dict, Optional

from ..core.search_params import ArxivSearchParams

logger = logging.getLogger(__name__)

class ArxivClient:
    """Class to handle all arXiv-specific operations"""
    
    def __init__(self):
        """Initialize the ArxivClient"""
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3,
            num_retries=5
        )

    def filter_by_date(self, result: arxiv.Result, start_date: Optional[datetime], end_date: Optional[datetime]) -> bool:
        """Filter arxiv result by date range"""
        if not (start_date or end_date):
            return True
            
        pub_date = result.published.astimezone(pytz.UTC)
        
        if start_date and pub_date < start_date:
            return False
        if end_date and pub_date > end_date:
            return False
            
        return True

    def filter_by_content_type(self, result: arxiv.Result, content_type: Optional[str]) -> bool:
        """Filter arxiv result by content type"""
        if not content_type:
            return True
            
        comment = getattr(result, 'comment', '') or ''
        journal_ref = getattr(result, 'journal_ref', '') or ''
        
        comment = comment.lower()
        journal_ref = journal_ref.lower()
        
        if content_type == 'journal':
            return bool(journal_ref and not ('preprint' in journal_ref or 'submitted' in journal_ref))
        elif content_type == 'conference':
            return bool('conference' in comment or 'proceedings' in comment or 
                    'conference' in journal_ref or 'proceedings' in journal_ref)
        elif content_type == 'preprint':
            return not bool(journal_ref)
            
        return True

    async def _prepare_arxiv_metadata(self, result: arxiv.Result) -> Optional[Dict]:
        """Prepare metadata from arxiv result"""
        try:
            return {
                'title': result.title,
                'abstract': result.summary,
                'authors': [author.name for author in result.authors],
                'published': result.published.strftime('%Y-%m-%d') if isinstance(result.published, datetime) else result.published,
                'arxiv_id': result.entry_id.split('/')[-1],
                'arxiv_url': result.entry_id,
                'pdf_url': result.pdf_url,
                'primary_category': result.primary_category,
                'categories': result.categories,
                'journal_ref': getattr(result, 'journal_ref', None),
                'doi': getattr(result, 'doi', None),
                'comment': getattr(result, 'comment', None)
            }
        except Exception as e:
            logger.error(f"Error preparing arxiv metadata: {str(e)}")
            return None

    def search_arxiv(self, search_params: ArxivSearchParams) -> List[Dict]:
        """Search arXiv using provided search parameters"""
        try:
            query = search_params.build_query()
            logger.info(f"Executing arXiv search with query: {query}")
            
            search = arxiv.Search(
                query=query,
                max_results=search_params.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            papers = []
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for result in self.client.results(search):
                    if not self.filter_by_date(result, search_params.start_date, search_params.end_date):
                        continue
                        
                    if not self.filter_by_content_type(result, search_params.content_type):
                        continue
                    
                    future = executor.submit(
                        asyncio.run,
                        self._prepare_arxiv_metadata(result)
                    )
                    futures.append(future)
                
                for future in as_completed(futures):
                    paper_metadata = future.result()
                    if paper_metadata:
                        papers.append(paper_metadata)
            
            logger.info(f"Found {len(papers)} papers matching the search criteria")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv: {str(e)}")
            return []
