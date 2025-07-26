import os
import logging
import requests
import time
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
        
        # 모킹 모드 설정 (크레딧 절약용)
        self.use_mock = os.getenv("VISIONSTORY_USE_MOCK", "false").lower() == "true"
        
        logger.info(f"VisionStory API 초기화: API 키 설정됨={bool(self.api_key)}, 모킹 모드={self.use_mock}")
        
        # 모킹 모드가 아닐 때만 API 키 검증
        if not self.use_mock and not self.api_key:
            logger.error("VISIONSTORY_API_KEY 환경 변수가 설정되지 않았습니다.")
            raise ValueError("VISIONSTORY_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    def get_video_status(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        특정 영상의 생성 상태를 조회합니다.
        
        Args:
            video_id: 조회할 영상 ID
            
        Returns:
            Dict: 영상 상태 정보 또는 None (실패 시)
        """
        try:
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # 공식 문서에 따른 GET 요청
            response = requests.get(
                f"{self.base_url}/video",
                params={"video_id": video_id},
                headers=headers,
                timeout=10
            )
            
            logger.info(f"영상 상태 조회 응답: status={response.status_code}, content={response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 공식 문서에 따른 응답 구조 확인
                if "data" in result:
                    data = result["data"]
                    logger.info(f"영상 상태 조회 성공: video_id={video_id}, status={data.get('status')}")
                    return data
                else:
                    logger.error(f"영상 상태 조회 응답에 data 필드가 없습니다: {result}")
                    return None
            else:
                logger.error(f"영상 상태 조회 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"영상 상태 조회 중 오류: {str(e)}")
            return None
    
    def wait_for_video_completion(self, video_id: str, max_wait_time: int = 300, poll_interval: int = 10) -> Optional[Dict[str, Any]]:
        """
        영상 생성이 완료될 때까지 대기합니다.
        
        Args:
            video_id: 대기할 영상 ID
            max_wait_time: 최대 대기 시간 (초)
            poll_interval: 폴링 간격 (초)
            
        Returns:
            Dict: 완성된 영상 정보 또는 None (실패 시)
        """
        logger.info(f"영상 생성 완료 대기 시작: video_id={video_id}, max_wait_time={max_wait_time}초")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status_info = self.get_video_status(video_id)
                
                if not status_info:
                    logger.warning(f"영상 상태 조회 실패, {poll_interval}초 후 재시도")
                    time.sleep(poll_interval)
                    continue
                
                status = status_info.get("status", "unknown")
                logger.info(f"영상 상태: {status} (video_id: {video_id})")
                
                if status == "created" or status == "completed":
                    # 영상 생성 완료
                    video_url = status_info.get("video_url", "")
                    if video_url:
                        logger.info(f"영상 생성 완료: {video_url}")
                        return status_info
                    else:
                        logger.warning("영상 생성 완료되었지만 URL이 없습니다")
                        return status_info
                
                elif status == "failed":
                    logger.error(f"영상 생성 실패: {status_info.get('error_message', 'Unknown error')}")
                    return status_info
                
                elif status in ["pending", "creating", "processing"]:
                    logger.info(f"영상 생성 중... ({status})")
                    time.sleep(poll_interval)
                    continue
                
                else:
                    logger.warning(f"알 수 없는 상태: {status}")
                    time.sleep(poll_interval)
                    continue
                    
            except Exception as e:
                logger.error(f"영상 상태 확인 중 오류: {str(e)}")
                time.sleep(poll_interval)
                continue
        
        logger.error(f"영상 생성 대기 시간 초과: {max_wait_time}초")
        return None
    
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
            
            # 모킹 모드 확인
            if self.use_mock:
                logger.info("🚫 모킹 모드 활성화 - 모의 아바타 데이터 반환")
                mock_data = {
                    "data": {
                        "public_avatars": [
                            {"avatar_id": "mock_avatar_1", "name": "Mock Avatar 1", "thumbnail": "https://mock.visionstory.ai/avatar1.jpg"},
                            {"avatar_id": "mock_avatar_2", "name": "Mock Avatar 2", "thumbnail": "https://mock.visionstory.ai/avatar2.jpg"}
                        ],
                        "my_avatars": [
                            {"avatar_id": "mock_my_avatar_1", "name": "My Mock Avatar", "thumbnail": "https://mock.visionstory.ai/my_avatar.jpg"}
                        ],
                        "total_cnt": 3
                    },
                    "message": "success",
                    "server_time": datetime.now().isoformat()
                }
                logger.info(f"모의 아바타 목록 조회 성공: public_avatars={len(mock_data.get('data', {}).get('public_avatars', []))}, my_avatars={len(mock_data.get('data', {}).get('my_avatars', []))}")
                return mock_data
            
            # 실제 VisionStory API 호출
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 공식 문서에 따른 응답 구조 확인
            if "data" in data:
                logger.info(f"아바타 목록 조회 성공: public_avatars={len(data.get('data', {}).get('public_avatars', []))}, my_avatars={len(data.get('data', {}).get('my_avatars', []))}")
                return data
            else:
                logger.error(f"아바타 목록 조회 응답에 data 필드가 없습니다: {data}")
                return None
            
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
                    background_color: str = "",
                    wait_for_completion: bool = True) -> VisionStoryVideoInfo:
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
            wait_for_completion: 영상 생성 완료까지 대기할지 여부
            
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
                "model_id": "vs_talk_v1",  # 공식 문서에 따른 기본 모델 ID
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
            
            # 모킹 모드 확인
            if self.use_mock:
                logger.info("🚫 모킹 모드 활성화 - 모의 영상 데이터 반환")
                mock_response_data = {
                    "data": {
                        "video_id": f"mock_video_{int(datetime.now().timestamp())}"
                    },
                    "message": "success",
                    "server_time": datetime.now().isoformat()
                }
                result = mock_response_data
            else:
                # 실제 VisionStory API 호출
                response = requests.post(
                    f"{self.base_url}/video",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                logger.info(f"VisionStory API 응답: status={response.status_code}, content={response.text[:500]}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 공식 문서에 따른 응답 구조 확인
                    if "data" in result and "video_id" in result["data"]:
                        video_id = result["data"]["video_id"]
                        logger.info(f"영상 생성 요청 성공: video_id={video_id}")
                        
                        # 영상 생성 완료까지 대기 (옵션)
                        if wait_for_completion:
                            logger.info(f"영상 생성 완료 대기 시작: {video_id}")
                            
                            completed_info = self.wait_for_video_completion(video_id)
                            if completed_info:
                                # 완성된 정보로 업데이트
                                result["data"].update(completed_info)
                                logger.info("영상 생성 완료 대기 성공")
                            else:
                                logger.warning("영상 생성 완료 대기 실패, 초기 정보 사용")
                    else:
                        logger.error(f"VisionStory API 응답에 video_id가 없습니다: {result}")
                        return VisionStoryVideoInfo(
                            video_id="",
                            video_url="",
                            thumbnail_url="",
                            status="error",
                            avatar_id=avatar_id,
                            voice_id=voice_id,
                            aspect_ratio=aspect_ratio,
                            resolution=resolution,
                            emotion=emotion,
                            background_color=background_color,
                            duration=0,
                            cost_credit=0,
                            created_at=datetime.now(),
                            generation_method="visionstory_api",
                            success=False,
                            error_message="API 응답에 video_id가 없습니다"
                        )
                else:
                    error_msg = f"VisionStory API 오류: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return VisionStoryVideoInfo(
                        video_id="",
                        video_url="",
                        thumbnail_url="",
                        status="error",
                        avatar_id=avatar_id,
                        voice_id=voice_id,
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                        emotion=emotion,
                        background_color=background_color,
                        duration=0,
                        cost_credit=0,
                        created_at=datetime.now(),
                        generation_method="visionstory_api",
                        success=False,
                        error_message=error_msg
                    )
            
            # 성공 응답 처리 (모킹/실제 API 공통)
            if result and "data" in result:
                data = result["data"]
                
                # 성공 응답 처리
                video_info = VisionStoryVideoInfo(
                    video_id=data.get("video_id", ""),
                    video_url=data.get("video_url", ""),
                    thumbnail_url=data.get("thumbnail_url", ""),
                    status=data.get("status", "pending"),
                    avatar_id=avatar_id,
                    voice_id=voice_id,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    emotion=emotion,
                    background_color=background_color,
                    duration=data.get("duration", 0),
                    cost_credit=data.get("cost_credit", 0),
                    created_at=datetime.now(),
                    generation_method="mock_api" if self.use_mock else "visionstory_api",
                    success=True
                )
                
                logger.info(f"VisionStory 영상 생성 성공: video_id={video_info.video_id}, status={video_info.status}")
                return video_info
            else:
                logger.error(f"VisionStory API 응답 구조가 올바르지 않습니다: {result}")
                return VisionStoryVideoInfo(
                    video_id="",
                    video_url="",
                    thumbnail_url="",
                    status="error",
                    avatar_id=avatar_id,
                    voice_id=voice_id,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    emotion=emotion,
                    background_color=background_color,
                    duration=0,
                    cost_credit=0,
                    created_at=datetime.now(),
                    generation_method="visionstory_api",
                    success=False,
                    error_message="API 응답 구조가 올바르지 않습니다"
                )
                
        except Exception as e:
            error_msg = f"VisionStory API 호출 중 오류: {str(e)}"
            logger.error(error_msg)
            
            return VisionStoryVideoInfo(
                video_id="",
                video_url="",
                thumbnail_url="",
                status="error",
                avatar_id=avatar_id,
                voice_id=voice_id,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                emotion=emotion,
                background_color=background_color,
                duration=0,
                cost_credit=0,
                created_at=datetime.now(),
                generation_method="mock_api" if self.use_mock else "visionstory_api",
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
            
            logger.info(f"영상 목록 조회 응답: status={response.status_code}, content={response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 공식 문서에 따른 응답 구조 확인
                if "data" in result and "videos" in result["data"]:
                    videos = result["data"]["videos"]
                    logger.info(f"VisionStory 영상 목록 조회 성공: {len(videos)}개")
                    return result
                else:
                    logger.error(f"영상 목록 조회 응답에 data.videos 필드가 없습니다: {result}")
                    return {"success": False, "error": "영상 목록을 가져올 수 없습니다."}
            else:
                logger.error(f"VisionStory 영상 목록 조회 실패: {response.status_code}")
                return {"success": False, "error": "영상 목록을 가져올 수 없습니다."}
            
        except Exception as e:
            logger.error(f"VisionStory 영상 목록 조회 중 오류: {str(e)}")
            return {"success": False, "error": str(e)} 