# place/services/maps_mcp.py

import os
import base64
import json
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def get_mcp_url():
    # 필수 환경 변수 검증
    required_vars = {
        'GOOGLE_MAPS_API_KEY': os.getenv("GOOGLE_MAPS_API_KEY"),
        'SMITHERY_API_KEY': os.getenv('SMITHERY_API_KEY'),
        'SMITHERY_PROFILE': os.getenv('SMITHERY_PROFILE')
    }
    
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
    
    config = {
        "googleMapsApiKey": required_vars["GOOGLE_MAPS_API_KEY"],
    }
    config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
    return (
        f"https://server.smithery.ai/@smithery-ai/google-maps/mcp"
        f"?config={config_b64}&api_key={required_vars['SMITHERY_API_KEY']}&profile={required_vars['SMITHERY_PROFILE']}"
    )


async def search_nearby_museums(latitude, longitude, radius, keyword):
     # 매개변수 검증
    if not (-90 <= latitude <= 90):
        raise ValueError("위도는 -90에서 90 사이의 값이어야 합니다")
    if not (-180 <= longitude <= 180):
        raise ValueError("경도는 -180에서 180 사이의 값이어야 합니다")
    if not (0 < radius <= 50000):  # Google Places API 제한
        raise ValueError("반경은 0보다 크고 50000미터 이하여야 합니다")
    if not keyword or not keyword.strip():
       raise ValueError("검색 키워드는 필수입니다")
    
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
        async with streamablehttp_client(url, timeout=30) as (read_stream, write_stream, _), \
                   ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("maps_search_places", payload)
            return result
    except Exception as e:
        raise RuntimeError(f"Google Maps MCP 호출 중 오류 발생: {str(e)}") from e
