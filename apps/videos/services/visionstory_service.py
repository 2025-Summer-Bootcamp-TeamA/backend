import os
import logging
import requests
from typing import Optional, Dict, Any
from apps.videos.services.visionstory_video_info import VisionStoryVideoInfo
from datetime import datetime

logger = logging.getLogger(__name__)


class VisionStoryService:
    """VisionStory AI API와 통신하는 서비스"""
    
    def __init__(self):
        """VisionStoryService 초기화"""
        self.api_key = os.getenv("VISIONSTORY_API_KEY")
        self.base_url = "https://openapi.visionstory.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("VISIONSTORY_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    def create_video(self, 
                    avatar_id: str, 
                    video_script: str,
                    voice_id: str = "Alice",
                    aspect_ratio: str = "9:16",
                    resolution: str = "480p",
                    emotion: str = "cheerful",
                    background_color: str = "") -> VisionStoryVideoInfo:
        """
        VisionStory AI를 사용하여 영상을 생성합니다.
        
        Args:
            avatar_id: 사용할 아바타 ID
            video_script: 영상 스크립트
            voice_id: 사용할 음성 ID
            aspect_ratio: 비디오 비율
            resolution: 해상도
            emotion: 감정 설정
            background_color: 배경색
            
        Returns:
            VisionStoryVideoInfo: 생성된 영상 정보
        """
        try:
            logger.info("VisionStory API 호출 시작")
            
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "avatar_id": avatar_id,
                "text_script": {
                    "text": video_script,
                    "voice_id": voice_id
                },
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "emotion": emotion
            }
            
            if background_color:
                payload["background_color"] = background_color
            
            response = requests.post(
                f"{self.base_url}/video",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 성공 응답 처리
                video_info = VisionStoryVideoInfo(
                    video_id=result.get("video_id", ""),
                    video_url=result.get("video_url", ""),
                    thumbnail_url=result.get("thumbnail_url", ""),
                    status=result.get("status", "created"),
                    avatar_id=avatar_id,
                    voice_id=voice_id,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    emotion=emotion,
                    background_color=background_color,
                    duration=result.get("duration", 0),
                    cost_credit=result.get("cost_credit", 0),
                    created_at=datetime.now(),
                    generation_method="visionstory_api",
                    success=True
                )
                
                logger.info(f"VisionStory 영상 생성 성공: {video_info.video_url}")
                return video_info
                
            else:
                error_msg = f"VisionStory API 오류: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                return VisionStoryVideoInfo(
                    avatar_id=avatar_id,
                    voice_id=voice_id,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    emotion=emotion,
                    background_color=background_color,
                    generation_method="visionstory_api",
                    success=False,
                    error_message=error_msg
                )
                
        except Exception as e:
            error_msg = f"VisionStory API 호출 중 오류: {str(e)}"
            logger.error(error_msg)
            
            return VisionStoryVideoInfo(
                avatar_id=avatar_id,
                voice_id=voice_id,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                emotion=emotion,
                background_color=background_color,
                generation_method="visionstory_api",
                success=False,
                error_message=error_msg
            )
    
    def get_available_avatars(self) -> Dict[str, Any]:
        """사용 가능한 아바타 목록을 가져옵니다."""
        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/avatars",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"아바타 목록 조회 실패: {response.status_code}")
                return {"success": False, "error": "아바타 목록을 가져올 수 없습니다."}
            
        except Exception as e:
            logger.error(f"아바타 목록 조회 중 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_available_voices(self) -> Dict[str, Any]:
        """사용 가능한 음성 목록을 가져옵니다."""
        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/voices",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"음성 목록 조회 실패: {response.status_code}")
                return {"success": False, "error": "음성 목록을 가져올 수 없습니다."}
            
        except Exception as e:
            logger.error(f"음성 목록 조회 중 오류: {str(e)}")
            return {"success": False, "error": str(e)} 