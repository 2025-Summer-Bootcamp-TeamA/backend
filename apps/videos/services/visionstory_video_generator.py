import logging
from datetime import datetime
from typing import Optional
from apps.core.services.entities.artwork_extracted_info import ArtworkExtractedInfo
from apps.videos.services.visionstory_video_info import VisionStoryVideoInfo
from apps.videos.services.visionstory_service import VisionStoryService

logger = logging.getLogger(__name__)


class VisionStoryVideoGenerator:
    """VisionStory AI를 사용하여 영상을 생성하는 서비스"""
    
    def __init__(self, visionstory_service: Optional[VisionStoryService] = None):
        """
        VisionStoryVideoGenerator 초기화
        
        Args:
            visionstory_service: VisionStory API 서비스
        """
        self.visionstory_service = visionstory_service or VisionStoryService()
    
    def generate_video(self, 
                      artwork_info: ArtworkExtractedInfo,
                      avatar_id: str,
                      voice_id: str = "Alice",
                      aspect_ratio: str = "9:16",
                      resolution: str = "480p",
                      emotion: str = "cheerful",
                      background_color: str = "") -> VisionStoryVideoInfo:
        """
        작품 정보를 바탕으로 VisionStory AI 영상을 생성합니다.
        
        Args:
            artwork_info: 추출 및 보강된 작품 정보
            avatar_id: 사용할 아바타 ID
            voice_id: 사용할 음성 ID
            aspect_ratio: 비디오 비율
            resolution: 해상도
            emotion: 감정 설정
            background_color: 배경색
            
        Returns:
            VisionStoryVideoInfo: 생성된 영상 정보
        """
        try:
            logger.info("=== VisionStory 영상 생성 시작 ===")
            
            # 작품 정보에서 스크립트 추출
            video_script = artwork_info.video_script.script_content
            
            # VisionStory API 호출
            video_info = self.visionstory_service.create_video(
                avatar_id=avatar_id,
                video_script=video_script,
                voice_id=voice_id,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                emotion=emotion,
                background_color=background_color
            )
            
            logger.info("=== VisionStory 영상 생성 완료 ===")
            return video_info
                
        except Exception as e:
            logger.error(f"VisionStory 영상 생성 중 오류 발생: {str(e)}")
            raise
    
    def get_available_avatars(self) -> dict:
        """사용 가능한 아바타 목록을 가져옵니다."""
        return self.visionstory_service.get_available_avatars()
    
    def get_available_voices(self) -> dict:
        """사용 가능한 음성 목록을 가져옵니다."""
        return self.visionstory_service.get_available_voices()
    
    def get_recent_videos(self) -> dict:
        """최근 생성된 영상 목록을 가져옵니다."""
        return self.visionstory_service.get_recent_videos() 