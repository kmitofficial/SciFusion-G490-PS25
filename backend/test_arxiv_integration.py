#!/usr/bin/env python3
"""
Test script for arXiv API integration in InternAgent
This script tests the updated paper fetching functionality using arXiv instead of Semantic Scholar
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dolphin_utils.rag_tools.lit_review_tools import (
    KeywordQuery, PaperQuery, PaperDetails, GetAbstract, 
    GetCitationCount, format_papers_for_printing, paper_filter
)

def test_keyword_query():
    """Test keyword-based paper search on arXiv"""
    print("=" * 50)
    print("Testing KeywordQuery with 'machine learning transformers'")
    print("=" * 50)
    
    try:
        result = KeywordQuery("machine learning transformers", max_results=5)
        if result and "data" in result:
            papers = result["data"]
            print(f"Found {len(papers)} papers")
            print("\nFirst paper:")
            if papers:
                print(format_papers_for_printing([papers[0]], include_score=False))
            return papers[0]["paperId"] if papers else None
        else:
            print("No results returned")
            return None
    except Exception as e:
        print(f"Error in KeywordQuery: {e}")
        return None

def test_paper_details(paper_id):
    """Test getting paper details from arXiv"""
    if not paper_id:
        print("No paper ID provided for testing")
        return
        
    print("=" * 50)
    print(f"Testing PaperDetails with ID: {paper_id}")
    print("=" * 50)
    
    try:
        details = PaperDetails(paper_id)
        if details:
            print("Paper details retrieved successfully:")
            print(f"Title: {details['title']}")
            print(f"Year: {details['year']}")
            print(f"Authors: {', '.join(details['authors'][:3])}")
            print(f"Categories: {', '.join(details['categories'])}")
            print(f"Abstract length: {len(details['abstract'])} characters")
        else:
            print("No details found")
    except Exception as e:
        print(f"Error in PaperDetails: {e}")

def test_paper_query(paper_id):
    """Test finding similar papers"""
    if not paper_id:
        print("No paper ID provided for testing")
        return
        
    print("=" * 50)
    print(f"Testing PaperQuery (similar papers) with ID: {paper_id}")
    print("=" * 50)
    
    try:
        result = PaperQuery(paper_id, max_results=3)
        if result and "recommendedPapers" in result:
            papers = result["recommendedPapers"]
            print(f"Found {len(papers)} similar papers")
            if papers:
                filtered_papers = paper_filter(papers)
                print(f"After filtering: {len(filtered_papers)} papers")
                if filtered_papers:
                    print("\nFirst similar paper:")
                    print(format_papers_for_printing([filtered_papers[0]], include_score=False))
        else:
            print("No similar papers found")
    except Exception as e:
        print(f"Error in PaperQuery: {e}")

def test_get_abstract(paper_id):
    """Test getting abstract"""
    if not paper_id:
        print("No paper ID provided for testing")
        return
        
    print("=" * 50)
    print(f"Testing GetAbstract with ID: {paper_id}")
    print("=" * 50)
    
    try:
        abstract = GetAbstract(paper_id)
        if abstract:
            print(f"Abstract retrieved (first 200 chars): {abstract[:200]}...")
        else:
            print("No abstract found")
    except Exception as e:
        print(f"Error in GetAbstract: {e}")

def main():
    """Run all tests"""
    print("🧪 Testing arXiv API Integration for InternAgent")
    print("This will test the updated paper fetching functionality\n")
    
    # Test keyword search
    paper_id = test_keyword_query()
    
    if paper_id:
        # Test other functions with the found paper ID
        test_paper_details(paper_id)
        test_get_abstract(paper_id)
        test_paper_query(paper_id)
    else:
        print("⚠️  Could not retrieve a paper ID for further testing")
        print("Trying with a known arXiv ID...")
        
        # Test with a known arXiv paper ID
        test_paper_id = "2106.04554"  # "Attention Is All You Need" follow-up paper
        test_paper_details(test_paper_id)
        test_get_abstract(test_paper_id)
    
    print("\n" + "=" * 50)
    print("✅ arXiv API integration tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()