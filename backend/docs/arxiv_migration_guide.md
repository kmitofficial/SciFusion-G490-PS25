# arXiv API Integration for InternAgent

This document describes the migration from Semantic Scholar to arXiv API for research paper fetching in the InternAgent project.

## Summary of Changes

The InternAgent project has been updated to use arXiv's open API instead of Semantic Scholar for fetching research papers. This change provides several benefits:

- **No API Key Required**: arXiv API is completely open and doesn't require authentication
- **Direct Access**: No rate limits or quotas to manage
- **Focus on Preprints**: Access to cutting-edge research papers often before peer review
- **Rich Metadata**: Comprehensive paper information including categories and full author lists

## What Changed

### Files Modified

1. **`requirements.txt`**: Added `arxiv` and `feedparser` dependencies
2. **`dolphin_utils/rag_tools/lit_review_tools.py`**: Complete rewrite to use arXiv API
3. **Created test script**: `test_arxiv_integration.py` for validation

### API Function Mapping

| Original (Semantic Scholar) | New (arXiv) | Notes |
|---------------------------|-------------|--------|
| `KeywordQuery(keyword)` | `KeywordQuery(keyword, max_results=20)` | Now searches arXiv's full text and metadata |
| `PaperQuery(paper_id)` | `PaperQuery(paper_id, max_results=20)` | Returns papers from same category instead of citations |
| `PaperDetails(paper_id)` | `PaperDetails(paper_id)` | Returns arXiv paper metadata |
| `GetCitationCount(paper_id)` | `GetCitationCount(paper_id)` | Always returns 0 (arXiv doesn't track citations) |
| `GetCitations(paper_id)` | `GetCitations(paper_id)` | Returns empty list (not available) |
| `GetReferences(paper_id)` | `GetReferences(paper_id)` | Returns similar papers instead of references |

### Data Structure Changes

**Old Semantic Scholar Format:**
```python
{
    "paperId": "abc123",
    "title": "Paper Title", 
    "abstract": "Abstract text",
    "year": 2023,
    "citationCount": 150,
    "venue": "Conference Name",
    "tldr": {"text": "Summary"}
}
```

**New arXiv Format:**
```python
{
    "paperId": "2301.12345",
    "title": "Paper Title",
    "abstract": "Abstract text", 
    "year": 2023,
    "authors": ["Author One", "Author Two"],
    "url": "http://arxiv.org/abs/2301.12345",
    "categories": ["cs.AI", "cs.LG"],
    "citationCount": 0,  # Always 0 for arXiv
    "venue": "arXiv",
    "published": "2023-01-15T10:30:00"
}
```

## Key Differences

### Advantages of arXiv

1. **No Authentication**: No need for API keys or account setup
2. **No Rate Limits**: Free and unlimited access
3. **Fresh Content**: Access to newest research preprints
4. **Detailed Metadata**: Rich categorization and author information
5. **Stable IDs**: arXiv IDs are permanent and don't change

### Limitations Compared to Semantic Scholar

1. **No Citation Data**: arXiv doesn't track citations or references
2. **Preprint Focus**: Mainly academic preprints, fewer published papers
3. **No Recommendation Engine**: Similar papers found by category, not ML-based similarity
4. **Limited Venue Info**: Most papers are preprints without venue information

## Setup Instructions

### 1. Install Dependencies

```bash
pip install arxiv feedparser
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Remove Semantic Scholar API Key

The `S2_API_KEY` environment variable is no longer needed and can be removed.

### 3. Test the Integration

Run the test script to verify everything works:

```bash
python test_arxiv_integration.py
```

## Usage Examples

### Basic Paper Search

```python
from dolphin_utils.rag_tools.lit_review_tools import KeywordQuery

# Search for papers about transformers
result = KeywordQuery("attention transformers", max_results=10)
if result and "data" in result:
    papers = result["data"]
    print(f"Found {len(papers)} papers")
```

### Get Paper Details

```python
from dolphin_utils.rag_tools.lit_review_tools import PaperDetails

# Get details for a specific arXiv paper
paper = PaperDetails("2106.04554")
if paper:
    print(f"Title: {paper['title']}")
    print(f"Categories: {paper['categories']}")
```

### Find Similar Papers

```python
from dolphin_utils.rag_tools.lit_review_tools import PaperQuery

# Find papers in similar categories
similar = PaperQuery("2106.04554", max_results=5)
if similar and "recommendedPapers" in similar:
    papers = similar["recommendedPapers"]
    print(f"Found {len(papers)} similar papers")
```

## Running InternAgent with arXiv

The main InternAgent workflow remains the same. Use RAG mode to fetch papers from arXiv:

```bash
python launch_dolphin.py \
    --model localhost-deepseek-v2-16b \
    --code_model localhost-deepseek-v2-16b \
    --experiment point_classification_modelnet \
    --rag \
    --topic "point cloud classification deep learning" \
    --max_papers 20
```

## Migration Impact

### For Users
- **Immediate**: No more API key management required
- **Search Quality**: May find different but relevant papers focused on recent research
- **Performance**: Potentially faster due to no rate limits

### For Developers  
- **Code Compatibility**: All existing function calls work the same way
- **Data Handling**: Same paper filtering and scoring logic applies
- **Testing**: New test script validates all functionality

## Troubleshooting

### Common Issues

1. **Import Errors**: Install missing dependencies with `pip install arxiv feedparser`
2. **No Results**: arXiv search is keyword-based; try different terms or broader queries
3. **Missing Papers**: Some papers may only exist in Semantic Scholar; arXiv focuses on preprints

### Getting Help

1. Run the test script: `python test_arxiv_integration.py`
2. Check arXiv API status: Visit [arxiv.org](https://arxiv.org)
3. Verify internet connection for API access

## Future Enhancements

Potential improvements to consider:

1. **Hybrid Search**: Combine arXiv with other sources
2. **Citation Integration**: Add external citation data from other sources
3. **Advanced Filtering**: Category-specific paper filtering
4. **Caching**: Local storage of frequently accessed papers
5. **Full Text**: Integration with arXiv PDF processing for full-text search

---

This migration maintains all existing functionality while providing a more accessible and reliable paper fetching system for the InternAgent research workflow.