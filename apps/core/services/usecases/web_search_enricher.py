import logging
import asyncio
from datetime import datetime
from typing import Optional

from apps.core.services.entities.artwork_basic_info import ArtworkBasicInfo
from apps.core.services.entities.web_search_info import WebSearchInfo
from apps.core.services.externals.brave_service import brave_search

logger = logging.getLogger(__name__)


class WebSearchEnricher:
    """웹 검색으로 정보를 보강하는 서비스"""

    def __init__(self, brave_service: Optional[callable] = None):
        """
        WebSearchEnricher 초기화

        Args:
            brave_service: brave_search 함수 (None이면 기본 함수 사용)
        """
        self.brave_service = brave_service or brave_search

    def enrich_with_web_search(self, basic_info: ArtworkBasicInfo, museum_name: Optional[str]) -> WebSearchInfo:
        """기본 작품 정보를 웹 검색으로 보강합니다"""

        if not self.brave_service:
            logger.info("Brave Search 서비스를 사용할 수 없습니다")
            return WebSearchInfo(
                performed=False,
                search_results=None,
                enriched_description=None,
                search_timestamp=datetime.now()
            )

        if self._has_valid_description(basic_info.description):
            logger.info(f"설명이 이미 존재하므로 웹 검색을 건너뜁니다: {basic_info.description[:50]}...")
            return WebSearchInfo(
                performed=False,
                search_results=None,
                enriched_description=None,
                search_timestamp=datetime.now()
            )

        if not museum_name:
            museum_name = ""
        query = f"{basic_info.title} {museum_name}".strip()

        try:
            logger.info(f"웹 검색 시작: {query}")

            # ⛳ brave_search는 dict를 반환하므로 .content 필요 없음
            search_results = asyncio.run(self.brave_service(query, count=5))

            if search_results.get("results"):
                snippets = [item.get("snippet") for item in search_results["results"] if item.get("snippet")]

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
                return WebSearchInfo(
                    performed=True,
                    search_results=search_results,
                    enriched_description=None,
                    search_timestamp=datetime.now()
                )

        except Exception as e:
            logger.error(f"웹 검색 중 오류 발생: {e}")
            return WebSearchInfo(
                performed=False,
                search_results={"success": False, "error": str(e)},
                enriched_description=None,
                search_timestamp=datetime.now()
            )

    def _enrich_description_with_web_data(self, original_description: str, snippets: list) -> str:
        """웹 검색 스니펫을 사용하여 작품 설명을 보강합니다"""
        if not snippets:
            return original_description

        web_info_summary = "\n".join(snippets[:10])
        if original_description and original_description != "작품 설명 없음":
            enriched = f"{original_description}\n\n[웹 검색 추가 정보]\n{web_info_summary}"
        else:
            enriched = f"[웹 검색 정보]\n{web_info_summary}"

        return enriched[:1900] + "\n... (추가 정보 생략)" if len(enriched) > 2000 else enriched

    def _has_valid_description(self, description: str) -> bool:
        """설명이 유효한지 확인합니다"""
        if not description or not description.strip():
            return False

        invalids = [
            "정보 없음", "작품 설명 없음", "설명 없음", "없음",
            "미상", "불명", "unknown", "---", "???", "불분명"
        ]
        if any(invalid in description.lower() for invalid in invalids):
            return False

        return len(description.strip()) >= 10
