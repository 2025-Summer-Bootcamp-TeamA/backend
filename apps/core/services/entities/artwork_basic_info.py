from dataclasses import dataclass


@dataclass
class ArtworkBasicInfo:
    """작품의 핵심 정보만 담당"""
    title: str = "작품명 확인 불가"
    artist: str = "작가 정보 없음"
    year: str = "제작연도 미상"
    description: str = "작품 설명 없음" 