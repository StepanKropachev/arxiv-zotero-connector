from datetime import datetime
from typing import List, Optional

class ArxivSearchParams:
    """
    Data class for organizing arXiv search parameters
    
    Attributes:
        keywords (List[str]): List of general search keywords
        title_search (str): Specific term to search for in titles
        categories (List[str]): List of arXiv category codes (e.g., ["cs.AI", "cs.MA"])
        start_date (datetime): Start of date range for filtering
        end_date (datetime): End of date range for filtering
        author (str): Author name to search for
        content_type (str): Type of content to filter for ("journal", "conference", "preprint")
        max_results (int): Maximum number of results to return
    """
    
    def __init__(
        self,
        keywords: List[str] = None,
        title_search: str = None,
        categories: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        author: str = None,
        content_type: str = None,
        max_results: int = 50
    ):
        """
        Initialize search parameters
        
        Args:
            keywords: List of general search keywords
            title_search: Specific term to search for in titles
            categories: List of arXiv category codes
            start_date: Start of date range for filtering
            end_date: End of date range for filtering
            author: Author name to search for
            content_type: Type of content to filter for
            max_results: Maximum number of results to return
        """
        self.keywords = keywords or []
        self.title_search = title_search
        self.categories = categories or []
        self.start_date = start_date
        self.end_date = end_date
        self.author = author
        self.content_type = content_type
        self.max_results = max_results

    def build_query(self) -> str:
        """
        Build the arXiv query string based on search parameters
        
        Returns:
            str: Formatted arXiv API query string
        """
        query_parts = []
        
        # Add general keywords
        if self.keywords:
            query_parts.append('(' + ' OR '.join(self.keywords) + ')')
            
        # Add title search
        if self.title_search:
            query_parts.append(f'ti:"{self.title_search}"')
            
        # Add author search
        if self.author:
            query_parts.append(f'au:"{self.author}"')
            
        # Add category filters
        if self.categories:
            cat_query = ' OR '.join(f'cat:{cat}' for cat in self.categories)
            query_parts.append(f'({cat_query})')
            
        return ' AND '.join(query_parts) if query_parts else '*:*'

    def __str__(self) -> str:
        """String representation of search parameters"""
        params = []
        if self.keywords:
            params.append(f"keywords={self.keywords}")
        if self.title_search:
            params.append(f"title_search='{self.title_search}'")
        if self.categories:
            params.append(f"categories={self.categories}")
        if self.author:
            params.append(f"author='{self.author}'")
        if self.content_type:
            params.append(f"content_type='{self.content_type}'")
        if self.start_date:
            params.append(f"start_date={self.start_date.strftime('%Y-%m-%d')}")
        if self.end_date:
            params.append(f"end_date={self.end_date.strftime('%Y-%m-%d')}")
        params.append(f"max_results={self.max_results}")
        
        return f"ArxivSearchParams({', '.join(params)})"