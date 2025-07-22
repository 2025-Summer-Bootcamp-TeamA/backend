from datetime import datetime
from typing import Optional
from apps.core.services.entities.artwork_basic_info import ArtworkBasicInfo
from apps.core.services.entities.web_search_info import WebSearchInfo
from apps.core.services.externals.brave_service import brave_search
from apps.core.services.externals.fetch_service import FetchService
from apps.core.services.externals.gemini_service import GEMINI_SERVICE
import asyncio
import logging

logger = logging.getLogger(__name__)

class WebSearchEnricher:
    def __init__(self, brave_service: Optional[callable] = None, fetch_service: Optional[FetchService] = None, gemini_service: Optional[GEMINI_SERVICE] = None):
        self.brave_service = brave_service or brave_search
        self.fetch_service = fetch_service or FetchService()
        self.gemini_service = gemini_service or GEMINI_SERVICE

    def enrich_with_web_search(self, basic_info: ArtworkBasicInfo, museum_name: Optional[str]) -> WebSearchInfo:
        if not self.brave_service:
            logger.info("Brave Search 서비스를 사용할 수 없습니다")
            return WebSearchInfo(
                performed=False,
                search_results=None,
                description=None,
                enriched_description=None,
                search_timestamp=datetime.now()
            )

        if self._has_valid_description(basic_info.description):
            logger.info(f"설명이 이미 존재하므로 웹 검색을 건너뜁니다: {basic_info.description[:50]}...")
            return WebSearchInfo(
                performed=False,
                search_results=None,
                description=basic_info.description,
                enriched_description=basic_info.description,
                search_timestamp=datetime.now()
            )

        if not museum_name:
            museum_name = ""
        query = f"{basic_info.title} {museum_name}".strip()
        logger.info(f"📣 최종 검색 쿼리: '{query}'")

        try:
            search_results = asyncio.run(self.brave_service(query, count=5))

            # Brave Search에서 URL만 받아오므로, Fetch MCP로 본문을 가져와 snippet 생성
            urls = []
            if search_results.get("results"):
                for item in search_results["results"]:
                    if isinstance(item, dict) and item.get("url"):
                        urls.append(item["url"])
                    elif isinstance(item, str):
                        urls.append(item)

            if urls:
                fetch_results = asyncio.run(self.fetch_service.fetch_urls(urls, max_concurrent=3, timeout=30))
                all_contents = [r["content"] for r in fetch_results if r.get("success") and r.get("content")]
                if all_contents:
                    prompt = (
                        f"다음은 '{basic_info.title}' 작품에 대한 다양한 웹 본문입니다.\n"
                        "이 정보들을 참고하여, 관람객이 이해하기 쉽고 풍부한 작품 설명을 500자 이내로 써주세요.\n\n"
                    )
                    for i, content in enumerate(all_contents, 1):
                        prompt += f"[자료 {i}]\n{content[:1000]}\n\n"
                    gemini_description = self.gemini_service.generate_content(prompt)
                    enriched_description = gemini_description or "정보를 찾을 수 없습니다."
                else:
                    enriched_description = "정보를 찾을 수 없습니다."
                return WebSearchInfo(
                    performed=True,
                    search_results=search_results,
                    description=enriched_description,
                    enriched_description=enriched_description,
                    search_timestamp=datetime.now()
                )
            else:
                logger.info("검색 결과가 없습니다.")
                return WebSearchInfo(
                    performed=True,
                    search_results=search_results,
                    description="정보를 찾을 수 없습니다.",
                    enriched_description=None,
                    search_timestamp=datetime.now()
                )

        except Exception as e:
            logger.error(f"웹 검색 중 오류 발생: {e}")
            return WebSearchInfo(
                performed=False,
                search_results={"success": False, "error": str(e)},
                description="정보를 찾을 수 없습니다.",
                enriched_description=None,
                search_timestamp=datetime.now()
            )

    def _enrich_description_with_web_data(self, original_description: str, snippets: list) -> str:
        if not snippets:
            return original_description

        web_info_summary = "\n".join(snippets[:10])
        if original_description and original_description != "작품 설명 없음":
            enriched = f"{original_description}\n\n[웹 검색 추가 정보]\n{web_info_summary}"
        else:
            enriched = f"[웹 검색 정보]\n{web_info_summary}"

        return enriched[:1900] + "\n... (추가 정보 생략)" if len(enriched) > 2000 else enriched

    def _has_valid_description(self, description: str) -> bool:
        if not description or not description.strip():
            return False

        invalids = [
            "정보 없음", "작품 설명 없음", "설명 없음", "없음",
            "미상", "불명", "unknown", "---", "???", "불분명"
        ]
        return not any(invalid in description.lower() for invalid in invalids) and len(description.strip()) >= 10
