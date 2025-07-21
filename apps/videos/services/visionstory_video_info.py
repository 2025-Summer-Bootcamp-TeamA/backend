from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VisionStoryVideoInfo:
    """VisionStory AI로 생성된 영상 정보"""
    video_id: str = ""  # VisionStory에서 생성된 비디오 ID
    video_url: str = ""  # 생성된 비디오 URL
    thumbnail_url: str = ""  # 썸네일 URL
    status: str = "pending"  # 생성 상태 (queued, creating, failed, created)
    avatar_id: str = ""  # 사용된 아바타 ID
    voice_id: str = ""  # 사용된 음성 ID
    aspect_ratio: str = "9:16"  # 비디오 비율
    resolution: str = "480p"  # 비디오 해상도
    emotion: str = "cheerful"  # 감정 설정
    background_color: str = ""  # 배경색
    duration: int = 0  # 비디오 길이 (초)
    cost_credit: int = 0  # 사용된 크레딧
    created_at: Optional[datetime] = None
    generation_method: str = "visionstory_api"  # 생성 방법
    success: bool = False
    error_message: Optional[str] = None 