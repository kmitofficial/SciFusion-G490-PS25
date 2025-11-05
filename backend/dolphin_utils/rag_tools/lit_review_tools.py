import requests
import xml.etree.ElementTree as ET
import os
import json
import re
import time
from typing import List, Dict, Union

# No API key needed for arXiv
S2_KEY = None  # Remove Semantic Scholar key dependency

# arXiv API endpoint
ARXIV_API_URL = "http://export.arxiv.org/api/query"


def KeywordQuery(keyword: str) -> Union[None, List[Dict]]:
    """Search arXiv for papers matching the given keyword."""
    query_params = {
        "search_query": f"all:{keyword}",
        "start": 0,
        "max_results": 20,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    try:
        response = requests.get(ARXIV_API_URL, params=query_params, timeout=30)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text[:500]}")  # Print first 500 chars
        if response.status_code == 200:
            # Parse XML response
            root = ET.fromstring(response.text)
            namespace = {"atom": "http://www.w3.org/2005/Atom"}
            papers = []
            for entry in root.findall("atom:entry", namespace):
                arxiv_id = entry.find("atom:id", namespace).text.split("/")[-1]  # Extract ID (e.g., 1234.56789)
                paper = {
                    "paperId": arxiv_id,
                    "title": entry.find("atom:title", namespace).text.strip(),
                    "year": entry.find("atom:published", namespace).text[:4],
                    "citationCount": 0,  # Not available from arXiv
                    "abstract": entry.find("atom:summary", namespace).text.strip() if entry.find("atom:summary",
                                                                                                 namespace) is not None else "",
                    "tldr": None  # arXiv does not provide TLDR
                }
                papers.append(paper)
            time.sleep(3.0)  # Respect arXiv's 3-second delay
            if not papers:
                return None
            return paper_filter(papers)
        else:
            print(f"Error from arXiv API: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Exception in KeywordQuery: {e}")
        return None


def PaperQuery(paper_id: str) -> Union[None, List[Dict]]:
    """Simulate retrieving similar papers by searching keywords from the target paper's title/abstract."""
    # First, get the paper's details to extract keywords
    paper_details = PaperDetails(paper_id)
    if not paper_details:
        print(f"PaperQuery: Could not retrieve details for paper {paper_id}")
        return None

    # Use title as the query (or extract keywords from abstract if available)
    query = paper_details["title"]
    if paper_details["abstract"]:
        # Simple keyword extraction: take first few words of abstract
        query = " ".join(paper_details["abstract"].split()[:5])

    query_params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": 20,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    try:
        response = requests.get(ARXIV_API_URL, params=query_params, timeout=30)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            namespace = {"atom": "http://www.w3.org/2005/Atom"}
            papers = []
            for entry in root.findall("atom:entry", namespace):
                arxiv_id = entry.find("atom:id", namespace).text.split("/")[-1]
                # Skip the original paper if it appears in results
                if arxiv_id == paper_id:
                    continue
                paper = {
                    "paperId": arxiv_id,
                    "title": entry.find("atom:title", namespace).text.strip(),
                    "year": entry.find("atom:published", namespace).text[:4],
                    "citationCount": 0,
                    "abstract": entry.find("atom:summary", namespace).text.strip() if entry.find("atom:summary",
                                                                                                 namespace) is not None else "",
                    "tldr": None
                }
                papers.append(paper)
            time.sleep(3.0)
            if not papers:
                return None
            return paper_filter(papers)
        else:
            print(f"Error from arXiv API (PaperQuery): {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception in PaperQuery: {e}")
        return None


def PaperDetails(paper_id: str, fields: str = 'title,year,abstract,authors,citationCount,venue') -> Union[None, Dict]:
    """Get details of a specific paper by arXiv ID."""
    query_params = {
        "search_query": f"id:{paper_id}",
        "start": 0,
        "max_results": 1
    }
    try:
        response = requests.get(ARXIV_API_URL, params=query_params, timeout=30)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            namespace = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", namespace)
            if not entry:
                return None
            paper = {
                "paperId": paper_id,
                "title": entry.find("atom:title", namespace).text.strip(),
                "year": entry.find("atom:published", namespace).text[:4],
                "abstract": entry.find("atom:summary", namespace).text.strip() if entry.find("atom:summary",
                                                                                             namespace) is not None else "",
                "authors": ", ".join(
                    author.find("atom:name", namespace).text.strip()
                    for author in entry.findall("atom:author", namespace)
                ),
                "citationCount": 0,
                "venue": "arXiv",
                "tldr": None
            }
            # Handle fields not in arXiv (citations, references)
            if "citations" in fields:
                paper["citations"] = []  # Not available
            if "references" in fields:
                paper["references"] = []  # Not available
            time.sleep(3.0)
            return paper
        else:
            print(f"Error from arXiv API (PaperDetails): {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception in PaperDetails: {e}")
        return None


def GetAbstract(paper_id: str) -> Union[None, str]:
    """Get the abstract of a paper by arXiv ID."""
    paper_details = PaperDetails(paper_id)
    if paper_details is not None:
        return paper_details["abstract"]
    return None


def GetCitationCount(paper_id: str) -> Union[None, int]:
    """Get the citation count of a paper by arXiv ID (always 0, as not available)."""
    return 0  # arXiv API does not provide citation counts


def GetCitations(paper_id: str) -> Union[None, List[Dict]]:
    """Get the citation list of a paper by arXiv ID (not supported, return empty list)."""
    print(f"Warning: arXiv API does not support retrieving citations for {paper_id}")
    return []  # arXiv API does not provide citations


def GetReferences(paper_id: str) -> Union[None, List[Dict]]:
    """Get the reference list of a paper by arXiv ID (not supported, return empty list)."""
    print(f"Warning: arXiv API does not support retrieving references for {paper_id}")
    return []  # arXiv API does not provide references


def paper_filter(paper_lst: List[Dict]) -> List[Dict]:
    """Filter out papers based on basic heuristics."""
    filtered_lst = []
    for paper in paper_lst:
        abstract = paper["abstract"] if paper["abstract"] else paper["title"]
        if "survey" in abstract.lower() or "review" in abstract.lower() or "position paper" in abstract.lower():
            continue
        filtered_lst.append(paper)
    return filtered_lst


# The following functions remain unchanged as they do not interact with the API directly
def parse_and_execute(output: str) -> Union[None, List[Dict], str, int]:
    """Parse GPT-4 output and execute corresponding functions."""
    if output.startswith("KeywordQuery"):
        match = re.match(r'KeywordQuery\("([^"]+)"\)', output)
        keyword = match.group(1) if match else None
        if keyword:
            response = KeywordQuery(keyword)
            if response is None:
                return None
            return paper_filter(response)
    elif output.startswith("PaperQuery"):
        match = re.match(r'PaperQuery\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            response = PaperQuery(paper_id)
            if response is not None:
                return paper_filter(response)
    elif output.startswith("GetAbstract"):
        match = re.match(r'GetAbstract\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            return GetAbstract(paper_id)
    elif output.startswith("GetCitationCount"):
        match = re.match(r'GetCitationCount\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            return GetCitationCount(paper_id)
    elif output.startswith("GetCitations"):
        match = re.match(r'GetCitations\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            return GetCitations(paper_id)
    elif output.startswith("GetReferences"):
        match = re.match(r'GetReferences\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            return GetReferences(paper_id)
    return None


def parse_io_description(output: str) -> tuple:
    match_input = re.match(r'Input\("([^"]+)"\)', output)
    input_description = match_input.group(1) if match_input else None
    match_output = re.match(r'.*Output\("([^"]+)"\)', output)
    output_description = match_output.group(1) if match_output else None
    return input_description, output_description


def format_papers_for_printing(paper_lst: List[Dict], include_abstract: bool = True, include_score: bool = True,
                               include_id: bool = True) -> str:
    """Convert a list of papers to a string for printing or as part of a prompt."""
    output_str = ""
    for paper in paper_lst:
        if include_id:
            output_str += "paperId: " + paper["paperId"].strip() + "\n"
        output_str += "title: " + paper["title"].strip() + "\n"
        if include_abstract and "abstract" in paper and paper["abstract"]:
            abstract = paper["abstract"].strip()
            if len(abstract) > 500:  # Limit abstract length
                abstract = abstract[:500] + "..."
            output_str += "abstract: " + abstract + "\n"
        # Skip tldr if not available
        if include_score and "score" in paper:
            output_str += "relevance score: " + str(paper["score"]) + "\n"
        output_str += "\n"
    return output_str


def print_top_papers_from_paper_bank(paper_bank: Dict, top_k: int = 10) -> None:
    data_list = [{'id': id, **info} for id, info in paper_bank.items()]
    top_papers = sorted(data_list, key=lambda x: x.get('score', 0), reverse=True)[:top_k]
    print(format_papers_for_printing(top_papers, include_abstract=False))


def dedup_paper_bank(sorted_paper_bank: List[Dict]) -> List[Dict]:
    idx_to_remove = []
    for i in reversed(range(len(sorted_paper_bank))):
        for j in range(i):
            if sorted_paper_bank[i]["paperId"].strip() == sorted_paper_bank[j]["paperId"].strip():
                idx_to_remove.append(i)
                break
            if ''.join(sorted_paper_bank[i]["title"].lower().split()) == ''.join(
                    sorted_paper_bank[j]["title"].lower().split()):
                idx_to_remove.append(i)
                break
            if sorted_paper_bank[i]["abstract"] == sorted_paper_bank[j]["abstract"]:
                idx_to_remove.append(i)
                break
    deduped_paper_bank = [paper for i, paper in enumerate(sorted_paper_bank) if i not in idx_to_remove]
    return deduped_paper_bank