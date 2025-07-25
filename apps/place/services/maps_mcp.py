# place/services/maps_mcp.py

import os
import base64
import json
import logging
from typing import Dict, List, Any, Optional
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class MapsServiceError(Exception):
    """Maps 서비스 관련 커스텀 예외"""
    pass


class MapsConfigError(MapsServiceError):
    """Maps 설정 관련 예외"""
    pass


class MapsAPIError(MapsServiceError):
    """Maps API 호출 관련 예외"""
    pass


def get_mcp_url() -> str:
    """MCP URL을 생성합니다."""
    # 필수 환경 변수 검증
    required_vars = {
        'GOOGLE_MAPS_API_KEY': os.getenv("GOOGLE_MAPS_API_KEY"),
        'SMITHERY_API_KEY': os.getenv('SMITHERY_API_KEY'),
        'SMITHERY_PROFILE': os.getenv('SMITHERY_PROFILE')
    }
    
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise MapsConfigError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
    
    try:
        config = {
            "googleMapsApiKey": required_vars["GOOGLE_MAPS_API_KEY"],
        }
        config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
        url = (
            f"https://server.smithery.ai/@smithery-ai/google-maps/mcp"
            f"?config={config_b64}&api_key={required_vars['SMITHERY_API_KEY']}&profile={required_vars['SMITHERY_PROFILE']}"
        )
        logger.info("MCP URL 생성 완료")
        return url
    except Exception as e:
        raise MapsConfigError(f"MCP URL 생성 중 오류 발생: {str(e)}") from e


async def debug_mcp_tools() -> Dict[str, Any]:
    """MCP 서버의 사용 가능한 툴을 디버깅합니다."""
    try:
        url = get_mcp_url()
        logger.info("MCP 툴 디버깅 시작")
        
        async with streamablehttp_client(url, timeout=30) as (read_stream, write_stream, _), \
                   ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # 사용 가능한 툴 목록 조회
            tools_result = await session.list_tools()
            available_tools = {}
            
            for tool in tools_result.tools:
                available_tools[tool.name] = {
                    "name": tool.name,
                    "description": getattr(tool, 'description', ''),
                    "input_schema": getattr(tool, 'inputSchema', {})
                }
                
            logger.info(f"사용 가능한 툴 목록: {list(available_tools.keys())}")
            return available_tools
            
    except Exception as e:
        logger.error(f"MCP 툴 디버깅 중 오류: {str(e)}", exc_info=True)
        raise MapsAPIError(f"MCP 툴 디버깅 실패: {str(e)}") from e


def validate_search_params(latitude: float, longitude: float, radius: int, keyword: str) -> None:
    """검색 매개변수의 유효성을 검증합니다."""
    if not (-90 <= latitude <= 90):
        raise ValueError("위도는 -90에서 90 사이의 값이어야 합니다")
    if not (-180 <= longitude <= 180):
        raise ValueError("경도는 -180에서 180 사이의 값이어야 합니다")
    if not (0 < radius <= 50000):  # Google Places API 제한
        raise ValueError("반경은 0보다 크고 50000미터 이하여야 합니다")
    if not keyword or not keyword.strip():
       raise ValueError("검색 키워드는 필수입니다")


async def search_nearby_museums(
    latitude: float, 
    longitude: float, 
    radius: int, 
    keyword: str
) -> Dict[str, Any]:
    """
    근처 박물관을 검색합니다.
    
    Args:
        latitude: 위도
        longitude: 경도
        radius: 검색 반경 (미터)
        keyword: 검색 키워드
        
    Returns:
        Dict: MCP 응답 결과
        
    Raises:
        ValueError: 입력 매개변수가 유효하지 않을 때
        MapsAPIError: API 호출 중 오류가 발생했을 때
        MapsConfigError: 설정 오류가 발생했을 때
    """
    # 매개변수 검증
    validate_search_params(latitude, longitude, radius, keyword)
    
    # 임시: Mock 데이터로 테스트 (MCP 연결 문제 해결 전까지)
    logger.warning("🚧 임시 Mock 데이터 사용 중 - MCP 연결 문제로 인해")
    
    mock_result = type('MockResult', (), {
        'to_dict': lambda self: {
            'content': [type('MockContent', (), {
                'text': json.dumps({
                    'places': [
                        {
                            "name": "국립중앙박물관",
                            "address": "서울 용산구 서빙고로 137",
                            "place_id": "ChIJzVVVVUB7Lj4ARXyb4HFVDV8s",
                            "latitude": 37.5242,
                            "longitude": 126.9806,
                            "web_url": "https://www.museum.go.kr"
                        },
                        {
                            "name": "국립민속박물관",
                            "address": "서울 종로구 삼청로 37",
                            "place_id": "ChIJXXXXXXB7Lj4ARXyb4HFVDV8s",
                            "latitude": 37.5799,
                            "longitude": 126.9770,
                            "web_url": "https://www.nfm.go.kr"
                        },
                        {
                            "name": "서울역사박물관",
                            "address": "서울 종로구 새문안로 55",
                            "place_id": "ChIJYYYYYYB7Lj4ARXyb4HFVDV8s",
                            "latitude": 37.5717,
                            "longitude": 126.9794,
                            "web_url": "https://www.museum.seoul.kr"
                        },
                        {
                            "name": "한국은행 화폐박물관",
                            "address": "서울 중구 남대문로 39",
                            "place_id": "ChIJZZZZZZB7Lj4ARXyb4HFVDV8s",
                            "latitude": 37.5598,
                            "longitude": 126.9783,
                            "web_url": "https://museum.bok.or.kr"
                        }
                    ]
                })
            })]
        }
    })()
    
    logger.info("✅ Mock 데이터 반환 완료")
    return mock_result
    
    # 실제 MCP 호출 코드 (현재 주석 처리)
    """
    try:
        url = get_mcp_url()
        
        logger.info(f"MCP 검색 시작: lat={latitude}, lng={longitude}, radius={radius}, keyword={keyword}")
        
        async with streamablehttp_client(url, timeout=30) as (read_stream, write_stream, _), \
                   ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # 먼저 사용 가능한 툴 목록 조회
            try:
                tools_result = await session.list_tools()
                available_tools = [tool.name for tool in tools_result.tools]
                logger.info(f"🔍 사용 가능한 툴 목록: {available_tools}")
                
                # 각 툴의 상세 정보도 로깅
                for tool in tools_result.tools:
                    logger.info(f"  📋 툴: {tool.name}")
                    if hasattr(tool, 'description'):
                        logger.info(f"     설명: {tool.description}")
                    if hasattr(tool, 'inputSchema'):
                        logger.info(f"     입력 스키마: {tool.inputSchema}")
                
                # 실제 툴을 찾아서 호출
                target_tool = None
                possible_tool_names = [
                    "search_places",
                    "places_search", 
                    "nearby_search",
                    "search_nearby",
                    "maps_search_places",
                    "google_places_search",
                    "place_search",
                    "search"
                ]
                
                for tool_name in possible_tool_names:
                    if tool_name in available_tools:
                        target_tool = tool_name
                        logger.info(f"✅ 사용할 툴 발견: {tool_name}")
                        break
                
                if not target_tool:
                    # 첫 번째 툴을 시도
                    if available_tools:
                        target_tool = available_tools[0]
                        logger.info(f"🔄 첫 번째 툴로 시도: {target_tool}")
                    else:
                        raise MapsAPIError("사용 가능한 툴이 없습니다")
                
                # 여러 페이로드 구조 시도
                possible_payloads = [
                    # 구조 1: 서울 근처 좌표로 테스트 (더 현실적인 좌표)
                    {
                        "query": keyword.strip(),
                        "location": f"{37.5665},{126.9780}",  # 서울시청 좌표
                        "radius": radius
                    },
                    # 구조 2: 기존 구조
                    {
                        "query": keyword.strip(),
                        "location": {
                            "latitude": 37.5665,
                            "longitude": 126.9780
                        },
                        "radius": radius
                    },
                    # 구조 3: 간단한 구조
                    {
                        "query": keyword.strip(),
                        "latitude": 37.5665,
                        "longitude": 126.9780,
                        "radius": radius
                    },
                    # 구조 4: Google Places API 스타일
                    {
                        "location": f"{37.5665},{126.9780}",
                        "radius": radius,
                        "keyword": keyword.strip(),
                        "type": "museum"
                    },
                    # 구조 5: 텍스트 검색 스타일
                    {
                        "textQuery": f"{keyword.strip()} near Seoul, South Korea"
                    }
                ]
                
                last_error = None
                
                # 각 페이로드 구조 시도
                for i, payload in enumerate(possible_payloads):
                    try:
                        logger.info(f"🧪 페이로드 구조 {i+1} 시도 ({target_tool}): {payload}")
                        result = await session.call_tool(target_tool, payload)
                        logger.info("✅ MCP 검색 완료!")
                        return result
                    except Exception as e:
                        logger.warning(f"❌ 페이로드 구조 {i+1} 실패: {str(e)}")
                        last_error = e
                        continue
                
                if last_error:
                    raise last_error
                else:
                    raise MapsAPIError("모든 페이로드 구조 시도가 실패했습니다")
                    
            except Exception as e:
                logger.error(f"MCP 세션 처리 중 오류: {str(e)}", exc_info=True)
                raise MapsAPIError(f"MCP 세션 오류: {str(e)}") from e
            
    except MapsConfigError:
        # 설정 오류는 그대로 전파
        raise
    except Exception as e:
        logger.error(f"Google Maps MCP 호출 중 오류 발생: {str(e)}", exc_info=True)
        raise MapsAPIError(f"Google Maps MCP 호출 중 오류 발생: {str(e)}") from e
    """


def process_mcp_response(result: Any, max_results: int = 4) -> List[Dict[str, Any]]:
    """
    MCP 응답을 처리하여 박물관 목록을 반환합니다.
    
    Args:
        result: MCP 응답 결과
        max_results: 최대 반환할 결과 수
        
    Returns:
        List[Dict]: 처리된 박물관 목록
        
    Raises:
        MapsAPIError: 응답 처리 중 오류가 발생했을 때
    """
    try:
        # 결과를 딕셔너리로 변환
        if hasattr(result, "to_dict"):
            result_dict = result.to_dict()
        elif hasattr(result, "data"):
            result_dict = result.data
        else:
            result_dict = dict(result)
            
        logger.debug(f"MCP 응답 구조: {type(result_dict)}")
        
        # content 추출 및 검증
        content_list = result_dict.get("content", [])
        if not content_list:
            logger.warning("MCP 응답에 content가 없습니다")
            return []
            
        if not hasattr(content_list[0], "text"):
            logger.warning("MCP 응답의 첫 번째 content에 text가 없습니다")
            return []
        
        # JSON 파싱
        places_json = json.loads(content_list[0].text)
        places = places_json.get("places", [])
        
        if not places:
            logger.info("검색 결과가 없습니다")
            return []
        
        # 데이터 정리 및 순위 부여
        processed_places = []
        for idx, place in enumerate(places[:max_results]):
            # 필수 필드 검증
            required_fields = ["name", "address", "place_id"]
            if not all(field in place for field in required_fields):
                logger.warning(f"필수 필드가 누락된 place 건너뜀: {place}")
                continue
                
            # 불필요한 필드 제거
            processed_place = {
                "name": place.get("name", ""),
                "address": place.get("address", ""),
                "place_id": place.get("place_id", ""),
                "latitude": place.get("latitude", 0.0),
                "longitude": place.get("longitude", 0.0),
                "rank": idx + 1,
                "web_url": place.get("web_url", None)
            }
            
            processed_places.append(processed_place)
        
        logger.info(f"처리된 박물관 수: {len(processed_places)}")
        return processed_places
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}")
        raise MapsAPIError(f"응답 데이터 파싱 중 오류가 발생했습니다: {str(e)}") from e
    except (KeyError, IndexError, AttributeError) as e:
        logger.error(f"MCP 응답 처리 중 구조 오류: {str(e)}")
        raise MapsAPIError(f"응답 구조 처리 중 오류가 발생했습니다: {str(e)}") from e
    except Exception as e:
        logger.error(f"MCP 응답 처리 중 예상치 못한 오류: {str(e)}", exc_info=True)
        raise MapsAPIError(f"응답 처리 중 예상치 못한 오류가 발생했습니다: {str(e)}") from e
