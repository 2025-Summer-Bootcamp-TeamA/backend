import requests
import logging
import json
import base64
from django.conf import settings
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class BraveSearchService:
    """
    Brave Search MCP를 사용하여 웹 검색을 수행하는 서비스
    """
    
    def __init__(self):
        self.smithery_api_key = settings.SMITHERY_API_KEY
        self.brave_api_key = settings.BRAVE_API_KEY
        self.profile = settings.BRAVE_MCP_PROFILE
        
        if not self.smithery_api_key or not self.brave_api_key:
            raise ValueError("Smithery MCP 설정이 누락되었습니다. SMITHERY_API_KEY와 BRAVE_API_KEY를 확인해주세요.")
    
    def _get_mcp_url(self):
        """MCP 서버 URL을 생성합니다."""
        config = {
            "braveApiKey": self.brave_api_key
        }
        config_b64 = base64.b64encode(json.dumps(config).encode()).decode()
        return f"https://server.smithery.ai/@smithery-ai/brave-search/mcp?config={config_b64}&api_key={self.smithery_api_key}&profile={self.profile}"
    
    def search_artwork(self, artwork_title: str, museum_name: str, limit: int = 5) -> Dict:
        """
        작품명과 박물관 이름으로 웹 검색을 수행합니다.
        
        Args:
            artwork_title: 작품명
            museum_name: 박물관/미술관 이름
            limit: 검색 결과 수 제한 (기본 5개)
            
        Returns:
            Dict: 검색 결과 딕셔너리
            {
                "success": bool,
                "query": str,
                "results": List[Dict],
                "total_count": int
            }
        """
        try:
            # 검색 쿼리 구성: "작품명 박물관명"
            search_query = f'"{artwork_title}" "{museum_name}"'
            
            logger.info(f"Brave Search 시작: {search_query}")
            
            # MCP API 호출
            response = self._call_mcp_api(search_query, limit)
            
            if response:
                return {
                    "success": True,
                    "query": search_query,
                    "results": response.get("results", []),
                    "total_count": len(response.get("results", []))
                }
            else:
                return self._empty_result(search_query)
                
        except Exception as e:
            logger.error(f"Brave Search 오류: {str(e)}")
            return {
                "success": False,
                "query": f'"{artwork_title}" "{museum_name}"',
                "results": [],
                "total_count": 0,
                "error": str(e)
            }
    
    def search_general(self, query: str, limit: int = 5) -> Dict:
        """
        일반적인 웹 검색을 수행합니다.
        
        Args:
            query: 검색어
            limit: 검색 결과 수 제한
            
        Returns:
            Dict: 검색 결과 딕셔너리
        """
        try:
            logger.info(f"Brave Search 일반 검색: {query}")
            
            response = self._call_mcp_api(query, limit)
            
            if response:
                return {
                    "success": True,
                    "query": query,
                    "results": response.get("results", []),
                    "total_count": len(response.get("results", []))
                }
            else:
                return self._empty_result(query)
                
        except Exception as e:
            logger.error(f"Brave Search 일반 검색 오류: {str(e)}")
            return {
                "success": False,
                "query": query,
                "results": [],
                "total_count": 0,
                "error": str(e)
            }
    
    def _call_mcp_api(self, query: str, limit: int) -> Optional[Dict]:
        """
        Brave MCP API를 호출합니다.
        
        Args:
            query: 검색어
            limit: 결과 수 제한
            
        Returns:
            Optional[Dict]: API 응답 또는 None
        """
        try:
            # MCP API 엔드포인트 구성
            url = f"{self._get_mcp_url()}"
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "*/*"
            }
            
            payload = {
                "query": query,
                "count": limit,
                "profile": self.profile,
                "freshness": "py",
                "search_lang": "ko",
                "country": "KR"
            }
            
            logger.debug(f"Brave MCP API 호출: {url}")
            logger.debug(f"페이로드: {payload}")
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Brave Search 성공: {len(result.get('results', []))}개 결과")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Brave MCP API 요청 오류: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Brave MCP API 처리 오류: {str(e)}")
            return None
    
    def _empty_result(self, query: str) -> Dict:
        """빈 검색 결과를 반환합니다."""
        return {
            "success": True,
            "query": query,
            "results": [],
            "total_count": 0
        }
    
    def extract_search_snippets(self, search_results: Dict) -> List[str]:
        """
        검색 결과에서 유용한 텍스트 스니펫을 추출합니다.
        
        Args:
            search_results: search_artwork() 또는 search_general()의 결과
            
        Returns:
            List[str]: 텍스트 스니펫 리스트
        """
        snippets = []
        
        if not search_results.get("success") or not search_results.get("results"):
            return snippets
        
        for result in search_results["results"]:
            # 제목 추가
            if result.get("title"):
                snippets.append(f"제목: {result['title']}")
            
            # 설명/스니펫 추가
            if result.get("description"):
                snippets.append(f"설명: {result['description']}")
            elif result.get("snippet"):
                snippets.append(f"내용: {result['snippet']}")
            
            # URL 추가 (참고용)
            if result.get("url"):
                snippets.append(f"출처: {result['url']}")
            
            snippets.append("---")  # 구분자
        
        return snippets[:20]  # 최대 20개 스니펫
