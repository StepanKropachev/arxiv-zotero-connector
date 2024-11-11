#!/usr/bin/env python3
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.connector import ArxivZoteroCollector
from src.core.search_params import ArxivSearchParams
from src.utils.credentials import load_credentials, CredentialsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('arxiv_zotero.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string in YYYY-MM-DD format"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='ArXiv-Zotero Connector: Download and organize arXiv papers in Zotero'
    )
    
    # Search parameters
    parser.add_argument(
        '--keywords', '-k',
        nargs='+',
        help='Keywords to search for (space-separated)'
    )
    parser.add_argument(
        '--title', '-t',
        help='Search specifically in paper titles'
    )
    parser.add_argument(
        '--categories', '-c',
        nargs='+',
        help='arXiv categories to search in (e.g., cs.AI cs.MA)'
    )
    parser.add_argument(
        '--author', '-a',
        help='Author name to search for'
    )
    parser.add_argument(
        '--start-date',
        type=parse_date,
        help='Start date for papers (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=parse_date,
        help='End date for papers (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--content-type',
        choices=['journal', 'conference', 'preprint'],
        help='Type of content to filter for'
    )
    parser.add_argument(
        '--max-results', '-m',
        type=int,
        default=50,
        help='Maximum number of results to retrieve (default: 50)'
    )
    
    # Application settings
    parser.add_argument(
        '--env-file',
        type=Path,
        help='Path to .env file containing credentials'
    )
    parser.add_argument(
        '--no-pdf',
        action='store_true',
        help='Skip downloading PDFs'
    )
    
    return parser.parse_args()

async def main():
    """Main entry point for the application"""
    args = parse_arguments()
    collector = None
    
    try:
        # Load credentials
        credentials = load_credentials(args.env_file)
        
        # Initialize collector
        collector = ArxivZoteroCollector(
            zotero_library_id=credentials['library_id'],
            zotero_api_key=credentials['api_key'],
            collection_key=credentials['collection_key']
        )
        
        # Create search parameters
        search_params = ArxivSearchParams(
            keywords=args.keywords,
            title_search=args.title,
            categories=args.categories,
            author=args.author,
            start_date=args.start_date,
            end_date=args.end_date,
            content_type=args.content_type,
            max_results=args.max_results
        )
        
        # Run collection process
        successful, failed = await collector.run_collection_async(
            search_params=search_params,
            download_pdfs=not args.no_pdf
        )
        
        logger.info(f"Collection complete. Successfully processed: {successful}, Failed: {failed}")
        
    except CredentialsError as e:
        logger.error(f"Credential error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        return 1
    finally:
        if collector:
            await collector.close()
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)