import logging
from datetime import datetime
from typing import Optional
from apps.core.services.entities.web_search_info import WebSearchInfo
from apps.core.services.entities.content_fetch_info import ContentFetchInfo
from apps.core.services.externals.fetch_service import FetchService

logger = logging.getLogger(__name__)


class ContentFetchEnricher:
    """Fetch MCP로 URL 본문을 가져와서 정보를 보강하는 서비스"""
    
    def __init__(self, fetch_service: Optional[FetchService] = None):
        """
        ContentFetchEnricher 초기화
        
        Args:
            fetch_service: FetchService 인스턴스 (None이면 기본 설정으로 생성)
        """
        try:
            if fetch_service:
                self.fetch_service = fetch_service
            else:
                self.fetch_service = FetchService()
        except ValueError as e:
            logger.warning(f"Fetch 서비스 초기화 실패: {e}")
            self.fetch_service = None
    
    def enrich_with_content_fetch(self, web_search_info: WebSearchInfo) -> ContentFetchInfo:
        """
        웹 검색 결과를 바탕으로 URL 본문을 가져와서 정보를 보강합니다.
        """
        # Fetch 서비스가 없으면 빈 결과 반환
        if not self.fetch_service:
            logger.info("Fetch 서비스를 사용할 수 없습니다")
            return ContentFetchInfo(
                performed=False,
                fetch_results=None,
                content_enriched_description=None,
                fetch_timestamp=datetime.now()
            )
        # 웹 검색이 수행되지 않았거나 결과가 없으면 빈 결과 반환
        if not web_search_info.performed or not web_search_info.search_results:
            logger.info("웹 검색 결과가 없어 Fetch를 수행할 수 없습니다")
            return ContentFetchInfo(
                performed=False,
                fetch_results=None,
                content_enriched_description=None,
                fetch_timestamp=datetime.now()
            )
        # Brave Search에서 스니펫이 아닌 url만 사용하도록 fetch_artwork_urls 호출
        # Fetch를 무조건 시도 (enriched_description 유무와 무관)
        try:
            logger.info("Fetch MCP로 URL 본문 가져오기 시작 (enriched_description 유무와 무관)")
            fetch_results = self.fetch_service.fetch_artwork_urls(web_search_info.search_results, max_urls=3)
            if fetch_results and any(r.get("success") for r in fetch_results):
                content_snippets = self.fetch_service.extract_content_snippets(fetch_results, max_snippets=5)
                content_enriched_description = self._enrich_description_with_content_data(
                    original_description=web_search_info.enriched_description,
                    content_snippets=content_snippets
                )
                logger.info(f"Fetch 성공: {len([r for r in fetch_results if r.get('success')])}개 URL")
                return ContentFetchInfo(
                    performed=True,
                    fetch_results=fetch_results,
                    content_enriched_description=content_enriched_description,
                    fetch_timestamp=datetime.now()
                )
            else:
                logger.info("Fetch 결과가 없습니다")
                return ContentFetchInfo(
                    performed=True,
                    fetch_results=fetch_results,
                    content_enriched_description=None,
                    fetch_timestamp=datetime.now()
                )
        except Exception as e:
            logger.error(f"Fetch MCP 오류: {str(e)}")
            return ContentFetchInfo(
                performed=False,
                fetch_results=[],
                content_enriched_description=None,
                fetch_timestamp=datetime.now()
            )
    
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
        if original_description and original_description != "작품 설명 없음":
            enriched = f"{original_description}\n\n[본문 내용 추가 정보]\n{content_summary}"
        else:
            enriched = f"[본문 내용 정보]\n{content_summary}"
        
        # 길이 제한 (너무 길면 자르기)
        if len(enriched) > 3000:
            enriched = enriched[:2800] + "\n... (추가 정보 생략)"
        
        return enriched 