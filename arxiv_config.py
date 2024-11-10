ARXIV_TO_ZOTERO_MAPPING = {
    'title': {
        'source_field': 'title',
        'required': True
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
        'required': False
    },
    'date': {
        'source_field': 'published',
        'required': True,
        'transformer': 'transform_date'
    },
    'tags': {
        'source_field': 'categories',
        'required': False,
        'transformer': 'transform_tags'
    }
}