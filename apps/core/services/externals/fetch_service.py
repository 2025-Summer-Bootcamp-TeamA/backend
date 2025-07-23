import os
import logging
import traceback
from typing import List, Dict, Optional
from urllib.parse import urlparse
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio

logger = logging.getLogger(__name__)

class FetchService:
    """
    Fetch MCP를 사용하여 URL 본문을 읽어오는 서비스 (Brave MCP와 동일한 비동기 방식)
    """
    def __init__(self):
        self.smithery_api_key = os.getenv("SMITHERY_API_KEY")
        self.profile = os.getenv("FETCH_MCP_PROFILE")
        if not self.smithery_api_key:
            raise ValueError("SMITHERY_API_KEY 환경변수가 필요합니다.")

    def get_fetch_mcp_url(self):
        return (
            f"https://server.smithery.ai/fetch-mcp/mcp"
            f"?api_key={self.smithery_api_key}&profile={self.profile}"
        )

    async def fetch_url_mcp_async(self, url: str, timeout: int = 30) -> dict:
        mcp_url = self.get_fetch_mcp_url()
        try:
            async with streamablehttp_client(mcp_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    logger.info(f"Fetch MCP tool 시도: fetch_txt for {url}")
                    try:
                        params = {"url": url}
                        result = await session.call_tool("fetch_txt", params)
                        content = getattr(result, "content", None)
                        logger.debug(f"[DEBUG] MCP result: {result}")
                        logger.debug(f"[DEBUG] MCP content: {content}")
                        if isinstance(content, dict):
                            return {
                                "url": url,
                                "success": True,
                                "title": content.get("title", ""),
                                "content": content.get("text", ""),
                                "text_length": len(content.get("text", "")),
                                "error": ""
                            }
                        elif isinstance(content, list):
                            all_texts = [
                                getattr(item, "text", "") for item in content
                                if hasattr(item, "text")
                            ]
                            joined = "\n".join(all_texts)
                            return {
                                "url": url,
                                "success": True,
                                "title": "",
                                "content": joined,
                                "text_length": len(joined),
                                "error": ""
                            }
                        elif hasattr(content, "text"):
                            return {
                                "url": url,
                                "success": True,
                                "title": getattr(content, "title", ""),
                                "content": getattr(content, "text", ""),
                                "text_length": len(getattr(content, "text", "")),
                                "error": ""
                            }
                        else:
                            logger.warning(f"Fetch MCP content 파싱 실패: {content}")
                            return {
                                "url": url,
                                "success": False,
                                "title": "",
                                "content": "",
                                "text_length": 0,
                                "error": "본문 파싱 실패"
                            }
                    except Exception as e:
                        # 502 등 서버 오류는 경고 레벨로 처리 (너무 시끄럽지 않게)
                        if "502 Bad Gateway" in str(e) or "BrokenResourceError" in str(e):
                            logger.warning(f"Fetch MCP 서버 오류 (일시적): {url} - {e}")
                        else:
                            logger.error(f"Fetch MCP tool fetch_txt 실패: {e}")
                            logger.error(traceback.format_exc())
                        return {
                            "url": url,
                            "success": False,
                            "title": "",
                            "content": "",
                            "text_length": 0,
                            "error": f"fetch_txt tool 실패: {e}"
                        }
        except Exception as e:
            logger.error(f"Fetch MCP async 연결 오류 {url}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "url": url,
                "success": False,
                "title": "",
                "content": "",
                "text_length": 0,
                "error": f"연결 오류: {e}"
            }

    async def fetch_urls(self, urls: List[str], max_concurrent: int = 3, timeout: int = 30) -> List[Dict]:
        results = []
        valid_urls = self._filter_urls(urls)
        if not valid_urls:
            logger.warning("유효한 URL이 없습니다.")
            return results
        logger.info(f"Fetch 시작: {len(valid_urls)}개 URL")
        tasks = [self.fetch_url_mcp_async(url, timeout) for url in valid_urls]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        for url, result in zip(valid_urls, raw_results):
            if isinstance(result, Exception):
                logger.error(f"Fetch 개별 오류 {url}: {str(result)}")
                results.append({
                    "url": url,
                    "success": False,
                    "title": "",
                    "content": "",
                    "text_length": 0,
                    "error": f"개별 요청 오류: {str(result)}"
                })
            else:
                results.append(result)
        success_count = len([r for r in results if r['success']])
        total_count = len(results)
        if success_count > 0:
            logger.info(f"Fetch 완료: {success_count}/{total_count}개 성공")
        else:
            logger.warning(f"Fetch 완료: 모든 URL 실패 ({total_count}개)")
        return results

    def fetch_artwork_urls(self, search_results: Dict, max_urls: int = 5) -> List[Dict]:
        """
        Brave Search 결과에서 URL을 추출하여 실제로 fetch MCP로 본문을 가져옵니다.

        Args:
            search_results: BraveSearchService.search_artwork() 결과
            max_urls: 가져올 최대 URL 수

        Returns:
            List[Dict]: fetch MCP 결과 (success, content 등 포함)
        """
        if not search_results or not search_results.get("results"):
            logger.warning("검색 결과가 없습니다.")
            return []

        urls = [r for r in search_results["results"] if isinstance(r, str)]
        if not urls:
            # results가 dict 형태인 경우 URL 추출
            urls = [r.get("url") for r in search_results["results"] if isinstance(r, dict) and r.get("url")]
        
        prioritized_urls = self._prioritize_artwork_urls(urls, max_urls)
        
        # 실제로 fetch MCP를 호출하여 본문을 가져옵니다
        logger.info(f"실제 fetch MCP 호출: {len(prioritized_urls)}개 URL")
        return asyncio.run(self.fetch_urls(prioritized_urls, max_concurrent=3, timeout=30))

    
    def _fetch_single_url(self, url: str, timeout: int) -> Dict:
        """
        단일 URL의 본문을 가져옵니다.
        
        Args:
            url: 가져올 URL
            timeout: 요청 타임아웃
            
        Returns:
            Dict: URL 본문 정보
        """
        try:
            # MCP API 엔드포인트 구성 (쿼리스트링은 params로 전달)
            mcp_url = f"{self._get_mcp_url()}/fetch"
            params = {
                "api_key": self.smithery_api_key,
                "profile": self.profile
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            payload = {
                "url": url,
                "timeout": timeout,
                "extract_text": True,
                "extract_title": True,
                "clean_html": True,
                "max_length": 10000  # 최대 10KB
            }
            logger.debug(f"Fetch MCP API 호출: {url}")
            response = requests.post(
                mcp_url,
                params=params,
                json=payload,
                headers=headers,
                timeout=timeout + 10  # MCP API 타임아웃
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                return {
                    "url": url,
                    "success": True,
                    "title": result.get("title", ""),
                    "content": result.get("text", ""),
                    "text_length": len(result.get("text", "")),
                    "error": ""
                }
            else:
                return {
                    "url": url,
                    "success": False,
                    "title": "",
                    "content": "",
                    "text_length": 0,
                    "error": result.get("error", "알 수 없는 오류")
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Fetch MCP API 요청 오류 {url}: {str(e)}")
            return {
                "url": url,
                "success": False,
                "title": "",
                "content": "",
                "text_length": 0,
                "error": f"요청 오류: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Fetch MCP API 처리 오류 {url}: {str(e)}")
            return {
                "url": url,
                "success": False,
                "title": "",
                "content": "",
                "text_length": 0,
                "error": f"처리 오류: {str(e)}"
            }
    
    def _filter_urls(self, urls: List[str]) -> List[str]:
        """
        URL을 필터링합니다 (중복 제거, 유효성 검사).
        
        Args:
            urls: 원본 URL 리스트
            
        Returns:
            List[str]: 필터링된 URL 리스트
        """
        valid_urls = []
        seen_urls = set()
        
        for url in urls:
            if not url or not url.strip():
                continue
            
            # URL 정규화
            normalized_url = self._normalize_url(url.strip())
            
            if not normalized_url:
                continue
            
            # 중복 제거
            if normalized_url in seen_urls:
                continue
            
            # 유효성 검사
            if self._is_valid_url(normalized_url):
                valid_urls.append(normalized_url)
                seen_urls.add(normalized_url)
        
        return valid_urls
    
    def _prioritize_artwork_urls(self, urls: List[str], max_urls: int) -> List[str]:
        """
        작품 정보 검색에 적합한 URL을 우선순위에 따라 정렬합니다.
        
        Args:
            urls: URL 리스트
            max_urls: 최대 URL 수
            
        Returns:
            List[str]: 우선순위가 적용된 URL 리스트
        """
        if not urls:
            return []
        
        # 우선순위 점수 계산
        url_scores = []
        
        for url in urls:
            score = 0
            domain = urlparse(url).netloc.lower()
            
            # 박물관 공식 사이트 (최고 우선순위)
            if any(keyword in domain for keyword in ['museum', 'gallery', 'art', '문화재', '박물관', '미술관']):
                score += 100
            
            # 한국 도메인 (.kr)
            if domain.endswith('.kr'):
                score += 50
            
            # HTTPS 보안 연결
            if url.startswith('https://'):
                score += 20
            
            # 뉴스/블로그 사이트 (중간 우선순위)
            if any(keyword in domain for keyword in ['news', 'blog', 'naver', 'tistory', 'daum']):
                score += 30
            
            # 일반 사이트 (낮은 우선순위)
            score += 10
            
            url_scores.append((url, score))
        
        # 점수순 정렬 (높은 점수 우선)
        url_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 URL만 반환
        return [url for url, score in url_scores[:max_urls]]
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """
        URL을 정규화합니다.
        
        Args:
            url: 원본 URL
            
        Returns:
            Optional[str]: 정규화된 URL 또는 None
        """
        if not url:
            return None
        
        # 프로토콜 추가
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # 기본 유효성 검사
        try:
            parsed = urlparse(url)
            if parsed.netloc and parsed.scheme:
                return url
        except:
            pass
        
        return None
    
    def _is_valid_url(self, url: str) -> bool:
        """
        URL 유효성을 검사합니다.
        
        Args:
            url: 검사할 URL
            
        Returns:
            bool: 유효성 여부
        """
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.scheme)
        except:
            return False
    
    def extract_content_snippets(self, fetch_results: List[Dict], max_snippets: int = 10) -> List[str]:
        """
        Fetch 결과에서 유용한 텍스트 스니펫을 추출합니다.
        
        Args:
            fetch_results: fetch_urls() 또는 fetch_artwork_urls() 결과
            max_snippets: 최대 스니펫 수
            
        Returns:
            List[str]: 텍스트 스니펫 리스트
        """
        snippets = []
        
        for result in fetch_results:
            if not result.get("success") or not result.get("content"):
                continue
            
            content = result["content"]
            title = result.get("title", "")
            
            # 제목 추가
            if title:
                snippets.append(f"제목: {title}")
            
            # 내용에서 핵심 부분 추출 (처음 500자)
            if len(content) > 500:
                content = content[:500] + "..."
            
            snippets.append(f"내용: {content}")
            snippets.append(f"출처: {result['url']}")
            snippets.append("---")  # 구분자
        
        return snippets[:max_snippets]
