"""
arXiv Service - Integration with arXiv API
"""

import arxiv
from typing import List, Optional
from datetime import datetime, timedelta
import re

from schemas.paper import (
    PaperResponse, PaperSearchRequest, PaperSearchResponse
)

# Import the updated InternAgent paper tools
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dolphin_utils.rag_tools.lit_review_tools import (
    KeywordQuery, PaperDetails, PaperQuery, GetAbstract,
    paper_filter, format_papers_for_printing
)


class ArxivService:
    """Service for interacting with arXiv API through InternAgent paper tools"""
    
    def __init__(self):
        self.client = arxiv.Client()
    
    def search_papers(self, search_request: PaperSearchRequest) -> PaperSearchResponse:
        """Search for papers using InternAgent's arXiv integration"""
        start_time = datetime.now()
        
        try:
            # Use InternAgent's KeywordQuery function
            result = KeywordQuery(search_request.query, max_results=search_request.max_results)
            
            if not result or "data" not in result:
                return PaperSearchResponse(
                    query=search_request.query,
                    total_results=0,
                    returned_results=0,
                    search_time=0.0,
                    papers=[]
                )
            
            papers_data = result["data"]
            
            # Apply filters
            filtered_papers = self._apply_filters(papers_data, search_request)
            
            # Convert to response format
            papers = [self._convert_to_paper_response(paper) for paper in filtered_papers]
            
            # Calculate search time
            search_time = (datetime.now() - start_time).total_seconds()
            
            return PaperSearchResponse(
                query=search_request.query,
                total_results=result.get("total", len(papers)),
                returned_results=len(papers),
                search_time=search_time,
                filters_applied={
                    "category": search_request.category,
                    "start_year": search_request.start_year,
                    "end_year": search_request.end_year
                },
                papers=papers,
                has_more=len(papers) >= search_request.max_results
            )
            
        except Exception as e:
            return PaperSearchResponse(
                query=search_request.query,
                total_results=0,
                returned_results=0,
                search_time=(datetime.now() - start_time).total_seconds(),
                papers=[],
                error=str(e)
            )
    
    def get_paper_details(self, paper_id: str) -> Optional[PaperResponse]:
        """Get detailed paper information"""
        try:
            # Use InternAgent's PaperDetails function
            paper_data = PaperDetails(paper_id)
            
            if not paper_data:
                return None
            
            return self._convert_to_paper_response(paper_data)
            
        except Exception as e:
            print(f"Error getting paper details: {e}")
            return None
    
    def get_similar_papers(self, paper_id: str, max_results: int = 10) -> List[PaperResponse]:
        """Get papers similar to the specified paper"""
        try:
            # Use InternAgent's PaperQuery function
            result = PaperQuery(paper_id, max_results=max_results)
            
            if not result or "recommendedPapers" not in result:
                return []
            
            papers_data = result["recommendedPapers"]
            filtered_papers = paper_filter(papers_data)
            
            return [self._convert_to_paper_response(paper) for paper in filtered_papers]
            
        except Exception as e:
            print(f"Error getting similar papers: {e}")
            return []
    
    def get_paper_abstract(self, paper_id: str) -> Optional[str]:
        """Get paper abstract"""
        try:
            return GetAbstract(paper_id)
        except Exception as e:
            print(f"Error getting paper abstract: {e}")
            return None
    
    def advanced_search(self, search_request: PaperSearchRequest) -> PaperSearchResponse:
        """Advanced search with complex queries"""
        # For now, use the same search logic
        # Could be enhanced with more sophisticated query building
        return self.search_papers(search_request)
    
    def _apply_filters(self, papers: List[dict], search_request: PaperSearchRequest) -> List[dict]:
        """Apply filters to paper results"""
        filtered = papers
        
        # Category filter
        if search_request.category:
            filtered = [
                paper for paper in filtered
                if search_request.category in paper.get("categories", [])
            ]
        
        # Year filters
        if search_request.start_year or search_request.end_year:
            def year_filter(paper):
                year = paper.get("year")
                if not year:
                    return False
                
                if search_request.start_year and year < search_request.start_year:
                    return False
                if search_request.end_year and year > search_request.end_year:
                    return False
                
                return True
            
            filtered = [paper for paper in filtered if year_filter(paper)]
        
        return filtered
    
    def _convert_to_paper_response(self, paper_data: dict) -> PaperResponse:
        """Convert InternAgent paper format to API response format"""
        
        # Extract publication date
        published = None
        if "published" in paper_data:
            if isinstance(paper_data["published"], str):
                try:
                    published = datetime.fromisoformat(paper_data["published"].replace('Z', '+00:00'))
                except:
                    published = None
        
        # Build URLs
        paper_id = paper_data.get("paperId", "")
        arxiv_url = paper_data.get("url") or f"http://arxiv.org/abs/{paper_id}"
        pdf_url = f"http://arxiv.org/pdf/{paper_id}.pdf"
        
        return PaperResponse(
            paper_id=paper_id,
            title=paper_data.get("title", ""),
            abstract=paper_data.get("abstract", ""),
            
            authors=paper_data.get("authors", []),
            
            published=published,
            year=paper_data.get("year"),
            
            categories=paper_data.get("categories", []),
            primary_category=paper_data.get("categories", [None])[0],
            
            arxiv_url=arxiv_url,
            pdf_url=pdf_url,
            
            comment=paper_data.get("comment"),
            journal_reference=paper_data.get("journal_reference"),
            doi=paper_data.get("doi"),
            
            relevance_score=paper_data.get("score")
        )