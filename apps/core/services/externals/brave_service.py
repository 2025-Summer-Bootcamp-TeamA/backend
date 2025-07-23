import os
import json
import base64
import logging
import traceback
import asyncio
from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import re

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY")
BRAVE_PROFILE = os.getenv("BRAVE_MCP_PROFILE", "other-beetle-JoaZ1u")


class MCPConnectionError(Exception):
    """MCP 연결 관련 오류"""
    pass


class MCPToolError(Exception):
    """MCP 도구 실행 관련 오류"""
    pass


class BraveSearchError(Exception):
    """Brave Search 관련 오류"""
    pass


# MCP 연결 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # 초


def get_brave_mcp_url():
    config = {"braveApiKey": BRAVE_API_KEY}
    config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
    return (
        f"https://server.smithery.ai/@smithery-ai/brave-search/mcp"
        f"?config={config_b64}&api_key={SMITHERY_API_KEY}&profile={BRAVE_PROFILE}"
    )


async def brave_search(query, count=3) -> dict:
    """
    Brave Search MCP를 사용한 검색 (재시도 로직 포함)
    
    Args:
        query: 검색 쿼리
        count: 결과 개수
        
    Returns:
        Dict: 검색 결과 (URL 리스트 포함)
    """
    url = get_brave_mcp_url()
    logger.info(f"🔍 Brave Search 요청: query='{query}', count={count}")

    for attempt in range(MAX_RETRIES):
        try:
            return await _brave_search_single_attempt(url, query, count)
        except MCPConnectionError as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Brave MCP 연결 최종 실패: {e}")
                return {"success": False, "error": f"연결 오류: {e}", "results": []}
            else:
                logger.warning(f"Brave MCP 연결 재시도 {attempt + 1}/{MAX_RETRIES}: {e}")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        except MCPToolError as e:
            logger.error(f"Brave MCP 도구 실행 오류: {e}")
            return {"success": False, "error": f"도구 실행 오류: {e}", "results": []}
        except Exception as e:
            logger.error(f"Brave MCP 예상치 못한 오류: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": f"예상치 못한 오류: {e}", "results": []}
    
    return {"success": False, "error": "최대 재시도 횟수 초과", "results": []}


async def _brave_search_single_attempt(url: str, query: str, count: int) -> dict:
    """단일 Brave Search MCP 요청 시도"""
    try:
        async with streamablehttp_client(url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                logger.debug(f"Brave MCP 세션 초기화 완료")
                
                result = await session.call_tool(
                    "brave_web_search", {"query": query, "count": count}
                )

                logger.info("📦 Brave MCP 응답 수신 완료")
                content = getattr(result, "content", None)
                logger.debug(f"[DEBUG] MCP result: {result}")
                logger.debug(f"[DEBUG] MCP content: {content}")

                return _process_brave_result(content, result)
                
    except ConnectionError as e:
        raise MCPConnectionError(f"Brave MCP 서버 연결 실패: {e}")
    except TimeoutError as e:
        raise MCPConnectionError(f"Brave MCP 연결 타임아웃: {e}")
    except Exception as e:
        if "502 Bad Gateway" in str(e) or "BrokenResourceError" in str(e):
            raise MCPConnectionError(f"Brave MCP 서버 일시적 오류: {e}")
        elif "tool" in str(e).lower() or "brave_web_search" in str(e):
            raise MCPToolError(f"brave_web_search 도구 실행 실패: {e}")
        else:
            raise


def _process_brave_result(content, result) -> dict:
    """Brave Search 결과 처리"""
    # ✅ TextContent 리스트 처리
    if isinstance(content, list):
        urls = []
        for item in content:
            meta = getattr(item, "meta", None)
            if isinstance(meta, dict) and "url" in meta:
                urls.append(meta["url"])
            elif hasattr(item, "text"):
                # text에서 URL 추출
                text = getattr(item, "text", "")
                found_urls = re.findall(r'https?://[^\s\"\'<>]+', text)
                urls.extend(found_urls)
                logger.warning(f"⚠️ meta 없음, text에서 URL 추출: {found_urls}")
            else:
                logger.warning(f"⚠️ URL 없음 또는 meta/text 포맷 이상: {item}")
        logger.info(f"✅ content는 list. URL 개수: {len(urls)}")
        return {"success": True, "results": urls}

    # ✅ TextContent 단일 객체 처리 (text에서 URL 추출)
    if hasattr(content, "text"):
        found_urls = re.findall(r'https?://[^\s\\)\\]\"\']+', getattr(content, "text", ""))
        if found_urls:
            logger.info(f"✅ 단일 text에서 URL 추출: {found_urls}")
            return {"success": True, "results": found_urls}
        else:
            logger.warning("⚠️ 단일 text에서 URL 추출 실패")
            return {"success": True, "results": []}

    # ✅ fallback: result.result도 확인
    if hasattr(result, "result"):
        logger.info("✅ result 속성에서 결과 반환")
        result_content = result.result
        logger.debug(f"[DEBUG] result.result: {result_content}")
        if isinstance(result_content, list):
            urls = [r.get("url") for r in result_content if "url" in r]
            return {"success": True, "results": urls}
        elif isinstance(result_content, dict):
            urls = [r.get("url") for r in result_content.get("results", []) if "url" in r]
            return {"success": True, "results": urls}

    logger.warning("⚠️ 결과를 파악할 수 없습니다.")
    return {"success": True, "results": []}
