import uuid
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GCSStorageService:
    """Google Cloud Storage 업로드 및 관리 서비스"""
    
    @staticmethod
    def upload_file_from_url(image_url: str, folder: str = "uploads") -> Optional[str]:
        """
        URL에서 이미지를 다운로드하여 GCS에 업로드
        
        Args:
            image_url (str): 업로드할 이미지 URL
            folder (str): GCS 내 저장 폴더 (기본값: "uploads")
            
        Returns:
            Optional[str]: 업로드된 GCS URL 또는 None (실패 시)
        """
        try:
            # 이미지 다운로드
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_content = response.content
            
            # 고유 파일명 생성
            file_extension = GCSStorageService._get_file_extension(image_url)
            filename = f"{folder}/{uuid.uuid4().hex}{file_extension}"
            
            # GCS에 업로드
            gcs_path = default_storage.save(filename, ContentFile(image_content))
            gcs_url = default_storage.url(gcs_path)
            
            logger.info(f"GCS 업로드 성공: {gcs_url}")
            return gcs_url
            
        except requests.RequestException as e:
            logger.error(f"이미지 다운로드 실패 ({image_url}): {e}")
            return None
        except Exception as e:
            logger.error(f"GCS 업로드 실패: {e}")
            return None
    
    @staticmethod
    def upload_file_from_content(file_content: bytes, filename: str, folder: str = "uploads") -> Optional[str]:
        """
        파일 내용을 직접 GCS에 업로드
        
        Args:
            file_content (bytes): 업로드할 파일 내용
            filename (str): 파일명
            folder (str): GCS 내 저장 폴더
            
        Returns:
            Optional[str]: 업로드된 GCS URL 또는 None (실패 시)
        """
        try:
            # 고유 파일명 생성
            unique_filename = f"{folder}/{uuid.uuid4().hex}_{filename}"
            
            # GCS에 업로드
            gcs_path = default_storage.save(unique_filename, ContentFile(file_content))
            gcs_url = default_storage.url(gcs_path)
            
            logger.info(f"GCS 업로드 성공: {gcs_url}")
            return gcs_url
            
        except Exception as e:
            logger.error(f"GCS 업로드 실패: {e}")
            return None
    
    @staticmethod
    def upload_django_file(file_obj, folder: str = "uploads") -> Optional[str]:
        """
        Django UploadedFile을 GCS에 업로드
        
        Args:
            file_obj: Django UploadedFile 객체
            folder (str): GCS 내 저장 폴더
            
        Returns:
            Optional[str]: 업로드된 GCS URL 또는 None (실패 시)
        """
        try:
            # 고유 파일명 생성
            ext = GCSStorageService._get_file_extension(file_obj.name)
            filename = f"{folder}/{uuid.uuid4().hex}{ext}"
            
            # GCS에 업로드
            gcs_path = default_storage.save(filename, file_obj)
            gcs_url = default_storage.url(gcs_path)
            
            logger.info(f"GCS 업로드 성공: {gcs_url}")
            return gcs_url
            
        except Exception as e:
            logger.error(f"GCS 업로드 실패: {e}")
            return None
    
    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """파일명에서 확장자 추출"""
        if not filename:
            return ".png"  # 기본 확장자
        
        # URL인 경우 쿼리 파라미터 제거
        if "?" in filename:
            filename = filename.split("?")[0]
        
        # 확장자 추출
        import os
        ext = os.path.splitext(filename)[1]
        return ext if ext else ".png"


# 편의를 위한 함수들 (기존 코드와의 호환성)
def upload_image_to_gcs(image_url: str, folder: str = "avatars") -> Optional[str]:
    """이미지 URL을 GCS에 업로드 (기존 함수명 유지)"""
    return GCSStorageService.upload_file_from_url(image_url, folder)


def upload_file_to_gcs(file_obj, folder: str = "uploads") -> Optional[str]:
    """Django 파일을 GCS에 업로드"""
    return GCSStorageService.upload_django_file(file_obj, folder)


def upload_video_to_gcs(video_url: str, folder: str = "videos") -> Optional[str]:
    """영상 URL을 GCS에 업로드"""
    return GCSStorageService.upload_file_from_url(video_url, folder) 