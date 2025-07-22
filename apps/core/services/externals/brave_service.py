import os
import json
import base64
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dotenv import load_dotenv

load_dotenv()

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY")
BRAVE_PROFILE = os.getenv("BRAVE_MCP_PROFILE", "other-beetle-JoaZ1u")


def get_brave_mcp_url():
    config = {
        "braveApiKey": BRAVE_API_KEY
    }
    config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
    return (
        f"https://server.smithery.ai/@smithery-ai/brave-search/mcp"
        f"?config={config_b64}&api_key={SMITHERY_API_KEY}&profile={BRAVE_PROFILE}"
    )


async def brave_search(query, count=3) -> dict:
    url = get_brave_mcp_url()

    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "brave_web_search",
                {
                    "query": query,
                    "count": count
                }
            )

            if hasattr(result, "content"):
                try:
                    return json.loads(result.content)
                except Exception as e:
                    return {"success": False, "error": f"JSON 파싱 실패: {str(e)}"}

            elif hasattr(result, "result"):
                return result.result

            else:
                return {"success": False, "results": []}
