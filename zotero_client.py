from collections import deque
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from pyzotero import zotero
from typing import List, Dict, Optional, Tuple
import logging
import requests
import time

logger = logging.getLogger(__name__)

class ZoteroAPIError(Exception):
    """Custom exception for Zotero API errors"""
    pass

class ZoteroClient:
    """Class to handle all Zotero-specific operations"""
    
    def __init__(self, library_id: str, api_key: str, collection_key: str = None):
        """
        Initialize the Zotero client
        
        Args:
            library_id: Zotero library identifier
            api_key: Zotero API key
            collection_key: Optional collection key to add items to
        """
        self.zot = zotero.Zotero(library_id, 'user', api_key)
        self.collection_key = collection_key
        
        # Configure HTTP session for better performance
        self.session = requests.Session()
        self.session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=20
        ))
        
        # Rate limiting support
        self.request_times = deque(maxlen=10)
        self.min_request_interval = 0.1
        
        if collection_key:
            self._validate_collection()

    def _validate_collection(self):
        """
        Validate that the specified collection exists
        
        Raises:
            ValueError: If collection does not exist
        """
        try:
            collections = self.zot.collections()
            if not any(col['key'] == self.collection_key for col in collections):
                raise ValueError(f"Collection {self.collection_key} does not exist")
            logger.info(f"Successfully validated collection {self.collection_key}")
        except Exception as e:
            logger.error(f"Failed to validate collection {self.collection_key}: {str(e)}")
            raise

    def create_item(self, template_type: str, metadata: Dict) -> Optional[str]:
        """
        Create a new item in Zotero
        
        Args:
            template_type: Type of Zotero item ('journalArticle', 'attachment', etc.)
            metadata: Mapped metadata to apply to the template
            
        Returns:
            Optional[str]: Item key if successful, None otherwise
        """
        try:
            template = self.zot.item_template(template_type)
            template.update(metadata)

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
            raise ZoteroAPIError(f"Failed to create Zotero item: {str(e)}")

    def add_to_collection(self, item_key: str) -> bool:
        """
        Add an item to the specified collection
        
        Args:
            item_key: Key of the item to add
            
        Returns:
            bool: True if successful, False otherwise
        """
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
            raise ZoteroAPIError(f"Failed to add item to collection: {str(e)}")

    def upload_attachment(self, parent_key: str, filepath: Path, filename: str) -> bool:
        """
        Upload a file attachment to a Zotero item
        
        Args:
            parent_key: Key of the parent item
            filepath: Path to the file to upload
            filename: Name to use for the uploaded file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create attachment item template
            attachment = self.zot.item_template('attachment', 'imported_file')
            attachment.update({
                'title': filename,
                'parentItem': parent_key,
                'contentType': 'application/pdf',
                'filename': str(filepath)
            })
            
            # Upload the attachment
            result = self.zot.upload_attachments([attachment])
            
            # Check if the attachment was created
            if result:
                has_attachment = (
                    len(result.get('success', [])) > 0 or 
                    len(result.get('unchanged', [])) > 0
                )
                if has_attachment:
                    logger.info(f"Successfully uploaded attachment for item {parent_key}")
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
            logger.error(f"Error uploading attachment: {str(e)}")
            raise ZoteroAPIError(f"Failed to upload attachment: {str(e)}")

    def check_duplicate(self, identifier: str, identifier_field: str = 'DOI') -> Optional[str]:
        """
        Check if an item already exists in the library
        
        Args:
            identifier: Value to search for (DOI, arXiv ID, etc.)
            identifier_field: Field to search in
            
        Returns:
            Optional[str]: Item key if found, None otherwise
        """
        try:
            query = f'{identifier_field}:"{identifier}"'
            results = self.zot.items(q=query)
            
            if results:
                return results[0]['key']
            return None

        except Exception as e:
            logger.error(f"Error checking for duplicate: {str(e)}")
            return None

    def delete_item(self, item_key: str) -> bool:
        """
        Delete an item from the library
        
        Args:
            item_key: Key of the item to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.zot.delete_item(item_key)
            logger.info(f"Successfully deleted item {item_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting item: {str(e)}")
            return False

    def create_collection(self, name: str, parent_collection: str = None) -> Optional[str]:
        """
        Create a new collection
        
        Args:
            name: Name of the collection
            parent_collection: Optional parent collection key
            
        Returns:
            Optional[str]: Collection key if successful, None otherwise
        """
        try:
            collections = self.zot.create_collections([{
                'name': name,
                'parentCollection': parent_collection
            }])
            
            if collections:
                collection_key = collections['successful']['0']['key']
                logger.info(f"Successfully created collection: {collection_key}")
                return collection_key
            return None

        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            return None

    def close(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()

    def __del__(self):
        """Cleanup resources on deletion"""
        self.close()