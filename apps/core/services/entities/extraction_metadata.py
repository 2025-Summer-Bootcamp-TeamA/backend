from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ExtractionMetadata:
    """추출 과정의 메타데이터 담당"""
    confidence: float = 0.0
    extraction_method: str = "gemini_ai"
    raw_response: str = ""
    success: bool = True
    extraction_timestamp: Optional[datetime] = None 