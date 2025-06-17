#!/usr/bin/env python3
import asyncio
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import yaml
import pytz

from .core.connector import ArxivZoteroCollector
from .core.search_params import ArxivSearchParams
from .utils.credentials import load_credentials, CredentialsError
from .utils.summarizer import PaperSummarizer

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
        # Add timezone awareness to parsed date
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
        return parsed_date.replace(tzinfo=pytz.UTC)  # Make timezone-aware
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
        
def load_yaml_config(config_path: Path) -> dict:
    """Load search parameters from YAML configuration file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Error loading config file: {str(e)}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='ArXiv-Zotero Connector: Download and organize arXiv papers in Zotero'
    )

    parser.add_argument(
    '--config',
    type=Path,
    help='Path to YAML configuration file'
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

async def async_main():
    """Main entry point for the application"""
    args = parse_arguments()
    collector = None
    config_params = {}
    
    try:
        # Load credentials
        credentials = load_credentials(args.env_file)
        
        # Load YAML config if provided
        if args.config:
            config_params = load_yaml_config(args.config)

        summarizer = None
        if config_params.get('summarizer', {}).get('enabled'):
            summarizer = PaperSummarizer(
                api_key=credentials['gemini_api_key'],  # Add Gemini API key to credentials 
                config=config_params
            )
        
        # Initialize collector
        collector = ArxivZoteroCollector(
            zotero_library_id=credentials['library_id'],
            zotero_api_key=credentials['api_key'],
            collection_key=credentials['collection_key'],
            summarizer=summarizer,  # Pass summarizer to collector
            config=config_params
        )
        
        # Merge command line arguments with config file, preferring command line
        search_params = ArxivSearchParams(
            keywords=args.keywords or config_params.get('keywords'),
            title_search=args.title or config_params.get('title_search'),
            categories=args.categories or config_params.get('categories'),
            author=args.author or config_params.get('author'),
            start_date=args.start_date or parse_date(config_params.get('start_date')),
            end_date=args.end_date or parse_date(config_params.get('end_date')),
            content_type=args.content_type or config_params.get('content_type'),
            max_results=args.max_results if args.max_results != 50 else config_params.get('max_results', 50)
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



def main():
    """Main entry point for the CLI"""
    exit_code = asyncio.run(async_main())
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

