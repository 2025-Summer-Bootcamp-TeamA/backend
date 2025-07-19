import json
import logging
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)


class ArtworkTitleNotFoundError(Exception):
    """작품명을 찾을 수 없을 때 발생하는 예외"""
    pass


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
    
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        """
        ArtworkInfoExtractor 초기화
        
        Args:
            gemini_service: GeminiService 인스턴스 (None이면 기본 설정으로 생성)
        """
        # Gemini 서비스 설정
        if gemini_service:
            self.gemini_service = gemini_service
        else:
            self.gemini_service = GeminiService()
        
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
            raise ArtworkTitleNotFoundError("빈 OCR 텍스트로 작품명을 확인할 수 없습니다")
        
        try:
            # Gemini AI 프롬프트 구성
            prompt = self._build_extraction_prompt(ocr_text)
            
            # Gemini API 호출
            raw_response = self.gemini_service.generate_content(prompt)
            
            if raw_response:
                # JSON 파싱 및 정보 추출
                extracted_data = self._parse_gemini_response(raw_response)
                
                if extracted_data:
                    result = ArtworkExtractedInfo(
                        title=extracted_data.get("title", self.default_values["title"]),
                        artist=extracted_data.get("artist", self.default_values["artist"]),
                        year=extracted_data.get("year", self.default_values["year"]),
                        description=extracted_data.get("description", self.default_values["description"]),
                        confidence=0.9,
                        extraction_method="gemini_ai_success",
                        raw_response=raw_response[:200],  # 처음 200자만 저장
                        success=True
                    )
                    
                    # 작품명 검증 - 없으면 바로 에러
                    if self._is_invalid_title(result.title):
                        raise ArtworkTitleNotFoundError(
                            f"작품명을 확인할 수 없어 저장할 수 없습니다. OCR 텍스트: {ocr_text[:50]}..."
                        )
                    
                    self.stats["successful_extractions"] += 1
                    return result
            
            # Gemini 응답 실패 - fallback 시도
            fallback_result = self._create_fallback_result(ocr_text, "gemini_response_failed")
            
            # 작품명 검증 - fallback도 실패하면 에러
            if self._is_invalid_title(fallback_result.title):
                raise ArtworkTitleNotFoundError(
                    f"작품명을 확인할 수 없어 저장할 수 없습니다. OCR 텍스트: {ocr_text[:50]}..."
                )
            
            self.stats["failed_extractions"] += 1
            return fallback_result
            
        except ArtworkTitleNotFoundError:
            # 작품명 없음 에러는 그대로 재발생
            raise
        except Exception as e:
            logger.error(f"Gemini 추출 실패: {e}")
            
            # 다른 에러는 fallback 시도
            fallback_result = self._create_fallback_result(ocr_text, f"gemini_error: {str(e)[:50]}")
            
            # fallback도 작품명 없으면 에러
            if self._is_invalid_title(fallback_result.title):
                raise ArtworkTitleNotFoundError(
                    f"작품명을 확인할 수 없어 저장할 수 없습니다. OCR 텍스트: {ocr_text[:50]}..."
                )
            
            self.stats["failed_extractions"] += 1
            return fallback_result
    
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
    
    def _is_invalid_title(self, title: str) -> bool:
        """작품명이 유효하지 않은지 검사"""
        if not title or not title.strip():
            return True
        
        # 기본값들
        if title == self.default_values["title"]:
            return True
        
        # 무의미한 제목들
        invalid_titles = [
            "정보 없음", "정보없음", "불명", "미상", "제목없음", "무제", 
            "???", "---", "unknown", "없음", "확인불가", "불분명"
        ]
        
        if title.strip().lower() in [t.lower() for t in invalid_titles]:
            return True
        
        # 너무 짧은 제목 (2글자 미만)
        if len(title.strip()) < 2:
            return True
        
        # 숫자만 있는 경우
        if title.strip().isdigit():
            return True
        
        return False
    
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