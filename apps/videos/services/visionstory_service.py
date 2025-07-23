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
        
        logger.info(f"VisionStory API 초기화: API 키 설정됨={bool(self.api_key)}")
        
        if not self.api_key:
            logger.error("VISIONSTORY_API_KEY 환경 변수가 설정되지 않았습니다.")
            raise ValueError("VISIONSTORY_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    def get_avatars(self) -> Optional[Dict[str, Any]]:
        """
        VisionStory에서 사용 가능한 아바타 목록을 조회합니다.
        
        Returns:
            Dict: 아바타 목록 데이터 또는 None (실패 시)
        """
        try:
            url = f"{self.base_url}/avatars"
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            logger.info("VisionStory 아바타 목록 조회 시작")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"아바타 목록 조회 성공: public_avatars={len(data.get('data', {}).get('public_avatars', []))}, my_avatars={len(data.get('data', {}).get('my_avatars', []))}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"VisionStory 아바타 목록 조회 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"아바타 목록 조회 중 예외 발생: {e}")
            return None
    
    def get_latest_avatar_id(self) -> Optional[str]:
        """
        가장 최근에 생성된 아바타 ID를 조회합니다.
        
        Returns:
            str: 최신 아바타 ID 또는 None (실패 시)
        """
        try:
            avatars_data = self.get_avatars()
            if not avatars_data:
                logger.warning("아바타 목록 조회 실패")
                return None
            
            data = avatars_data.get('data', {})
            my_avatars = data.get('my_avatars', [])
            
            if not my_avatars:
                logger.warning("생성된 아바타가 없습니다")
                return None
            
            # 가장 최근 아바타 (첫 번째 아바타가 최신이라고 가정)
            latest_avatar = my_avatars[0]
            avatar_id = latest_avatar.get('avatar_id')
            
            logger.info(f"최신 아바타 ID 조회 성공: {avatar_id}")
            return avatar_id
            
        except Exception as e:
            logger.error(f"최신 아바타 ID 조회 중 예외 발생: {e}")
            return None
    
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
            logger.info(f"VisionStory API 호출 시작: avatar_id={avatar_id}, script_length={len(video_script)}")
            
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
            
            logger.info(f"VisionStory API 요청 URL: {self.base_url}/video")
            logger.info(f"VisionStory API 요청 페이로드: {payload}")
            
            response = requests.post(
                f"{self.base_url}/video",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"VisionStory API 응답: status={response.status_code}, content={response.text[:500]}")
            
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
    
    def get_recent_videos(self) -> Dict[str, Any]:
        """최근 생성된 영상 목록을 가져옵니다."""
        try:
            headers = {
                "X-API-Key": self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/videos",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"VisionStory 영상 목록 조회 성공: {len(result.get('data', {}).get('videos', []))}개")
                return result
            else:
                logger.error(f"VisionStory 영상 목록 조회 실패: {response.status_code}")
                return {"success": False, "error": "영상 목록을 가져올 수 없습니다."}
            
        except Exception as e:
            logger.error(f"VisionStory 영상 목록 조회 중 오류: {str(e)}")
            return {"success": False, "error": str(e)} 