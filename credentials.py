from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
import logging
import os

logger = logging.getLogger(__name__)

class CredentialsError(Exception):
    """Custom exception for credential loading errors"""
    pass

@lru_cache(maxsize=32)
def load_credentials(env_path: str = None) -> dict:
    """
    Load credentials from environment variables or .env file with caching
    
    Args:
        env_path (str, optional): Path to the environment file. Defaults to None.
        
    Returns:
        dict: Dictionary containing the loaded credentials
        
    Raises:
        FileNotFoundError: If the specified env_path doesn't exist
        CredentialsError: If required credentials are missing or there's an error loading them
    """
    try:
        if env_path and not os.path.exists(env_path):
            raise FileNotFoundError(f"Environment file not found: {env_path}")
        
        # Define potential environment file locations in order of preference
        env_locations = [
            loc for loc in [
                env_path if env_path else None,
                '.env',
                Path.home() / '.arxiv-zotero' / '.env',
                Path('/etc/arxiv-zotero/.env')
            ] if loc and os.path.exists(loc)
        ]
        
        # Load the first available environment file
        if env_locations:
            load_dotenv(env_locations[0])
            logger.info(f"Loaded environment from {env_locations[0]}")
        else:
            logger.warning("No environment file found, attempting to load from environment variables")
        
        # Check for required variables
        required_vars = ['ZOTERO_LIBRARY_ID', 'ZOTERO_API_KEY']
        credentials = {var: os.getenv(var) for var in required_vars}
        
        # Validate required credentials
        if None in credentials.values():
            missing = [k for k, v in credentials.items() if v is None]
            raise CredentialsError(f"Missing required environment variables: {', '.join(missing)}")
            
        # Return credentials including optional collection_key
        return {
            'library_id': credentials['ZOTERO_LIBRARY_ID'],
            'api_key': credentials['ZOTERO_API_KEY'],
            'collection_key': os.getenv('COLLECTION_KEY')
        }
        
    except Exception as e:
        logger.error(f"Error loading credentials: {str(e)}")
        if isinstance(e, (FileNotFoundError, CredentialsError)):
            raise
        raise CredentialsError(f"Failed to load credentials: {str(e)}")