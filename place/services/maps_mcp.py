# place/services/maps_mcp.py

import os
import base64
import json
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def get_mcp_url():
    config = {
        "googleMapsApiKey": os.getenv("GOOGLE_MAPS_API_KEY"),
    }
    config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
    return (
        f"https://server.smithery.ai/@smithery-ai/google-maps/mcp"
        f"?config={config_b64}&api_key={os.getenv('SMITHERY_API_KEY')}&profile={os.getenv('SMITHERY_PROFILE')}"
    )


async def search_nearby_museums(latitude, longitude, radius, keyword):
    url = get_mcp_url()
    payload = {
        "query": keyword,
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "radius": radius
    }

    try:
        async with streamablehttp_client(url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool("maps_search_places", payload)
                return result
    except Exception as e:
        raise RuntimeError(f"Google Maps MCP 호출 중 오류 발생: {str(e)}")
