import logging
from datetime import datetime
from typing import Optional
from apps.core.services.entities.artwork_basic_info import ArtworkBasicInfo
from apps.core.services.entities.web_search_info import WebSearchInfo
from apps.core.services.externals.brave_service import BraveSearchService

logger = logging.getLogger(__name__)


class WebSearchEnricher:
    """웹 검색으로 정보를 보강하는 서비스"""
    
    def __init__(self, brave_service: Optional[BraveSearchService] = None):
        """
        WebSearchEnricher 초기화
        
        Args:
            brave_service: BraveSearchService 인스턴스 (None이면 기본 설정으로 생성)
        """
        try:
            if brave_service:
                self.brave_service = brave_service
            else:
                self.brave_service = BraveSearchService()
        except ValueError as e:
            logger.warning(f"Brave Search 서비스 초기화 실패: {e}")
            self.brave_service = None
    
    def enrich_with_web_search(self, basic_info: ArtworkBasicInfo, museum_name: Optional[str]) -> WebSearchInfo:
        """
        기본 작품 정보를 웹 검색으로 보강합니다.
        
        Args:
            basic_info: 기본 작품 정보
            museum_name: 박물관/미술관 이름
            
        Returns:
            WebSearchInfo: 웹 검색 결과 정보
        """
        # Brave Search 서비스가 없으면 빈 결과 반환
        if not self.brave_service:
            logger.info("Brave Search 서비스를 사용할 수 없습니다")
            return WebSearchInfo(
                performed=False,
                search_results=None,
                enriched_description=None,
                search_timestamp=datetime.now()
            )
        
        # 설명이 이미 있으면 웹 검색 수행하지 않음
        if self._has_valid_description(basic_info.description):
            logger.info(f"설명이 이미 존재하므로 웹 검색을 건너뜁니다: {basic_info.description[:50]}...")
            return WebSearchInfo(
                performed=False,
                search_results=None,
                enriched_description=None,
                search_timestamp=datetime.now()
            )
        
        # 박물관 이름이 없으면 작품명만으로 검색
        if not museum_name:
            logger.info(f"박물관 이름이 없어 작품명만으로 검색: {basic_info.title}")
            museum_name = ""
        
        try:
            logger.info(f"설명이 없어 웹 검색 시작: '{basic_info.title}' at '{museum_name}'")
            
            # Brave Search 수행
            search_results = self.brave_service.search_artwork(
                artwork_title=basic_info.title,
                museum_name=museum_name,
                limit=5
            )
            
            if search_results.get("success") and search_results.get("results"):
                logger.info(f"웹 검색 성공: {search_results['total_count']}개 결과")
                
                # 검색 스니펫 추출
                snippets = self.brave_service.extract_search_snippets(search_results)
                
                # 웹 검색 정보로 설명 보강
                enriched_description = self._enrich_description_with_web_data(
                    original_description=basic_info.description,
                    snippets=snippets
                )
                
                return WebSearchInfo(
                    performed=True,
                    search_results=search_results,
                    enriched_description=enriched_description,
                    search_timestamp=datetime.now()
                )
            
            else:
                logger.info("웹 검색 결과가 없습니다")
                return WebSearchInfo(
                    performed=True,
                    search_results=search_results,
                    enriched_description=None,
                    search_timestamp=datetime.now()
                )
        
        except Exception as e:
            logger.error(f"웹 검색 중 오류 발생: {str(e)}")
            return WebSearchInfo(
                performed=False,
                search_results={"success": False, "error": str(e)},
                enriched_description=None,
                search_timestamp=datetime.now()
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
        if original_description and original_description != "작품 설명 없음":
            enriched = f"{original_description}\n\n[웹 검색 추가 정보]\n{web_info_summary}"
        else:
            enriched = f"[웹 검색 정보]\n{web_info_summary}"
        
        # 길이 제한 (너무 길면 자르기)
        if len(enriched) > 2000:
            enriched = enriched[:1900] + "\n... (추가 정보 생략)"
        
        return enriched 
    
    def _has_valid_description(self, description: str) -> bool:
        """
        설명이 유효한지 확인합니다.
        
        Args:
            description: 확인할 설명
            
        Returns:
            bool: 유효한 설명이 있으면 True
        """
        if not description or not description.strip():
            return False
        
        # 기본값들
        invalid_descriptions = [
            "정보 없음", "정보없음", "작품 설명 없음", "설명 없음", "없음",
            "미상", "불명", "unknown", "---", "???", "불분명"
        ]
        
        description_lower = description.strip().lower()
        for invalid in invalid_descriptions:
            if invalid.lower() in description_lower:
                return False
        
        # 너무 짧은 설명 (10글자 미만)
        if len(description.strip()) < 10:
            return False
        
        return True 