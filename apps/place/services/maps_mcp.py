# place/services/maps_mcp.py

import os
import base64
import json
import logging
import math
from typing import Dict, List, Any
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


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    하버사인 공식을 사용하여 두 좌표 간의 거리를 미터 단위로 계산합니다.
    
    Args:
        lat1, lon1: 첫 번째 지점의 위도, 경도
        lat2, lon2: 두 번째 지점의 위도, 경도
        
    Returns:
        float: 두 지점 사이의 거리 (미터)
    """
    # 지구 반지름 (미터)
    R = 6371000
    
    # 위도/경도를 라디안으로 변환
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    
    # 하버사인 공식
    a = (math.sin(Δφ / 2) * math.sin(Δφ / 2) +
         math.cos(φ1) * math.cos(φ2) *
         math.sin(Δλ / 2) * math.sin(Δλ / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 거리 계산 (미터)
    distance = R * c
    
    # 소수점 둘째 자리까지 반올림
    return round(distance, 2)


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
            "apiKey": required_vars["GOOGLE_MAPS_API_KEY"],
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


async def test_mcp_connection() -> Dict[str, Any]:
    """MCP 서버 연결을 테스트합니다."""
    try:
        url = get_mcp_url()
        logger.info(f"🔍 MCP URL: {url}")
        
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # POST 요청으로 테스트
            response = await client.post(url, json={
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp",
                        "version": "0.1.0"
                    }
                }
            })
            
            logger.info(f"🔍 응답 상태 코드: {response.status_code}")
            logger.info(f"🔍 응답 헤더: {dict(response.headers)}")
            logger.info(f"🔍 응답 내용: {response.text}")
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text
            }
            
    except Exception as e:
        logger.error(f"🔍 MCP 연결 테스트 실패: {str(e)}", exc_info=True)
        return {"error": str(e)}


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
    
    # 먼저 MCP 연결 테스트
    logger.info("🔍 MCP 연결 테스트 시작...")
    test_result = await test_mcp_connection()
    logger.info(f"🔍 MCP 연결 테스트 결과: {test_result}")
    
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
                    # 구조 1: 실제 사용자 좌표 사용
                    {
                        "query": keyword.strip(),
                        "location": f"{latitude},{longitude}",
                        "radius": radius
                    },
                    # 구조 2: 객체 형태의 location
                    {
                        "query": keyword.strip(),
                        "location": {
                            "latitude": latitude,
                            "longitude": longitude
                        },
                        "radius": radius
                    },
                    # 구조 3: 간단한 구조
                    {
                        "query": keyword.strip(),
                        "latitude": latitude,
                        "longitude": longitude,
                        "radius": radius
                    },
                    # 구조 4: Google Places API 스타일
                    {
                        "location": f"{latitude},{longitude}",
                        "radius": radius,
                        "keyword": keyword.strip(),
                        "type": "museum"
                    },
                    # 구조 5: 텍스트 검색 스타일
                    {
                        "textQuery": f"{keyword.strip()} near {latitude},{longitude}"
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
                        # 422 오류인 경우 응답 내용도 로깅
                        if hasattr(e, 'response') and e.response:
                            try:
                                error_content = e.response.text
                                logger.error(f"🔍 422 오류 응답 내용: {error_content}")
                            except:
                                pass
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
        
        # httpx.HTTPStatusError인 경우 더 자세한 정보 로깅
        if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            logger.error(f"🔍 HTTP 상태 코드: {e.response.status_code}")
            logger.error(f"🔍 응답 헤더: {dict(e.response.headers)}")
            try:
                logger.error(f"🔍 응답 내용: {e.response.text}")
            except:
                pass
        
        # ExceptionGroup인 경우 내부 예외들도 확인
        if hasattr(e, '__cause__') and e.__cause__:
            logger.error(f"🔍 원인 예외: {e.__cause__}")
            if hasattr(e.__cause__, 'response') and hasattr(e.__cause__.response, 'status_code'):
                logger.error(f"🔍 원인 HTTP 상태 코드: {e.__cause__.response.status_code}")
                try:
                    logger.error(f"🔍 원인 응답 내용: {e.__cause__.response.text}")
                except:
                    pass
        
        raise MapsAPIError(f"Google Maps MCP 호출 중 오류 발생: {str(e)}") from e


def process_mcp_response(result: Any, user_lat: float, user_lon: float, radius: int, max_results: int = 4) -> List[Dict[str, Any]]:
    """
    MCP 응답을 처리하여 박물관 목록을 반환합니다.
    
    Args:
        result: MCP 응답 결과
        user_lat: 사용자 위도
        user_lon: 사용자 경도
        radius: 검색 반경 (미터)
        max_results: 최대 반환할 결과 수
        
    Returns:
        List[Dict]: 처리된 박물관 목록 (거리 정보 포함, 반경 내만)
        
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
        
        # 데이터 정리 및 거리 계산
        processed_places = []
        logger.info(f"총 {len(places)}개 박물관 처리 시작...")
        
        for i, place in enumerate(places):  # 모든 박물관 처리
            logger.info(f"처리 중: {i+1}/{len(places)} - {place.get('name', 'Unknown')}")
            
            # 이름은 필수, 나머지는 선택적
            if not place.get("name"):
                logger.warning(f"이름이 없는 place 건너뜀: {place}")
                continue
                
            # 주소 추출 (formatted_address 또는 address)
            address = place.get("formatted_address") or place.get("address") or ""
            
            # 좌표 추출 (location 객체 또는 직접 필드)
            place_lat = 0.0
            place_lon = 0.0
            
            # 좌표 추출 시도 1: location 객체
            if "location" in place and isinstance(place["location"], dict):
                place_lat = place["location"].get("lat", 0.0)
                place_lon = place["location"].get("lng", 0.0)
                logger.info(f"  📍 좌표 추출 (location 객체): lat={place_lat}, lng={place_lon}")
            # 좌표 추출 시도 2: 직접 필드
            elif place.get("latitude") and place.get("longitude"):
                place_lat = place.get("latitude", 0.0)
                place_lon = place.get("longitude", 0.0)
                logger.info(f"  📍 좌표 추출 (직접 필드): lat={place_lat}, lng={place_lon}")
            else:
                logger.warning(f"  ⚠️ 좌표를 찾을 수 없음: {place}")
                continue
            
            # 거리 계산
            distance = calculate_distance(user_lat, user_lon, place_lat, place_lon)
            logger.info(f"거리 계산: {place.get('name')} - 사용자({user_lat}, {user_lon}) -> 장소({place_lat}, {place_lon}) = {distance:.2f}m")
            
            # 처리된 장소 정보 구성
            processed_place = {
                "name": place.get("name", ""),
                "address": address,
                "place_id": place.get("place_id", ""),
                "latitude": place_lat,
                "longitude": place_lon,
                "rating": place.get("rating", None),
                "types": place.get("types", []),
                "web_url": place.get("web_url", None),
                "distance_m": distance
            }
            
            # ✅ 검색 반경 내에 있는 경우만 추가
            if distance <= radius:
                processed_places.append(processed_place)
            else:
                logger.debug(f"반경 밖 장소 제외: {place.get('name')} ({distance:.2f}m > {radius}m)")
        
        # 🎯 거리 순으로 정렬 (가까운 순)
        processed_places.sort(key=lambda x: x["distance_m"])
        
        # 🏆 정렬된 순서에 따라 rank 부여하고 max_results만 반환
        for idx, place in enumerate(processed_places):
            place["rank"] = idx + 1
        
        # 최대 결과 수만큼만 반환
        final_places = processed_places[:max_results]
        
        logger.info(f"처리된 박물관 수: {len(processed_places)} -> 최종 반환: {len(final_places)}개 (반경 {radius}m 내, 거리순 정렬 완료)")
        return final_places
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}")
        raise MapsAPIError(f"응답 데이터 파싱 중 오류가 발생했습니다: {str(e)}") from e
    except (KeyError, IndexError, AttributeError) as e:
        logger.error(f"MCP 응답 처리 중 구조 오류: {str(e)}")
        raise MapsAPIError(f"응답 구조 처리 중 오류가 발생했습니다: {str(e)}") from e
    except Exception as e:
        logger.error(f"MCP 응답 처리 중 예상치 못한 오류: {str(e)}", exc_info=True)
        raise MapsAPIError(f"응답 처리 중 예상치 못한 오류가 발생했습니다: {str(e)}") from e
