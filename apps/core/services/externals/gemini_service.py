import json
import logging
import os
from typing import Optional, Dict, Any
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationResponse

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Google Vertex AI Gemini 모델 서비스
    
    기능:
    - Gemini 모델 초기화 및 관리
    - 기본 텍스트 생성 API 제공
    - 인증 및 프로젝트 설정 관리
    """
    
    def __init__(self, 
                 credentials_path: Optional[str] = None, 
                 location: str = "asia-northeast3",
                 model_name: str = "gemini-2.5-flash"):
        """
        GeminiService 초기화
        
        Args:
            credentials_path: 서비스 계정 파일 경로 (None이면 환경변수 사용)
            location: Vertex AI 리전 (기본값: 서울)
            model_name: 사용할 Gemini 모델명
        """
        self.model_name = model_name
        self.location = location
        
        # 인증 및 프로젝트 설정
        self.project_id = self._setup_credentials(credentials_path)
        
        # Vertex AI 초기화
        self._initialize_vertex_ai()
        
        # Gemini 모델 로드
        self._load_model()
        
        # 사용 통계
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        
        logger.info(f"GeminiService 초기화 완료 - 프로젝트: {self.project_id}, 모델: {model_name}")
    
    def generate_content(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Gemini 모델에 프롬프트를 전송하고 응답을 받습니다
        
        Args:
            prompt: 전송할 프롬프트
            **kwargs: 추가 생성 파라미터
            
        Returns:
            생성된 텍스트 응답 또는 None (실패 시)
        """
        self.stats["total_requests"] += 1
        
        try:
            # Gemini API 호출
            response = self.model.generate_content(prompt, **kwargs)
            
            if hasattr(response, 'candidates') and response.candidates:
                # 응답 텍스트 추출
                response_text = response.candidates[0].content.parts[0].text.strip()
                
                self.stats["successful_requests"] += 1
                logger.debug(f"Gemini 응답 성공: {len(response_text)} 문자")
                
                return response_text
            else:
                logger.warning("Gemini 응답에 candidates가 없음")
                self.stats["failed_requests"] += 1
                return None
                
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            self.stats["failed_requests"] += 1
            return None
    
    def generate_content_full_response(self, prompt: str, **kwargs) -> Optional[GenerationResponse]:
        """
        전체 응답 객체를 반환 (고급 사용)
        
        Args:
            prompt: 전송할 프롬프트
            **kwargs: 추가 생성 파라미터
            
        Returns:
            GenerationResponse 객체 또는 None
        """
        self.stats["total_requests"] += 1
        
        try:
            response = self.model.generate_content(prompt, **kwargs)
            self.stats["successful_requests"] += 1
            return response
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            self.stats["failed_requests"] += 1
            return None
    
    def _setup_credentials(self, credentials_path: Optional[str]) -> str:
        """서비스 계정 인증 정보 설정"""
        try:
            # 1. 환경변수에서 직접 서비스 계정 정보 확인
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
            if project_id:
                logger.info(f"환경변수에서 프로젝트 ID 사용: {project_id}")
                return project_id
            
            # 2. 파일에서 서비스 계정 정보 읽기
            if credentials_path:
                cred_file = credentials_path
            else:
                cred_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if not cred_file:
                    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되지 않았습니다.")
            
            if not os.path.exists(cred_file):
                raise FileNotFoundError(f"서비스 계정 파일을 찾을 수 없습니다: {cred_file}")
            
            # 프로젝트 ID 추출
            with open(cred_file, 'r') as f:
                service_account_info = json.load(f)
                project_id = service_account_info.get('project_id')
                if not project_id:
                    raise ValueError("서비스 계정 파일에 project_id가 없습니다.")
            
            return project_id
                
        except Exception as e:
            logger.error(f"서비스 계정 인증 설정 실패: {str(e)}")
            raise ValueError(f"Vertex AI 서비스 인증 설정에 실패했습니다: {str(e)}") from e
    
    def _initialize_vertex_ai(self):
        """Vertex AI 초기화"""
        try:
            vertexai.init(
                project=self.project_id,
                location=self.location
            )
            logger.info(f"Vertex AI 초기화 완료 - 프로젝트: {self.project_id}, 리전: {self.location}")
        except Exception as e:
            logger.error(f"Vertex AI 초기화 실패: {e}")
            raise ValueError(f"Vertex AI 초기화에 실패했습니다: {str(e)}") from e
    
    def _load_model(self):
        """Gemini 모델 로드"""
        try:
            self.model = GenerativeModel(self.model_name)
            logger.info(f"Gemini 모델 로드 완료: {self.model_name}")
        except Exception as e:
            logger.error(f"Gemini 모델 로드 실패: {e}")
            raise ValueError(f"Gemini 모델 로드에 실패했습니다: {str(e)}") from e
    
    def get_stats(self) -> Dict[str, Any]:
        """서비스 사용 통계 반환"""
        total = self.stats["total_requests"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "success_rate": self.stats["successful_requests"] / total * 100,
            "failure_rate": self.stats["failed_requests"] / total * 100
        }
    
    def get_model_info(self) -> Dict[str, str]:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "project_id": self.project_id,
            "location": self.location
        }
    
GEMINI_SERVICE = GeminiService()
