"""
Paper search and retrieval endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel

from schemas.paper import PaperResponse, PaperSearchRequest, PaperSearchResponse
from services.arxiv_service import ArxivService
import sys
import os

# Add parent directories to path to import InternAgent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

router = APIRouter()

# Dependency injection
def get_arxiv_service() -> ArxivService:
    return ArxivService()


@router.get("/search", response_model=PaperSearchResponse)
async def search_papers(
    query: str = Query(..., description="Search query for papers"),
    max_results: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    category: Optional[str] = Query(None, description="arXiv category filter"),
    start_year: Optional[int] = Query(None, description="Start year filter"),
    end_year: Optional[int] = Query(None, description="End year filter"),
    arxiv_service: ArxivService = Depends(get_arxiv_service)
):
    """Search for papers using arXiv API"""
    try:
        search_request = PaperSearchRequest(
            query=query,
            max_results=max_results,
            category=category,
            start_year=start_year,
            end_year=end_year
        )
        
        results = arxiv_service.search_papers(search_request)
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper_details(
    paper_id: str,
    arxiv_service: ArxivService = Depends(get_arxiv_service)
):
    """Get detailed information about a specific paper"""
    try:
        paper = arxiv_service.get_paper_details(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return paper
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[PaperResponse])
async def get_multiple_papers(
    paper_ids: List[str],
    arxiv_service: ArxivService = Depends(get_arxiv_service)
):
    """Get details for multiple papers"""
    if len(paper_ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 papers per batch request")
    
    try:
        papers = []
        for paper_id in paper_ids:
            paper = arxiv_service.get_paper_details(paper_id)
            if paper:
                papers.append(paper)
        
        return papers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{paper_id}/similar", response_model=List[PaperResponse])
async def get_similar_papers(
    paper_id: str,
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of similar papers"),
    arxiv_service: ArxivService = Depends(get_arxiv_service)
):
    """Get papers similar to the specified paper"""
    try:
        similar_papers = arxiv_service.get_similar_papers(paper_id, max_results)
        return similar_papers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{paper_id}/abstract")
async def get_paper_abstract(
    paper_id: str,
    arxiv_service: ArxivService = Depends(get_arxiv_service)
):
    """Get only the abstract of a paper"""
    try:
        abstract = arxiv_service.get_paper_abstract(paper_id)
        if not abstract:
            raise HTTPException(status_code=404, detail="Paper not found")
        return {"paper_id": paper_id, "abstract": abstract}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/")
async def get_available_categories():
    """Get list of available arXiv categories"""
    categories = {
        "cs.AI": "Artificial Intelligence",
        "cs.LG": "Machine Learning", 
        "cs.CL": "Computation and Language",
        "cs.CV": "Computer Vision and Pattern Recognition",
        "cs.RO": "Robotics",
        "cs.NE": "Neural and Evolutionary Computing",
        "stat.ML": "Machine Learning (Statistics)",
        "math.OC": "Optimization and Control",
        "cs.IR": "Information Retrieval",
        "cs.HC": "Human-Computer Interaction"
    }
    return {"categories": categories}


class PaperSearchHistory(BaseModel):
    query: str
    timestamp: str
    results_count: int

@router.get("/search/history")
async def get_search_history():
    """Get recent search history (placeholder for future implementation)"""
    # This would typically fetch from a database
    return {"history": []}


@router.post("/search/advanced", response_model=PaperSearchResponse)
async def advanced_search(
    search_request: PaperSearchRequest,
    arxiv_service: ArxivService = Depends(get_arxiv_service)
):
    """Advanced paper search with complex filters"""
    try:
        results = arxiv_service.advanced_search(search_request)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")