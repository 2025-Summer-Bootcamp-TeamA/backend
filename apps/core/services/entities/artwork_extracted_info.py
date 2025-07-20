from dataclasses import dataclass
from apps.core.services.entities.artwork_basic_info import ArtworkBasicInfo
from apps.core.services.entities.extraction_metadata import ExtractionMetadata
from apps.core.services.entities.web_search_info import WebSearchInfo
from apps.core.services.entities.content_fetch_info import ContentFetchInfo


@dataclass
class ArtworkExtractedInfo:
    """모든 정보를 통합하는 컨테이너"""
    basic_info: ArtworkBasicInfo
    metadata: ExtractionMetadata
    web_search: WebSearchInfo
    content_fetch: ContentFetchInfo 