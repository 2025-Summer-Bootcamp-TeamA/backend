import json
import logging
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
import vertexai
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)


@dataclass
class ArtworkExtractedInfo:
    """추출된 작품 정보"""
    title: str = "작품명 확인 불가"
    artist: str = "작가 정보 없음"
    year: str = "제작연도 미상"
    description: str = "작품 설명 없음"
    confidence: float = 0.0
    extraction_method: str = "gemini_ai"
    raw_response: str = ""
    success: bool = True


class ArtworkInfoExtractor:
    """
    OCR 텍스트에서 Gemini AI를 사용하여 작품 정보를 추출하는 서비스
    
    기능:
    - 작품명, 작가, 연도, 설명을 구조화하여 추출
    - 정보가 없는 경우 의미있는 기본값 제공
    - JSON 구조화된 응답
    """
    
    def __init__(self, credentials_path: Optional[str] = None, location: str = "asia-northeast3"):
        """
        ArtworkInfoExtractor 초기화
        
        Args:
            credentials_path: Gemini 서비스 계정 파일 경로
            location: Vertex AI 리전 (기본값: 서울)
        """
        # Gemini 설정
        self.project_id = self._setup_credentials(credentials_path)
        self.location = location
        
        # Vertex AI 초기화
        vertexai.init(
            project=self.project_id,
            location=self.location
        )
        
        # Gemini 모델 초기화
        self.model = GenerativeModel('gemini-2.5-flash')
        
        # 기본값 설정
        self.default_values = {
            "title": "작품명 확인 불가",
            "artist": "작가 정보 없음", 
            "year": "제작연도 미상",
            "description": "작품 설명 없음"
        }
        
        # 통계
        self.stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "failed_extractions": 0
        }
    
    def extract_artwork_info(self, ocr_text: str) -> ArtworkExtractedInfo:
        """
        OCR 텍스트에서 작품 정보를 추출
        
        Args:
            ocr_text: 박물관에서 촬영한 OCR 텍스트
            
        Returns:
            ArtworkExtractedInfo: 추출된 작품 정보
        """
        self.stats["total_extractions"] += 1
        
        if not ocr_text or not ocr_text.strip():
            return ArtworkExtractedInfo(
                confidence=0.0,
                extraction_method="input_validation_failed",
                success=False
            )
        
        try:
            # Gemini AI 프롬프트 구성
            prompt = self._build_extraction_prompt(ocr_text)
            
            # Gemini API 호출
            response = self.model.generate_content(prompt)
            
            if hasattr(response, 'candidates') and response.candidates:
                raw_response = response.candidates[0].content.parts[0].text.strip()
                
                # JSON 파싱 및 정보 추출
                extracted_data = self._parse_gemini_response(raw_response)
                
                if extracted_data:
                    self.stats["successful_extractions"] += 1
                    
                    return ArtworkExtractedInfo(
                        title=extracted_data.get("title", self.default_values["title"]),
                        artist=extracted_data.get("artist", self.default_values["artist"]),
                        year=extracted_data.get("year", self.default_values["year"]),
                        description=extracted_data.get("description", self.default_values["description"]),
                        confidence=0.9,
                        extraction_method="gemini_ai_success",
                        raw_response=raw_response[:200],  # 처음 200자만 저장
                        success=True
                    )
            
            # Gemini 응답 실패
            self.stats["failed_extractions"] += 1
            return self._create_fallback_result(ocr_text, "gemini_response_failed")
            
        except Exception as e:
            logger.error(f"Gemini 추출 실패: {e}")
            self.stats["failed_extractions"] += 1
            return self._create_fallback_result(ocr_text, f"gemini_error: {str(e)[:50]}")
    
    def _build_extraction_prompt(self, ocr_text: str) -> str:
        """Gemini용 작품 정보 추출 프롬프트 구성"""
        
        return f"""다음은 박물관이나 미술관에서 촬영한 작품 설명판의 OCR 텍스트입니다. 
이 텍스트에서 작품 정보를 정확하게 추출해주세요.

OCR 텍스트:
\"\"\"
{ocr_text}
\"\"\"

추출 요구사항:
1. 작품명 (title): 작품의 제목
2. 작가명 (artist): 작품을 만든 작가의 이름  
3. 제작연도 (year): 작품이 만들어진 연도 (원본 형태 유지)
4. 작품설명 (description): 작품에 대한 설명이나 해설

중요한 규칙:
- 정보가 명확하지 않거나 없으면 "정보 없음"으로 설정
- 추측하지 말고 텍스트에 명시된 내용만 추출
- 한 줄에 여러 정보가 섞여있어도 정확히 구분
- 연도는 "1889년", "1503-1519", "16세기" 등 원본 형태 유지

응답은 반드시 아래 JSON 형식으로만 답변하세요:

{{
  "title": "작품명 또는 정보 없음",
  "artist": "작가명 또는 정보 없음",
  "year": "제작연도 또는 정보 없음", 
  "description": "작품 설명 또는 정보 없음"
}}"""
    
    def _parse_gemini_response(self, response_text: str) -> Optional[Dict[str, str]]:
        """Gemini 응답을 JSON으로 파싱"""
        try:
            # JSON 부분만 추출
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                json_text = response_text[start:end].strip()
            else:
                # JSON 블록 없이 바로 JSON인 경우
                json_text = response_text.strip()
            
            # JSON 파싱
            result = json.loads(json_text)
            
            # 필수 필드 확인 및 기본값 적용
            for field in ["title", "artist", "year", "description"]:
                if field not in result or not result[field] or result[field].strip() == "":
                    result[field] = self.default_values[field]
                elif result[field].strip().lower() in ["null", "없음", "미상", "불명"]:
                    result[field] = self.default_values[field]
                else:
                    # 문자열 정리
                    result[field] = result[field].strip()
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}, 응답: {response_text[:100]}")
            return None
        except Exception as e:
            logger.error(f"응답 처리 실패: {e}")
            return None
    
    def _create_fallback_result(self, ocr_text: str, error_reason: str) -> ArtworkExtractedInfo:
        """AI 실패시 fallback 결과 생성"""
        
        # 간단한 규칙 기반 정보 추출 시도
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
        
        fallback_title = self.default_values["title"]
        fallback_artist = self.default_values["artist"] 
        fallback_year = self.default_values["year"]
        fallback_description = self.default_values["description"]
        
        # 첫 번째 줄을 작품명으로 추정
        if lines:
            first_line = lines[0]
            if len(first_line) <= 50 and not any(char in first_line for char in '.!?'):
                fallback_title = first_line
        
        # 연도 패턴 찾기
        import re
        year_pattern = r'\b(\d{4}(?:-\d{4})?년?|\d{1,2}세기)\b'
        for line in lines:
            year_match = re.search(year_pattern, line)
            if year_match:
                fallback_year = year_match.group(0)
                break
        
        # 긴 텍스트를 설명으로 추정
        for line in lines:
            if len(line) > 30 and ('다.' in line or '이다' in line or '된다' in line):
                fallback_description = line
                break
        
        return ArtworkExtractedInfo(
            title=fallback_title,
            artist=fallback_artist,
            year=fallback_year,
            description=fallback_description,
            confidence=0.3,
            extraction_method=f"fallback_rules ({error_reason})",
            success=False
        )
    
    def _setup_credentials(self, credentials_path: Optional[str]) -> str:
        """서비스 계정 인증 정보 설정"""
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
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """추출 통계 반환"""
        total = self.stats["total_extractions"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "success_rate": self.stats["successful_extractions"] / total * 100,
            "failure_rate": self.stats["failed_extractions"] / total * 100
        } 