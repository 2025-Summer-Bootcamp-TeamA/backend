from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, AsyncMock, MagicMock
import json


class NearbyMuseumViewTestCase(APITestCase):
    """근처 박물관 검색 API 테스트"""
    
    def setUp(self):
        self.url = reverse('place:nearby_museums_search')
        self.valid_payload = {
            "latitude": 37.5665,
            "longitude": 126.9780,
            "radius": 3000,
            "keyword": "museum"
        }
    
    @patch('apps.place.views.async_to_sync')
    def test_valid_request_structure(self, mock_async_to_sync):
        """유효한 요청 구조 테스트"""
        # MCP 응답 모킹
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            'content': [MagicMock(text=json.dumps({
                'places': [
                    {
                        "name": "테스트 박물관",
                        "address": "서울시 중구 테스트로 123",
                        "place_id": "test_place_id_123",
                        "latitude": 37.5665,
                        "longitude": 126.9780
                    }
                ]
            }))]
        }
        
        # async_to_sync 모킹
        mock_search_func = MagicMock(return_value=mock_result)
        mock_async_to_sync.return_value = mock_search_func
        
        response = self.client.post(self.url, self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        if response.data:
            place = response.data[0]
            self.assertIn('name', place)
            self.assertIn('address', place)
            self.assertIn('place_id', place)
            self.assertIn('rank', place)
    
    def test_invalid_latitude(self):
        """잘못된 위도 값 테스트"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['latitude'] = 91.0  # 유효 범위 초과
        
        response = self.client.post(self.url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('latitude', response.data)
    
    def test_invalid_longitude(self):
        """잘못된 경도 값 테스트"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['longitude'] = -181.0  # 유효 범위 초과
        
        response = self.client.post(self.url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('longitude', response.data)
    
    def test_missing_required_fields(self):
        """필수 필드 누락 테스트"""
        invalid_payload = {"radius": 3000}  # latitude, longitude 누락
        
        response = self.client.post(self.url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('latitude', response.data)
        self.assertIn('longitude', response.data)
    
    @patch('apps.place.views.async_to_sync')
    def test_optional_fields_default_values(self, mock_async_to_sync):
        """선택 필드의 기본값 테스트"""
        minimal_payload = {
            "latitude": 37.5665,
            "longitude": 126.9780
        }
        
        # MCP 응답 모킹 (빈 결과)
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            'content': [MagicMock(text=json.dumps({'places': []}))]
        }
        
        mock_search_func = MagicMock(return_value=mock_result)
        mock_async_to_sync.return_value = mock_search_func
        
        response = self.client.post(self.url, minimal_payload, format='json')
        
        # async_to_sync가 호출되었는지 확인
        mock_async_to_sync.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
