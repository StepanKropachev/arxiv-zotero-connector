"""Test basic imports"""

def test_imports():
    """Test that main components can be imported"""
    try:
        from arxiv_zotero import (
            ArxivZoteroCollector,
            ArxivSearchParams,
            load_credentials,
            PDFManager,
            PaperSummarizer
        )
        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"

def test_search_params():
    """Test ArxivSearchParams creation"""
    from arxiv_zotero import ArxivSearchParams
    
    params = ArxivSearchParams(
        keywords=["test"],
        max_results=5
    )
    assert params.keywords == ["test"]
    assert params.max_results == 5
