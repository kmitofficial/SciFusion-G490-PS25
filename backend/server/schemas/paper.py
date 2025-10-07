"""
Paper-related Pydantic schemas
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime


class PaperAuthor(BaseModel):
    name: str
    affiliation: Optional[str] = None


class PaperResponse(BaseModel):
    paper_id: str = Field(..., description="arXiv paper ID")
    title: str = Field(..., description="Paper title")
    abstract: str = Field(..., description="Paper abstract")
    
    # Author information
    authors: List[str] = Field(default=[], description="List of author names")
    
    # Publication information
    published: Optional[datetime] = Field(None, description="Publication date")
    updated: Optional[datetime] = Field(None, description="Last update date")
    year: Optional[int] = Field(None, description="Publication year")
    
    # arXiv specific fields
    categories: List[str] = Field(default=[], description="arXiv categories")
    primary_category: Optional[str] = Field(None, description="Primary arXiv category")
    
    # URLs and identifiers
    arxiv_url: Optional[str] = Field(None, description="arXiv URL")
    pdf_url: Optional[str] = Field(None, description="PDF download URL")
    
    # Additional metadata
    comment: Optional[str] = Field(None, description="Author comments")
    journal_reference: Optional[str] = Field(None, description="Journal reference")
    doi: Optional[str] = Field(None, description="DOI")
    
    # Scoring (for ranked results)
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "paper_id": "2301.12345",
                "title": "Attention Is All You Need for Point Clouds",
                "abstract": "We propose a novel attention mechanism...",
                "authors": ["John Doe", "Jane Smith"],
                "year": 2023,
                "categories": ["cs.CV", "cs.LG"],
                "primary_category": "cs.CV"
            }
        }


class PaperSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    
    # Filters
    category: Optional[str] = Field(None, description="arXiv category filter")
    start_year: Optional[int] = Field(None, ge=1990, description="Start year filter")
    end_year: Optional[int] = Field(None, le=2030, description="End year filter")
    
    # Search options
    search_in_title: bool = Field(default=True, description="Search in paper titles")
    search_in_abstract: bool = Field(default=True, description="Search in paper abstracts")
    search_in_comments: bool = Field(default=False, description="Search in author comments")
    
    # Sorting options
    sort_by: str = Field(default="relevance", description="Sort by: relevance, date, citations")
    sort_order: str = Field(default="desc", description="Sort order: asc, desc")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "transformer attention mechanism",
                "max_results": 10,
                "category": "cs.LG",
                "start_year": 2020,
                "sort_by": "relevance"
            }
        }


class PaperSearchResponse(BaseModel):
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Total number of results found")
    returned_results: int = Field(..., description="Number of results returned")
    
    # Search metadata
    search_time: float = Field(..., description="Search execution time in seconds")
    filters_applied: Dict[str, Any] = Field(default={}, description="Applied filters")
    
    # Results
    papers: List[PaperResponse] = Field(default=[], description="List of matching papers")
    
    # Pagination info
    has_more: bool = Field(default=False, description="Whether more results are available")
    next_offset: Optional[int] = Field(None, description="Offset for next page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "transformer attention",
                "total_results": 150,
                "returned_results": 10,
                "search_time": 0.85,
                "papers": []
            }
        }


class PaperCategories(BaseModel):
    categories: Dict[str, str] = Field(..., description="Available arXiv categories")
    
    class Config:
        json_schema_extra = {
            "example": {
                "categories": {
                    "cs.AI": "Artificial Intelligence",
                    "cs.LG": "Machine Learning",
                    "cs.CV": "Computer Vision and Pattern Recognition"
                }
            }
        }


class PaperStats(BaseModel):
    paper_id: str
    views: Optional[int] = None
    downloads: Optional[int] = None
    citations: Optional[int] = None  # Not available in arXiv, but could be added from external sources
    
    # Engagement metrics
    bookmarks: Optional[int] = None
    shares: Optional[int] = None
    
    # Time-based metrics
    daily_views: Optional[List[int]] = None
    weekly_downloads: Optional[List[int]] = None


class PaperCollection(BaseModel):
    name: str
    description: Optional[str] = None
    created_at: datetime
    paper_ids: List[str]
    tags: List[str] = []
    
    # Collection metadata
    total_papers: int
    public: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Transformer Architecture Papers",
                "description": "Collection of seminal transformer papers",
                "paper_ids": ["1706.03762", "2010.11929"],
                "tags": ["transformers", "attention", "nlp"],
                "total_papers": 2,
                "public": True
            }
        }