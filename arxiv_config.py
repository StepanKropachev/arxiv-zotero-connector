from typing import Dict, Any

ARXIV_TO_ZOTERO_MAPPING = {
    # Basic metadata
    'title': {
        'source_field': 'title',
        'required': True,
        'transformer': 'clean_latex_markup'  # New transformer to clean LaTeX markup
    },
    'creators': {
        'source_field': 'authors',
        'required': True,
        'transformer': 'transform_creators'
    },
    'url': {
        'source_field': 'arxiv_url',
        'required': True
    },
    'abstractNote': {
        'source_field': 'abstract',
        'required': False,
        'transformer': 'clean_latex_markup'  # Clean LaTeX markup from abstract
    },
    'date': {
        'source_field': 'published',
        'required': True,
        'transformer': 'transform_date'
    },
    
    # Additional metadata
    'DOI': {
        'source_field': 'doi',
        'required': False
    },
    'journalAbbreviation': {
        'source_field': 'journal_ref',
        'required': False,
        'transformer': 'extract_journal_abbrev'
    },
    'publicationTitle': {
        'source_field': 'journal_ref',
        'required': False,
        'transformer': 'extract_journal_name'
    },
    'volume': {
        'source_field': 'journal_ref',
        'required': False,
        'transformer': 'extract_volume'
    },
    'issue': {
        'source_field': 'journal_ref',
        'required': False,
        'transformer': 'extract_issue'
    },
    'pages': {
        'source_field': 'journal_ref',
        'required': False,
        'transformer': 'extract_pages'
    },
    'archiveID': {  # Store arXiv ID
        'source_field': 'arxiv_id',
        'required': True
    },
    'archive': {  # Constant value for arXiv
        'source_field': None,
        'required': True,
        'default_value': 'arXiv'
    },
    'archiveLocation': {  # Store primary category
        'source_field': 'primary_category',
        'required': False
    },
    'libraryCatalog': {  # Constant value
        'source_field': None,
        'required': True,
        'default_value': 'arXiv.org'
    },
    'tags': {
        'source_field': 'categories',
        'required': False,
        'transformer': 'transform_tags'
    },
    'extra': {  # Store additional metadata like comment, version
        'source_field': ['comment', 'version'],
        'required': False,
        'transformer': 'transform_extra'
    },
    'accessDate': {  # Add access date
        'source_field': None,
        'required': True,
        'transformer': 'get_current_date'
    },
    'rights': {  # Add license information if available
        'source_field': 'license',
        'required': False
    }
}