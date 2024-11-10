from typing import Dict, Any, Callable, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MetadataMapper:
    """
    A class to handle flexible mapping of source metadata to Zotero format
    """
    
    def __init__(self, mapping_config: Dict[str, Dict[str, Any]]):
        """
        Initialize with a mapping configuration
        
        Args:
            mapping_config: Dictionary containing field mappings and transformers
        """
        self.mapping_config = mapping_config

    def transform_creators(self, authors: List[str]) -> List[Dict[str, str]]:
        """Transform author names into Zotero creator format"""
        return [
            {
                'creatorType': 'author',
                'firstName': name.split()[0],
                'lastName': ' '.join(name.split()[1:])
            }
            for name in authors
        ]

    def transform_date(self, date: datetime) -> str:
        """Transform datetime to Zotero date format"""
        return date.strftime('%Y-%m-%d')

    def transform_tags(self, categories: List[str]) -> List[Dict[str, str]]:
        """Transform categories into Zotero tags format"""
        return [{'tag': cat} for cat in categories]

    def map_metadata(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map source metadata to Zotero format based on configuration
        
        Args:
            source_data: Source metadata dictionary
            
        Returns:
            Dict containing mapped metadata in Zotero format
        """
        try:
            mapped_data = {}
            
            for zotero_field, mapping in self.mapping_config.items():
                source_field = mapping['source_field']
                
                if source_field not in source_data:
                    if mapping.get('required', False):
                        raise ValueError(f"Required field '{source_field}' not found in source data")
                    continue

                value = source_data[source_field]
                
                # Apply transformer if specified
                if 'transformer' in mapping:
                    transformer = getattr(self, mapping['transformer'])
                    value = transformer(value)
                
                mapped_data[zotero_field] = value
            
            return mapped_data
            
        except Exception as e:
            logger.error(f"Error mapping metadata: {str(e)}")
            raise