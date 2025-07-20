import json
import logging
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from .gemini_service import GeminiService
from .brave_service import BraveSearchService
from .fetch_service import FetchService

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
    # Brave Search 관련 필드
    web_search_performed: bool = False
    web_search_results: Optional[Dict] = None
    web_enriched_description: Optional[str] = None
    # Fetch 관련 필드
    fetch_performed: bool = False
    fetch_results: Optional[List[Dict]] = None
    content_enriched_description: Optional[str] = None


class ArtworkInfoExtractor:
    """
    OCR 텍스트에서 Gemini AI를 사용하여 작품 정보를 추출하는 서비스
    
    기능:
    - 작품명, 작가, 연도, 설명을 구조화하여 추출
    - 정보가 없는 경우 의미있는 기본값 제공
    - JSON 구조화된 응답
    """
    
    def __init__(self, gemini_service: Optional[GeminiService] = None, brave_service: Optional[BraveSearchService] = None, fetch_service: Optional[FetchService] = None):
        """
        ArtworkInfoExtractor 초기화
        
        Args:
            gemini_service: GeminiService 인스턴스 (None이면 기본 설정으로 생성)
            brave_service: BraveSearchService 인스턴스 (None이면 기본 설정으로 생성)
            fetch_service: FetchService 인스턴스 (None이면 기본 설정으로 생성)
        """
        # Gemini 서비스 설정
        if gemini_service:
            self.gemini_service = gemini_service
        else:
            self.gemini_service = GeminiService()
        
        # Brave Search 서비스 설정
        try:
            if brave_service:
                self.brave_service = brave_service
            else:
                self.brave_service = BraveSearchService()
        except ValueError as e:
            logger.warning(f"Brave Search 서비스 초기화 실패: {e}")
            self.brave_service = None
        
        # Fetch 서비스 설정
        try:
            if fetch_service:
                self.fetch_service = fetch_service
            else:
                self.fetch_service = FetchService()
        except ValueError as e:
            logger.warning(f"Fetch 서비스 초기화 실패: {e}")
            self.fetch_service = None
        
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
    
    def extract_artwork_info(self, ocr_text: str, museum_name: Optional[str] = None) -> ArtworkExtractedInfo:
        """
        OCR 텍스트에서 작품 정보를 추출하고 웹 검색으로 보강
        
        Args:
            ocr_text: 박물관에서 촬영한 OCR 텍스트
            museum_name: 박물관/미술관 이름 (Brave Search에 사용)
            
        Returns:
            ArtworkExtractedInfo: 추출된 작품 정보 (웹 검색 결과 포함)
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
                    
                    # 작품명이 확인되면 웹 검색 수행
                    enriched_result = self._perform_web_search(result, museum_name)
                    
                    self.stats["successful_extractions"] += 1
                    return enriched_result
            
            # Gemini 응답 실패 - fallback 시도
            fallback_result = self._create_fallback_result(ocr_text, "gemini_response_failed")
            
            # 작품명 검증 - fallback도 실패하면 에러
            if self._is_invalid_title(fallback_result.title):
                raise ArtworkTitleNotFoundError(
                    f"작품명을 확인할 수 없어 저장할 수 없습니다. OCR 텍스트: {ocr_text[:50]}..."
                )
            
            # fallback도 작품명이 확인되면 웹 검색 수행
            enriched_fallback = self._perform_web_search(fallback_result, museum_name)
            
            self.stats["failed_extractions"] += 1
            return enriched_fallback
            
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
            
            # 예외 fallback도 작품명이 확인되면 웹 검색 수행
            enriched_exception_fallback = self._perform_web_search(fallback_result, museum_name)
            
            self.stats["failed_extractions"] += 1
            return enriched_exception_fallback
    
    def _build_extraction_prompt(self, ocr_text: str) -> str:
        """Gemini용 작품 정보 추출 및 다듬기 프롬프트 구성"""
        
        return f"""다음은 박물관이나 미술관에서 촬영한 작품 설명판의 OCR 텍스트입니다. 
OCR로 인식된 텍스트는 어색하거나 오타가 있을 수 있으므로, 자연스럽고 정확한 한국어로 다듬어서 작품 정보를 추출해주세요.

OCR 텍스트:
\"\"\"
{ocr_text}
\"\"\"

추출 및 다듬기 요구사항:
1. 작품명 (title): 작품의 제목을 자연스럽게 다듬기
   - OCR 오타 수정 (예: "모나리자" → "모나리자")
   - 불필요한 기호나 공백 제거
   - 작품명이 명확하지 않으면 "정보 없음"

2. 작가명 (artist): 작가의 이름을 정확하게 다듬기
   - 외국 작가명은 한국어 표기법으로 통일 (예: "Leonardo da Vinci" → "레오나르도 다 빈치")
   - 작가명 오타 수정
   - 작가 정보가 없으면 "정보 없음"

3. 제작연도 (year): 연도를 명확하게 정리
   - "1889년", "1503-1519", "16세기" 등 원본 형태 유지
   - 연도 범위는 그대로 유지
   - 연도 정보가 없으면 "정보 없음"

4. 작품설명 (description): 설명을 자연스럽고 읽기 쉽게 다듬기
   - OCR 오타 수정 및 문장 부호 정리
   - 어색한 표현을 자연스럽게 수정
   - 문장 구조를 명확하게 정리
   - 설명이 없으면 "정보 없음"

다듬기 규칙:
- OCR 오타를 정확한 한국어로 수정
- 불필요한 공백, 기호, 특수문자 제거
- 문장을 자연스럽고 읽기 쉽게 정리
- 작품 정보의 의미는 그대로 유지
- 추측하지 말고 텍스트에 명시된 내용만 다듬기

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
    
    def _perform_web_search(self, artwork_info: ArtworkExtractedInfo, museum_name: Optional[str]) -> ArtworkExtractedInfo:
        """
        작품 정보를 바탕으로 웹 검색을 수행하여 정보를 보강합니다.
        
        Args:
            artwork_info: 기본 작품 정보
            museum_name: 박물관/미술관 이름
            
        Returns:
            ArtworkExtractedInfo: 웹 검색 결과가 포함된 작품 정보
        """
        # Brave Search 서비스가 없으면 원본 그대로 반환
        if not self.brave_service:
            logger.info("Brave Search 서비스를 사용할 수 없습니다")
            return artwork_info
        
        # 박물관 이름이 없으면 작품명만으로 검색
        if not museum_name:
            logger.info(f"박물관 이름이 없어 작품명만으로 검색: {artwork_info.title}")
            museum_name = ""
        
        try:
            logger.info(f"웹 검색 시작: '{artwork_info.title}' at '{museum_name}'")
            
            # Brave Search 수행
            search_results = self.brave_service.search_artwork(
                artwork_title=artwork_info.title,
                museum_name=museum_name,
                limit=5
            )
            
            if search_results.get("success") and search_results.get("results"):
                logger.info(f"웹 검색 성공: {search_results['total_count']}개 결과")
                
                # 검색 스니펫 추출
                snippets = self.brave_service.extract_search_snippets(search_results)
                
                # 웹 검색 정보로 설명 보강
                enriched_description = self._enrich_description_with_web_data(
                    original_description=artwork_info.description,
                    snippets=snippets
                )
                
                # Fetch MCP로 URL 본문 가져오기
                fetch_results = None
                content_enriched_description = None
                
                if self.fetch_service:
                    try:
                        logger.info("Fetch MCP로 URL 본문 가져오기 시작")
                        fetch_results = self.fetch_service.fetch_artwork_urls(search_results, max_urls=3)
                        
                        if fetch_results and any(r.get("success") for r in fetch_results):
                            # Fetch 결과에서 스니펫 추출
                            content_snippets = self.fetch_service.extract_content_snippets(fetch_results, max_snippets=5)
                            
                            # 본문 내용으로 추가 보강
                            content_enriched_description = self._enrich_description_with_content_data(
                                original_description=enriched_description,
                                content_snippets=content_snippets
                            )
                            
                            logger.info(f"Fetch 성공: {len([r for r in fetch_results if r.get('success')])}개 URL")
                        else:
                            logger.info("Fetch 결과가 없습니다")
                            
                    except Exception as e:
                        logger.error(f"Fetch MCP 오류: {str(e)}")
                        fetch_results = []
                else:
                    logger.info("Fetch 서비스를 사용할 수 없습니다")
                
                # 새로운 ArtworkExtractedInfo 생성 (기존 정보 + 웹 검색 + Fetch 결과)
                return ArtworkExtractedInfo(
                    title=artwork_info.title,
                    artist=artwork_info.artist,
                    year=artwork_info.year,
                    description=artwork_info.description,  # 원본 설명 유지
                    confidence=artwork_info.confidence,
                    extraction_method=artwork_info.extraction_method,
                    raw_response=artwork_info.raw_response,
                    success=artwork_info.success,
                    # 웹 검색 관련 필드
                    web_search_performed=True,
                    web_search_results=search_results,
                    web_enriched_description=enriched_description,
                    # Fetch 관련 필드
                    fetch_performed=bool(fetch_results),
                    fetch_results=fetch_results,
                    content_enriched_description=content_enriched_description or enriched_description
                )
            
            else:
                logger.info("웹 검색 결과가 없습니다")
                # 검색했지만 결과 없음
                return ArtworkExtractedInfo(
                    title=artwork_info.title,
                    artist=artwork_info.artist,
                    year=artwork_info.year,
                    description=artwork_info.description,
                    confidence=artwork_info.confidence,
                    extraction_method=artwork_info.extraction_method,
                    raw_response=artwork_info.raw_response,
                    success=artwork_info.success,
                    web_search_performed=True,
                    web_search_results=search_results,
                    web_enriched_description=None
                )
        
        except Exception as e:
            logger.error(f"웹 검색 중 오류 발생: {str(e)}")
            # 검색 실패해도 원본 정보는 반환
            return ArtworkExtractedInfo(
                title=artwork_info.title,
                artist=artwork_info.artist,
                year=artwork_info.year,
                description=artwork_info.description,
                confidence=artwork_info.confidence,
                extraction_method=artwork_info.extraction_method,
                raw_response=artwork_info.raw_response,
                success=artwork_info.success,
                web_search_performed=False,
                web_search_results={"success": False, "error": str(e)},
                web_enriched_description=None
            )
    
    def _enrich_description_with_web_data(self, original_description: str, snippets: list) -> str:
        """
        웹 검색 스니펫을 사용하여 작품 설명을 보강합니다.
        
        Args:
            original_description: 원본 작품 설명
            snippets: 웹 검색에서 추출된 스니펫들
            
        Returns:
            str: 보강된 설명
        """
        if not snippets:
            return original_description
        
        # 웹 검색 정보 요약
        web_info_summary = "\n".join(snippets[:10])  # 상위 10개 스니펫만 사용
        
        # 원본 설명과 웹 정보 결합
        if original_description and original_description != self.default_values["description"]:
            enriched = f"{original_description}\n\n[웹 검색 추가 정보]\n{web_info_summary}"
        else:
            enriched = f"[웹 검색 정보]\n{web_info_summary}"
        
        # 길이 제한 (너무 길면 자르기)
        if len(enriched) > 2000:
            enriched = enriched[:1900] + "\n... (추가 정보 생략)"
        
        return enriched
    
    def _enrich_description_with_content_data(self, original_description: str, content_snippets: list) -> str:
        """
        Fetch MCP로 가져온 본문 내용을 사용하여 작품 설명을 추가 보강합니다.
        
        Args:
            original_description: 원본 작품 설명 (이미 웹 검색으로 보강된 것일 수 있음)
            content_snippets: Fetch MCP에서 추출된 본문 스니펫들
            
        Returns:
            str: 본문 내용으로 추가 보강된 설명
        """
        if not content_snippets:
            return original_description
        
        # 본문 내용 요약
        content_summary = "\n".join(content_snippets[:5])  # 상위 5개 스니펫만 사용
        
        # 기존 설명과 본문 내용 결합
        if original_description and original_description != self.default_values["description"]:
            enriched = f"{original_description}\n\n[본문 내용 추가 정보]\n{content_summary}"
        else:
            enriched = f"[본문 내용 정보]\n{content_summary}"
        
        # 길이 제한 (너무 길면 자르기)
        if len(enriched) > 3000:
            enriched = enriched[:2800] + "\n... (추가 정보 생략)"
        
        return enriched