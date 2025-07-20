from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VideoScriptInfo:
    """VisionStory AI용 영상 스크립트 정보"""
    script_content: str = ""  # 완성된 스크립트 내용
    script_length: int = 0    # 스크립트 길이 (초 단위)
    generation_method: str = "none"  # 생성 방법 (gemini_ai, fallback 등)
    generation_timestamp: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None 