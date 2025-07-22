import os
import json
import base64
import logging
import traceback
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


def get_brave_mcp_url():
    config = {"braveApiKey": BRAVE_API_KEY}
    config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
    return (
        f"https://server.smithery.ai/@smithery-ai/brave-search/mcp"
        f"?config={config_b64}&api_key={SMITHERY_API_KEY}&profile={BRAVE_PROFILE}"
    )


async def brave_search(query, count=3) -> dict:
    url = get_brave_mcp_url()
    logger.info(f"🔍 Brave Search 요청: query='{query}', count={count}")

    try:
        async with streamablehttp_client(url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "brave_web_search", {"query": query, "count": count}
                )

                logger.info("📦 MCP 응답 수신 완료")
                content = getattr(result, "content", None)
                logger.debug(f"[DEBUG] MCP result: {result}")
                logger.debug(f"[DEBUG] MCP content: {content}")

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
                    return {"results": urls}

                # ✅ TextContent 단일 객체 처리 (text에서 URL 추출)
                if hasattr(content, "text"):
                    found_urls = re.findall(r'https?://[^\s\\)\\]\"\']+', getattr(content, "text", ""))
                    if found_urls:
                        logger.info(f"✅ 단일 text에서 URL 추출: {found_urls}")
                        return {"results": found_urls}
                    else:
                        logger.warning("⚠️ 단일 text에서 URL 추출 실패")
                        return {"results": []}


                # ✅ fallback: result.result도 확인
                if hasattr(result, "result"):
                    logger.info("✅ result 속성에서 결과 반환")
                    result_content = result.result
                    logger.debug(f"[DEBUG] result.result: {result_content}")
                    if isinstance(result_content, list):
                        urls = [r.get("url") for r in result_content if "url" in r]
                        return {"results": urls}
                    elif isinstance(result_content, dict):
                        urls = [r.get("url") for r in result_content.get("results", []) if "url" in r]
                        return {"results": urls}

                logger.warning("⚠️ 결과를 파악할 수 없습니다.")
                return {"results": []}

    except Exception as e:
        logger.error(f"🌐 Brave MCP 요청 중 예외 발생: {str(e)}")
        logger.error(traceback.format_exc())
        # raw response/result가 있다면 최대한 출력
        try:
            logger.error(f"[DEBUG] result: {locals().get('result', None)}")
            logger.error(f"[DEBUG] content: {locals().get('content', None)}")
        except Exception as log_e:
            logger.error(f"[DEBUG] 로깅 중 추가 예외: {log_e}")
        return {"success": False, "error": str(e)}
