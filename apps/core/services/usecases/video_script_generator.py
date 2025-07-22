import logging
from datetime import datetime
from typing import Optional
from apps.core.services.entities.artwork_extracted_info import ArtworkExtractedInfo
from apps.core.services.entities.video_script_info import VideoScriptInfo
from apps.core.services.externals.gemini_service import GEMINI_SERVICE

logger = logging.getLogger(__name__)


class VideoScriptGenerator:
    """VisionStory AI용 영상 스크립트를 생성하는 서비스"""
    
    def __init__(self, gemini_service: Optional[object] = None):
        """
        VideoScriptGenerator 초기화
        
        Args:
            gemini_service: GeminiService 인스턴스 (None이면 전역 싱글톤 인스턴스 사용)
        """
        self.gemini_service = gemini_service or GEMINI_SERVICE
    
    def generate_video_script(self, artwork_info: ArtworkExtractedInfo) -> VideoScriptInfo:
        """
        작품 정보를 바탕으로 VisionStory AI용 영상 스크립트를 생성합니다.
        
        Args:
            artwork_info: 추출 및 보강된 작품 정보
            
        Returns:
            VideoScriptInfo: 생성된 스크립트 정보
        """
        try:
            logger.info("=== 영상 스크립트 생성 시작 ===")
            
            # 스크립트 생성 프롬프트 구성
            prompt = self._build_script_prompt(artwork_info)
            
            # Gemini AI로 스크립트 생성
            raw_response = self.gemini_service.generate_content(prompt)
            
            if raw_response:
                # 스크립트 내용 정리
                script_content = self._clean_script_content(raw_response)
                
                # 스크립트 길이 계산 (대략적인 초 단위)
                script_length = self._calculate_script_length(script_content)
                
                logger.info(f"스크립트 생성 성공: {script_length}초")
                
                return VideoScriptInfo(
                    script_content=script_content,
                    script_length=script_length,
                    generation_method="gemini_ai",
                    generation_timestamp=datetime.now(),
                    success=True
                )
            
            else:
                logger.warning("Gemini AI 응답이 없어 fallback 스크립트 생성")
                return self._create_fallback_script(artwork_info)
                
        except Exception as e:
            logger.error(f"스크립트 생성 중 오류 발생: {str(e)}")
            return VideoScriptInfo(
                script_content="",
                script_length=0,
                generation_method="error",
                generation_timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    def _build_script_prompt(self, artwork_info: ArtworkExtractedInfo) -> str:
        """VisionStory AI용 스크립트 생성 프롬프트 구성"""
        
        # 작품 정보 수집
        title = artwork_info.basic_info.title
        artist = artwork_info.basic_info.artist
        year = artwork_info.basic_info.year
        
        # 설명 정보 수집 (우선순위: 본문 > 웹검색 > 기본)
        description = ""
        if artwork_info.content_fetch.content_enriched_description:
            description = artwork_info.content_fetch.content_enriched_description
        elif artwork_info.web_search.enriched_description:
            description = artwork_info.web_search.enriched_description
        else:
            description = artwork_info.basic_info.description
        
        return f"""다음은 박물관 작품에 대한 정보입니다. 이 정보를 바탕으로 VisionStory AI에서 사용할 영상 나레이션 스크립트를 작성해주세요.

작품 정보:
- 작품명: {title}
- 작가: {artist}
- 제작연도: {year}
- 작품 설명: {description}

스크립트 요구사항:
1. **자연스러운 나레이션**: 마치 전문 해설사가 설명하는 듯한 자연스러운 톤
2. **흥미로운 도입**: 시청자의 관심을 끄는 흥미로운 시작
3. **구체적인 정보**: 작품의 특징, 역사적 의미, 예술적 가치 등
4. **감정적 연결**: 작품이 가진 감정적, 문화적 의미
5. **적절한 길이**: 30초~2분 정도의 영상에 맞는 분량
6. **한국어**: 자연스러운 한국어로 작성
7. **완성된 스크립트**: 바로 나레이션에 사용할 수 있는 완성된 형태

스크립트 작성 규칙:
- 문장은 자연스럽고 듣기 좋게 구성
- 전문 용어는 쉽게 설명
- 작품의 역사적 배경과 예술적 가치를 포함
- 시청자가 작품을 직접 보는 듯한 생생한 묘사
- 감정적이고 몰입감 있는 톤으로 작성

응답은 스크립트 내용만 작성하세요. 다른 설명이나 주석은 포함하지 마세요."""
    
    def _clean_script_content(self, raw_response: str) -> str:
        """Gemini 응답을 깔끔한 스크립트로 정리"""
        # 불필요한 마크다운이나 코드 블록 제거
        if '```' in raw_response:
            start = raw_response.find('```') + 3
            end = raw_response.find('```', start)
            if end != -1:
                raw_response = raw_response[start:end].strip()
        
        # 앞뒤 공백 제거
        script = raw_response.strip()
        
        # 문장 끝 정리
        if not script.endswith(('.', '!', '?')):
            script += '.'
        
        return script
    
    def _calculate_script_length(self, script_content: str) -> int:
        """스크립트 길이를 초 단위로 계산 (대략적)"""
        # 한국어 기준으로 분당 약 300자 정도로 계산
        char_count = len(script_content)
        estimated_seconds = int(char_count / 5)  # 분당 300자 = 초당 5자
        
        # 최소 10초, 최대 120초로 제한
        return max(10, min(120, estimated_seconds))
    
    def _create_fallback_script(self, artwork_info: ArtworkExtractedInfo) -> VideoScriptInfo:
        """AI 실패시 기본 스크립트 생성"""
        title = artwork_info.basic_info.title
        artist = artwork_info.basic_info.artist
        year = artwork_info.basic_info.year
        
        # 기본 스크립트 템플릿
        fallback_script = f"""이 작품은 {artist}가 {year}에 제작한 '{title}'입니다. 이 작품은 예술사에서 중요한 의미를 지니며, 작가의 독특한 기법과 창의성이 잘 드러나 있습니다. 박물관에서 직접 감상하시면 더욱 깊이 있는 예술 경험을 하실 수 있을 것입니다."""
        
        return VideoScriptInfo(
            script_content=fallback_script,
            script_length=self._calculate_script_length(fallback_script),
            generation_method="fallback_template",
            generation_timestamp=datetime.now(),
            success=True
        )
