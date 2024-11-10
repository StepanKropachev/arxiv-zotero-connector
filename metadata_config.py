from typing import Dict, Any, Callable, List, Union, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

class MetadataMapper:
    """
    An enhanced class to handle flexible mapping of arXiv metadata to Zotero format
    """
    
    def __init__(self, mapping_config: Dict[str, Dict[str, Any]]):
        """
        Initialize with a mapping configuration
        
        Args:
            mapping_config: Dictionary containing field mappings and transformers
        """
        self.mapping_config = mapping_config

    def transform_creators(self, authors: List[str]) -> List[Dict[str, str]]:
        """
        Transform author names into Zotero creator format with improved name parsing
        """
        creators = []
        for name in authors:
            # Handle cases with 'and' in author names
            if ' and ' in name:
                names = name.split(' and ')
            else:
                names = [name]
                
            for author in names:
                # Remove extra whitespace
                author = ' '.join(author.split())
                
                # Try to intelligently split the name
                if ',' in author:  # Last, First format
                    last, first = author.split(',', 1)
                    creators.append({
                        'creatorType': 'author',
                        'firstName': first.strip(),
                        'lastName': last.strip()
                    })
                else:  # First Last format
                    parts = author.split()
                    if len(parts) > 1:
                        creators.append({
                            'creatorType': 'author',
                            'firstName': ' '.join(parts[:-1]),
                            'lastName': parts[-1]
                        })
                    else:
                        creators.append({
                            'creatorType': 'author',
                            'firstName': '',
                            'lastName': author
                        })
        
        return creators

    def transform_date(self, date: datetime) -> str:
        """Transform datetime to Zotero date format"""
        return date.strftime('%Y-%m-%d')

    def transform_tags(self, categories: List[str]) -> List[Dict[str, str]]:
        """Transform categories into Zotero tags format with category cleaning"""
        return [{'tag': cat.strip().lower()} for cat in categories if cat.strip()]

    def clean_latex_markup(self, text: str) -> str:
        """
        Clean common LaTeX markup from text while preserving meaning
        """
        if not text:
            return text
            
        # Common LaTeX replacements
        replacements = {
            r'\n': ' ',  # Replace newlines with spaces
            r'\s+': ' ',  # Normalize multiple spaces
            r'\\textit\{([^}]*)\}': r'\1',  # Replace \textit{} with content
            r'\\textbf\{([^}]*)\}': r'\1',  # Replace \textbf{} with content
            r'\\emph\{([^}]*)\}': r'\1',  # Replace \emph{} with content
            r'\\cite\{[^}]*\}': '',  # Remove citations
            r'\\[a-zA-Z]+\{([^}]*)\}': r'\1',  # Remove other common LaTeX commands
            r'\$([^$]*)\$': r'\1',  # Remove inline math delimiters
        }
        
        cleaned = text
        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned)
            
        return cleaned.strip()

    def extract_journal_abbrev(self, journal_ref: Optional[str]) -> Optional[str]:
        """Extract journal abbreviation from journal reference"""
        if not journal_ref:
            return None
            
        # Common journal abbreviations mapping
        abbreviations = {
            'Physical Review': 'Phys. Rev.',
            'Physical Review Letters': 'Phys. Rev. Lett.',
            'Journal of High Energy Physics': 'JHEP',
            # Add more as needed
        }
        
        for full_name, abbrev in abbreviations.items():
            if full_name in journal_ref:
                return abbrev
                
        return None

    def extract_journal_name(self, journal_ref: Optional[str]) -> Optional[str]:
        """Extract full journal name from journal reference"""
        if not journal_ref:
            return None
            
        # Try to extract journal name (assuming format: "Journal Name Volume (Year) Pages")
        match = re.match(r'^([^0-9]+)', journal_ref)
        if match:
            return match.group(1).strip()
        return None

    def extract_volume(self, journal_ref: Optional[str]) -> Optional[str]:
        """Extract volume number from journal reference"""
        if not journal_ref:
            return None
            
        # Try to extract volume (assuming format: "Journal Name Volume (Year) Pages")
        match = re.search(r'(\d+)\s*\(', journal_ref)
        if match:
            return match.group(1)
        return None

    def extract_issue(self, journal_ref: Optional[str]) -> Optional[str]:
        """Extract issue number from journal reference"""
        if not journal_ref:
            return None
            
        # Try to extract issue (assuming format: "Journal Name Volume.Issue (Year) Pages")
        match = re.search(r'(\d+)\.(\d+)', journal_ref)
        if match:
            return match.group(2)
        return None

    def extract_pages(self, journal_ref: Optional[str]) -> Optional[str]:
        """Extract page numbers from journal reference"""
        if not journal_ref:
            return None
            
        # Try to extract pages (assuming format: "Journal Name Volume (Year) Pages")
        match = re.search(r'\)\s*(\d+(?:-\d+)?)', journal_ref)
        if match:
            return match.group(1)
        return None

    def transform_extra(self, extra_fields: Dict[str, Any]) -> str:
        """Transform extra fields into a formatted string"""
        extra_parts = []
        
        if 'comment' in extra_fields:
            extra_parts.append(f"Comment: {extra_fields['comment']}")
        if 'version' in extra_fields:
            extra_parts.append(f"Version: v{extra_fields['version']}")
            
        return '\n'.join(extra_parts)

    def get_current_date(self, _: Any = None) -> str:
        """Get current date in Zotero format"""
        return datetime.now().strftime('%Y-%m-%d')

    def map_metadata(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map source metadata to Zotero format based on configuration with enhanced error handling
        
        Args:
            source_data: Source metadata dictionary
            
        Returns:
            Dict containing mapped metadata in Zotero format
        """
        try:
            mapped_data = {}
            
            for zotero_field, mapping in self.mapping_config.items():
                try:
                    source_field = mapping['source_field']
                    
                    # Handle fields with default values
                    if source_field is None and 'default_value' in mapping:
                        mapped_data[zotero_field] = mapping['default_value']
                        continue
                    
                    # Handle multiple source fields
                    if isinstance(source_field, list):
                        value = {field: source_data.get(field) for field in source_field}
                    else:
                        if source_field not in source_data:
                            if mapping.get('required', False):
                                raise ValueError(f"Required field '{source_field}' not found in source data")
                            continue
                        value = source_data[source_field]
                    
                    # Apply transformer if specified
                    if 'transformer' in mapping:
                        transformer = getattr(self, mapping['transformer'])
                        value = transformer(value)
                    
                    if value is not None:  # Only include non-None values
                        mapped_data[zotero_field] = value
                
                except Exception as field_error:
                    logger.warning(f"Error mapping field '{zotero_field}': {str(field_error)}")
                    if mapping.get('required', False):
                        raise
            
            return mapped_data
            
        except Exception as e:
            logger.error(f"Error mapping metadata: {str(e)}")
            raise