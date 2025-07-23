import logging
import asyncio
from datetime import datetime
from typing import Optional
from apps.core.services.entities.artwork_basic_info import ArtworkBasicInfo
from apps.core.services.entities.web_search_info import WebSearchInfo
from apps.core.services.externals.brave_service import brave_search
from apps.core.services.externals.gemini_service import GeminiService
from apps.core.services.externals.fetch_service import FetchService

logger = logging.getLogger(__name__)


def _run_async_safely(coro):
    """
    안전하게 비동기 코루틴을 실행합니다.
    이미 실행 중인 event loop가 있으면 새로운 루프를 생성합니다.
    """
    try:
        # 현재 실행 중인 event loop가 있는지 확인
        loop = asyncio.get_running_loop()
        if loop.is_running():
            # 이미 실행 중인 루프가 있으면 새로운 스레드에서 실행
            import threading
            import queue
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                try:
                    result = new_loop.run_until_complete(coro)
                    result_queue.put(result)
                except Exception as e:
                    exception_queue.put(e)
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=run_in_new_loop)
            thread.start()
            thread.join()
            
            if not exception_queue.empty():
                raise exception_queue.get()
            
            return result_queue.get()
    except RuntimeError:
        # 실행 중인 event loop가 없으면 새로 생성
        pass
    
    # 기본적으로 asyncio.run 사용
    return asyncio.run(coro)


class WebSearchEnricher:
    """웹 검색을 통해 작품 정보를 보강하는 서비스"""
    
    def __init__(self, brave_service=None, gemini_service: Optional[GeminiService] = None, fetch_service: Optional[FetchService] = None):
        self.brave_service = brave_service or brave_search
        self.gemini_service = gemini_service or GeminiService()
        self.fetch_service = fetch_service or FetchService()

    def enrich_with_web_search(self, basic_info: ArtworkBasicInfo, museum_name: Optional[str]) -> WebSearchInfo:
        if not self.brave_service:
            logger.info("Brave Search 서비스를 사용할 수 없습니다")
            return WebSearchInfo(
                performed=False,
                search_results=None,
                description="정보를 찾을 수 없습니다.",
                enriched_description=None,
                search_timestamp=datetime.now()
            )

        # 1. OCR 설명이 있으면 Gemini로 오타 보정만 수행
        if self._has_valid_description(basic_info.description):
            logger.info(f"설명이 이미 존재하므로 웹 검색을 건너뜁니다: {basic_info.description[:50]}...")
            # Gemini로 오타/문장 보정
            prompt = (
                f"아래는 OCR로 추출한 작품 설명입니다. 오타, 띄어쓰기, 문장 부호, 어색한 표현을 자연스럽게 보정해 주세요.\n"
                f"---\n{basic_info.description}\n---\n"
                "보정된 설명만 출력하세요."
            )
            gemini_description = self.gemini_service.generate_content(prompt)
            enriched_description = gemini_description or basic_info.description
            return WebSearchInfo(
                performed=False,
                search_results=None,
                description=enriched_description,
                enriched_description=enriched_description,
                search_timestamp=datetime.now()
            )

        # 2. 설명이 없으면 fetch MCP + Gemini 요약
        if not museum_name:
            museum_name = ""
        query = f"{basic_info.title} {museum_name}".strip()
        logger.info(f"📣 최종 검색 쿼리: '{query}'")

        try:
            search_results = _run_async_safely(self.brave_service(query, count=5))
            logger.info(f"웹 검색 완료: {search_results}")
            
            urls = []
            if search_results.get("results"):
                for item in search_results["results"]:
                    if isinstance(item, dict) and item.get("url"):
                        urls.append(item["url"])
                    elif isinstance(item, str):
                        urls.append(item)

            if urls:
                logger.info(f"URL 추출 완료: {len(urls)}개")
                fetch_results = _run_async_safely(self.fetch_service.fetch_urls(urls, max_concurrent=3, timeout=30))
                all_contents = [r["content"] for r in fetch_results if r.get("success") and r.get("content")]
                if all_contents:
                    logger.info(f"콘텐츠 추출 완료: {len(all_contents)}개")
                    prompt = (
                        f"다음은 '{basic_info.title}' 작품에 대한 다양한 웹 본문입니다.\n"
                        "이 정보들을 참고하여, 관람객이 이해하기 쉽고 풍부한 작품 설명을 500자 이내로 써주세요.\n\n"
                    )
                    for i, content in enumerate(all_contents, 1):
                        prompt += f"[자료 {i}]\n{content[:1000]}\n\n"
                    logger.info("Gemini로 설명 생성 시작")
                    gemini_description = self.gemini_service.generate_content(prompt)
                    enriched_description = gemini_description or "정보를 찾을 수 없습니다."
                    logger.info(f"설명 생성 완료: {enriched_description[:100]}...")
                else:
                    enriched_description = "정보를 찾을 수 없습니다."
                    logger.info("웹 콘텐츠가 없어 기본 설명 사용")
                    
                return WebSearchInfo(
                    performed=True,
                    search_results=search_results,
                    description=enriched_description,
                    enriched_description=enriched_description,
                    search_timestamp=datetime.now()
                )
            else:
                logger.info("URL이 추출되지 않음")
                search_results = {"success": False, "error": "검색 결과 없음", "results": []}
                return WebSearchInfo(
                    performed=True,
                    search_results=search_results,
                    description="정보를 찾을 수 없습니다.",
                    enriched_description=None,
                    search_timestamp=datetime.now()
                )
        except Exception as e:
            logger.error(f"웹 검색 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
            prompt = f"""
            다음은 작품에 대한 기본 정보입니다:
            {original_description}

            그리고 다음은 웹에서 수집한 추가 정보입니다:
            {web_info_summary}

            이 정보들을 종합하여 풍부하고 완전한 작품 설명을 500자 이내로 작성해주세요.
            """
        else:
            prompt = f"""
            다음은 웹에서 수집한 작품 정보입니다:
            {web_info_summary}

            이 정보를 기반으로 작품에 대한 완전한 설명을 500자 이내로 작성해주세요.
            """

        return self.gemini_service.generate_content(prompt) or original_description

    def _has_valid_description(self, description: str) -> bool:
        """유효한 설명이 있는지 확인"""
        if not description:
            return False
        
        description = description.strip()
        if not description or description == "작품 설명 없음":
            return False
        
        # 너무 짧은 설명은 유효하지 않다고 간주
        if len(description) < 10:
            return False
        
        return True
