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
    def move_file(source_url: str, source_folder: str, target_folder: str) -> Optional[str]:
        """
        GCS 내에서 파일을 한 폴더에서 다른 폴더로 이동
        
        Args:
            source_url (str): 원본 파일 URL
            source_folder (str): 원본 폴더명
            target_folder (str): 대상 폴더명
            
        Returns:
            Optional[str]: 이동된 파일의 새 URL 또는 None (실패 시)
        """
        try:
            # URL에서 파일 경로 추출
            from urllib.parse import urlparse
            parsed_url = urlparse(source_url)
            file_path = parsed_url.path.lstrip('/')
            
            # 원본 폴더가 경로에 포함되어 있는지 확인
            if not file_path.startswith(source_folder):
                logger.error(f"원본 폴더가 경로에 포함되지 않음: {file_path}")
                return None
            
            # 대상 경로 생성
            relative_path = file_path[len(source_folder):].lstrip('/')
            target_path = f"{target_folder}/{relative_path}"
            
            # 파일 복사
            if default_storage.exists(file_path):
                with default_storage.open(file_path, 'rb') as source_file:
                    target_gcs_path = default_storage.save(target_path, source_file)
                    target_url = default_storage.url(target_gcs_path)
                
                # 원본 파일 삭제
                default_storage.delete(file_path)
                
                logger.info(f"GCS 파일 이동 성공: {file_path} -> {target_path}")
                return target_url
            else:
                logger.error(f"원본 파일이 존재하지 않음: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"GCS 파일 이동 실패: {e}")
            return None
    
    @staticmethod
    def copy_file(source_url: str, source_folder: str, target_folder: str) -> Optional[str]:
        """
        GCS 내에서 파일을 한 폴더에서 다른 폴더로 복사
        
        Args:
            source_url (str): 원본 파일 URL
            source_folder (str): 원본 폴더명
            target_folder (str): 대상 폴더명
            
        Returns:
            Optional[str]: 복사된 파일의 새 URL 또는 None (실패 시)
        """
        try:
            # URL에서 파일 경로 추출
            from urllib.parse import urlparse
            parsed_url = urlparse(source_url)
            file_path = parsed_url.path.lstrip('/')
            
            # 원본 폴더가 경로에 포함되어 있는지 확인
            if not file_path.startswith(source_folder):
                logger.error(f"원본 폴더가 경로에 포함되지 않음: {file_path}")
                return None
            
            # 대상 경로 생성
            relative_path = file_path[len(source_folder):].lstrip('/')
            target_path = f"{target_folder}/{relative_path}"
            
            # 파일 복사
            if default_storage.exists(file_path):
                with default_storage.open(file_path, 'rb') as source_file:
                    target_gcs_path = default_storage.save(target_path, source_file)
                    target_url = default_storage.url(target_gcs_path)
                
                logger.info(f"GCS 파일 복사 성공: {file_path} -> {target_path}")
                return target_url
            else:
                logger.error(f"원본 파일이 존재하지 않음: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"GCS 파일 복사 실패: {e}")
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


def move_gcs_file(source_url: str, source_folder: str, target_folder: str) -> Optional[str]:
    """GCS 내에서 파일을 한 폴더에서 다른 폴더로 이동"""
    return GCSStorageService.move_file(source_url, source_folder, target_folder)


def copy_gcs_file(source_url: str, source_folder: str, target_folder: str) -> Optional[str]:
    """GCS 내에서 파일을 한 폴더에서 다른 폴더로 복사"""
    return GCSStorageService.copy_file(source_url, source_folder, target_folder) 