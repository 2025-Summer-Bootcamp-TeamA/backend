import logging
from typing import Optional, Dict, Any
from apps.core.services.entities.artwork_extracted_info import ArtworkExtractedInfo
from apps.core.services.entities.video_script_info import VideoScriptInfo
from apps.core.services.usecases.basic_artwork_extractor import BasicArtworkExtractor, ArtworkTitleNotFoundError
from apps.core.services.usecases.web_search_enricher import WebSearchEnricher
from apps.core.services.usecases.content_fetch_enricher import ContentFetchEnricher
from apps.core.services.usecases.video_script_generator import VideoScriptGenerator

logger = logging.getLogger(__name__)


class ArtworkInfoOrchestrator:
    """전체 작품 정보 추출 및 보강 플로우를 조정하는 서비스"""
    
    def __init__(self, 
                 basic_extractor: Optional[BasicArtworkExtractor] = None,
                 web_enricher: Optional[WebSearchEnricher] = None,
                 content_enricher: Optional[ContentFetchEnricher] = None,
                 script_generator: Optional[VideoScriptGenerator] = None):
        """
        ArtworkInfoOrchestrator 초기화
        
        Args:
            basic_extractor: 기본 추출 서비스
            web_enricher: 웹 검색 보강 서비스
            content_enricher: 콘텐츠 Fetch 보강 서비스
            script_generator: 영상 스크립트 생성 서비스
        """
        self.basic_extractor = basic_extractor or BasicArtworkExtractor()
        self.web_enricher = web_enricher or WebSearchEnricher()
        self.content_enricher = content_enricher or ContentFetchEnricher()
        self.script_generator = script_generator or VideoScriptGenerator()
        
        # 통계
        self.stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "failed_extractions": 0
        }
    
    async def extract_and_enrich(self, ocr_text: str, museum_name: Optional[str] = None) -> ArtworkExtractedInfo:
        """
        OCR 텍스트에서 작품 정보를 추출하고 웹 검색, Fetch, 스크립트 생성을 수행합니다.
        
        Args:
            ocr_text: 박물관에서 촬영한 OCR 텍스트
            museum_name: 박물관/미술관 이름
            
        Returns:
            ArtworkExtractedInfo: 추출 및 보강된 작품 정보 (스크립트 포함)
        """
        self.stats["total_extractions"] += 1
        
        try:
            logger.info("=== 작품 정보 추출 및 보강 시작 ===")
            
            # 1단계: 기본 정보 추출
            logger.info("1단계: 기본 정보 추출")
            basic_info, metadata = self.basic_extractor.extract_basic_info(ocr_text)
            
            # 2단계: 웹 검색 보강
            logger.info("2단계: 웹 검색 보강")
            web_search_info = self.web_enricher.enrich_with_web_search(basic_info, museum_name)
            
            # 3단계: 콘텐츠 Fetch 보강 (웹 검색이 수행된 경우만)
            logger.info("3단계: 콘텐츠 Fetch 보강")
            if web_search_info.performed and web_search_info.search_results:
                logger.info("웹 검색이 수행되었으므로 Fetch 보강을 진행합니다")
                content_fetch_info = await self.content_enricher.enrich_with_content_fetch(web_search_info)
            else:
                logger.info("웹 검색이 수행되지 않았으므로 Fetch 보강을 건너뜁니다 (OCR 설명 존재)")
                from apps.core.services.entities.content_fetch_info import ContentFetchInfo
                from datetime import datetime
                content_fetch_info = ContentFetchInfo(
                    performed=False,
                    fetch_results=None,
                    content_enriched_description=None,
                    fetch_timestamp=datetime.now()
                )
            
            # 4단계: 영상 스크립트 생성
            logger.info("4단계: 영상 스크립트 생성")
            video_script_info = self.script_generator.generate_video_script(
                ArtworkExtractedInfo(
                    basic_info=basic_info,
                    metadata=metadata,
                    web_search=web_search_info,
                    content_fetch=content_fetch_info,
                    video_script=VideoScriptInfo()  # 임시 객체
                )
            )
            
            # 5단계: 최종 결과 통합
            logger.info("5단계: 최종 결과 통합")
            final_result = ArtworkExtractedInfo(
                basic_info=basic_info,
                metadata=metadata,
                web_search=web_search_info,
                content_fetch=content_fetch_info,
                video_script=video_script_info
            )
            
            self.stats["successful_extractions"] += 1
            logger.info("=== 작품 정보 추출 및 보강 완료 ===")
            
            return final_result
            
        except ArtworkTitleNotFoundError:
            # 작품명 없음 에러는 그대로 재발생
            logger.error("작품명을 찾을 수 없습니다")
            self.stats["failed_extractions"] += 1
            raise
        except Exception as e:
            logger.error(f"작품 정보 추출 및 보강 중 오류 발생: {str(e)}")
            self.stats["failed_extractions"] += 1
            raise
    
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