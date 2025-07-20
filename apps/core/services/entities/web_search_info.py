from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass
class WebSearchInfo:
    """웹 검색 관련 정보만 담당"""
    performed: bool = False
    search_results: Optional[Dict] = None
    enriched_description: Optional[str] = None
    search_timestamp: Optional[datetime] = None 