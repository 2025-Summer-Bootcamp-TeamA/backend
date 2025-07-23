from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class ContentFetchInfo:
    """Fetch MCP 결과만 담당"""
    performed: bool = False
    fetch_results: Optional[List[Dict]] = None
    content_enriched_description: Optional[str] = None
    fetch_timestamp: Optional[datetime] = None 