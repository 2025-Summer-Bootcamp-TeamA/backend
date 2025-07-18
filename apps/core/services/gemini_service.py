import json
import logging
import os
from typing import Optional
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class GeminiService:
    """
    간단한 Gemini AI 텍스트 분석 서비스
    
    목적: OCR 텍스트가 작품 설명인지 판단 (true/false 반환)
    """
    
    def __init__(self, credentials_path: Optional[str] = None, location: str = "asia-northeast3"):
        """
        GeminiService 초기화
        
        Args:
            credentials_path: 서비스 계정 JSON 파일 경로
            location: Vertex AI 리전 (기본값: asia-northeast3, 서울)
        """
        # 서비스 계정 인증 설정
        self.project_id = self._setup_credentials(credentials_path)
        self.location = location
        
        # Vertex AI 초기화
        vertexai.init(
            project=self.project_id,
            location=self.location
        )
        
        # Gemini 모델 초기화
        self.model = GenerativeModel('gemini-2.5-flash')
        
        # 간단한 프롬프트
        self.prompt = """
다음 텍스트가 미술 작품에 대한 "설명"입니까?

텍스트: "{text}"

작품 설명이면 "YES", 아니면 "NO"로만 답변하세요.
"""
    
    def _setup_credentials(self, credentials_path: Optional[str]) -> str:
        """
        서비스 계정 인증 정보 설정 및 프로젝트 ID 반환
        """
        try:
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
            raise ValueError(f"Vertex AI 서비스 인증 설정에 실패했습니다: {str(e)}")

    def is_description(self, text: str) -> bool:
        """
        텍스트가 작품 설명인지 판단
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            bool: 설명이면 True, 아니면 False
        """
        if not text or len(text.strip()) < 10:
            return False
        
        try:
            # Vertex AI Gemini 호출
            prompt = self.prompt.format(text=text.strip())
            response = self.model.generate_content(prompt)
            
            # 응답 추출
            if hasattr(response, 'candidates') and response.candidates:
                if response.candidates[0].content.parts:
                    answer = response.candidates[0].content.parts[0].text.strip().upper()
                    return "YES" in answer
            
            return False
            
        except Exception as e:
            logger.error(f"Vertex AI 호출 실패: {str(e)}")
            # 간단한 fallback: 길이 기반 판단
            return len(text) > 50 and ('.' in text or '다' in text)

    def test_connection(self) -> bool:
        """Vertex AI Gemini 연결 테스트"""
        try:
            response = self.model.generate_content("테스트")
            return bool(response.candidates[0].content.parts[0].text)
        except Exception as e:
            logger.error(f"연결 테스트 실패: {e}")
            return False
