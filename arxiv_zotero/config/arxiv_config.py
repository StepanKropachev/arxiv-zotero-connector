ARXIV_TO_ZOTERO_MAPPING = {
    # Basic metadata (required fields)
    'title': {
        'source_field': 'title',
        'required': True,
        'transformer': 'clean_latex_markup'
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
    
    # Additional metadata (all optional)
    'abstractNote': {
        'source_field': 'abstract',
        'required': False,
        'transformer': 'clean_latex_markup'
    },
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
    'archive': {
        'source_field': None,
        'required': False,
        'default_value': 'arXiv',
        'use_default': True
    },
    'archiveLocation': {
        'source_field': 'arxiv_id',  # Changed from primary_category to arxiv_id
        'required': False
    },
    'libraryCatalog': {
        'source_field': None,
        'required': False,
        'default_value': 'arXiv.org',
        'use_default': True
    },
    'tags': {
        'source_field': 'categories',
        'required': False,
        'transformer': 'transform_tags'
    },
    'extra': {
        'source_field': ['comment', 'version', 'primary_category', 'arxiv_id'],  # Added arxiv_id and primary_category
        'required': False,
        'transformer': 'transform_extra'
    },
    'accessDate': {
        'source_field': None,
        'required': False,
        'transformer': 'get_current_date',
        'use_default': True
    },
    'rights': {
        'source_field': 'license',
        'required': False
    }
}
