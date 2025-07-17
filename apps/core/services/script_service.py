import re
import logging
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TextType(Enum):
    """텍스트 유형 분류"""
    ARTWORK_DESCRIPTION = "artwork_description"  # 작품 설명
    ARTWORK_TITLE = "artwork_title"             # 작품명
    EXHIBITION_INFO = "exhibition_info"         # 전시 정보
    ARTIST_INFO = "artist_info"                 # 작가 정보
    OTHER = "other"                             # 기타


@dataclass
class AnalysisResult:
    """텍스트 분석 결과"""
    text_type: TextType
    confidence: float  # 0.0 ~ 1.0
    is_description: bool
    reasoning: str
    metadata: Dict = None


class ScriptAnalyzer:
    """
    OCR 텍스트에서 작품 설명 여부를 판단하는 규칙 기반 분석기
    
    단계별 처리:
    1. 빠른 규칙 기반 필터링 (90% 케이스)
    2. 상세 패턴 분석 (10% 케이스)
    """
    
    def __init__(self):
        self.description_keywords = [
            '작품 해설', '작품 설명', '설명', '해설', '소개', '배경', 
            '의미', '표현', '기법', '특징', '주제', '상징',
            'Description', 'About', 'Overview'
        ]
        
        self.title_keywords = [
            '작품명', '제목', '작품', 'Title', '타이틀'
        ]
        
        self.exhibition_keywords = [
            '전시', '기간', '장소', '주최', '후원', '관람', '입장',
            'Exhibition', 'Gallery', 'Museum', '년', '월', '일'
        ]
        
        self.artist_keywords = [
            '작가', '화가', '예술가', '아티스트', '출생', '활동',
            'Artist', 'Painter', '작가 소개', '프로필'
        ]

    def analyze_text(self, text: str) -> AnalysisResult:
        """
        텍스트를 분석하여 작품 설명 여부와 유형을 판단
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            AnalysisResult: 분석 결과
        """
        if not text or not text.strip():
            return AnalysisResult(
                text_type=TextType.OTHER,
                confidence=1.0,
                is_description=False,
                reasoning="빈 텍스트"
            )
        
        text = text.strip()
        
        # Stage 1: 빠른 규칙 기반 필터링
        quick_result = self._quick_rule_filter(text)
        if quick_result.confidence >= 0.8:
            return quick_result
        
        # Stage 2: 상세 패턴 분석
        pattern_result = self._pattern_analysis(text)
        return pattern_result

    def _quick_rule_filter(self, text: str) -> AnalysisResult:
        """빠른 규칙 기반 필터링"""
        
        # 🚨 명확하게 "설명 아님" 케이스들
        
        # 1. 너무 짧은 텍스트
        if len(text) < 15:
            return AnalysisResult(
                text_type=TextType.OTHER,
                confidence=0.9,
                is_description=False,
                reasoning="텍스트가 너무 짧음 (15자 미만)"
            )
        
        # 2. 순수 숫자/날짜/기호
        if re.match(r'^[\d\-\.\s\/\(\)]+$', text):
            return AnalysisResult(
                text_type=TextType.EXHIBITION_INFO,
                confidence=0.95,
                is_description=False,
                reasoning="숫자/날짜/기호만 포함"
            )
        
        # 3. 매우 짧은 제목 형태
        if len(text) <= 30 and not any(char in text for char in '.!?'):
            title_indicators = ['작품명:', 'Title:', '"', "'", '《', '》']
            if any(indicator in text for indicator in title_indicators):
                return AnalysisResult(
                    text_type=TextType.ARTWORK_TITLE,
                    confidence=0.9,
                    is_description=False,
                    reasoning="짧은 제목 형태"
                )
        
        # 🚨 명확하게 "설명임" 케이스들
        
        # 1. 설명 키워드 포함
        if any(keyword in text for keyword in self.description_keywords):
            return AnalysisResult(
                text_type=TextType.ARTWORK_DESCRIPTION,
                confidence=0.95,
                is_description=True,
                reasoning="설명 키워드 포함"
            )
        
        # 2. 긴 텍스트 + 완전한 문장 구조
        korean_endings = ['다.', '요.', '음.', '임.', '니다.', '습니다.', '죠.']
        english_endings = ['. ', '! ', '? ']
        
        sentence_count = sum(text.count(ending) for ending in korean_endings + english_endings)
        
        if len(text) > 100 and sentence_count >= 2:
            return AnalysisResult(
                text_type=TextType.ARTWORK_DESCRIPTION,
                confidence=0.85,
                is_description=True,
                reasoning=f"긴 텍스트({len(text)}자) + 복수 문장({sentence_count}개)"
            )
        
        # 중간 신뢰도: 패턴 분석으로 넘어감
        return AnalysisResult(
            text_type=TextType.OTHER,
            confidence=0.5,
            is_description=False,
            reasoning="패턴 분석 필요"
        )

    def _pattern_analysis(self, text: str) -> AnalysisResult:
        """상세 패턴 분석"""
        
        confidence_scores = {
            TextType.ARTWORK_DESCRIPTION: 0.0,
            TextType.ARTWORK_TITLE: 0.0,
            TextType.EXHIBITION_INFO: 0.0,
            TextType.ARTIST_INFO: 0.0,
            TextType.OTHER: 0.0
        }
        
        # 키워드 기반 점수 계산
        desc_score = sum(1 for keyword in self.description_keywords if keyword in text)
        title_score = sum(1 for keyword in self.title_keywords if keyword in text)
        exhibition_score = sum(1 for keyword in self.exhibition_keywords if keyword in text)
        artist_score = sum(1 for keyword in self.artist_keywords if keyword in text)
        
        confidence_scores[TextType.ARTWORK_DESCRIPTION] += desc_score * 0.2
        confidence_scores[TextType.ARTWORK_TITLE] += title_score * 0.2
        confidence_scores[TextType.EXHIBITION_INFO] += exhibition_score * 0.2
        confidence_scores[TextType.ARTIST_INFO] += artist_score * 0.2
        
        # 길이 기반 점수
        if len(text) > 80:
            confidence_scores[TextType.ARTWORK_DESCRIPTION] += 0.3
        elif len(text) < 40:
            confidence_scores[TextType.ARTWORK_TITLE] += 0.2
        
        # 문장 구조 점수
        korean_endings = ['다.', '요.', '음.', '임.', '니다.', '습니다.']
        sentence_count = sum(text.count(ending) for ending in korean_endings)
        
        if sentence_count >= 2:
            confidence_scores[TextType.ARTWORK_DESCRIPTION] += 0.3
        elif sentence_count == 0:
            confidence_scores[TextType.ARTWORK_TITLE] += 0.2
        
        # 특수 패턴 점수
        if re.search(r'[0-9]{4}년|[0-9]{1,2}월|[0-9]{1,2}일', text):
            confidence_scores[TextType.EXHIBITION_INFO] += 0.4
        
        if re.search(r'["""].*["""]|《.*》|「.*」', text):
            confidence_scores[TextType.ARTWORK_TITLE] += 0.3
        
        # 최고 점수 유형 결정
        best_type = max(confidence_scores, key=confidence_scores.get)
        max_confidence = confidence_scores[best_type]
        
        # 최소 신뢰도 보장
        if max_confidence < 0.3:
            # 애매한 경우 길이 기반으로 기본 판단
            if len(text) > 50:
                best_type = TextType.ARTWORK_DESCRIPTION
                max_confidence = 0.6
            else:
                best_type = TextType.OTHER
                max_confidence = 0.6
        
        is_description = best_type == TextType.ARTWORK_DESCRIPTION
        
        return AnalysisResult(
            text_type=best_type,
            confidence=min(max_confidence, 0.9),  # 최대 0.9로 제한
            is_description=is_description,
            reasoning=f"패턴 분석 결과: {best_type.value} (점수: {max_confidence:.2f})",
            metadata={"scores": confidence_scores}
        )

    def is_likely_description(self, text: str) -> Tuple[bool, float]:
        """
        규칙 기반으로 작품 설명 여부 판단
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            Tuple[bool, float]: (설명여부, 신뢰도)
        """
        result = self.analyze_text(text)
        return result.is_description, result.confidence

    def batch_analyze(self, texts: List[str]) -> List[AnalysisResult]:
        """여러 텍스트를 한번에 분석"""
        return [self.analyze_text(text) for text in texts]

    def get_description_texts(self, texts: List[str], min_confidence: float = 0.7) -> List[str]:
        """신뢰도가 높은 설명 텍스트들만 필터링"""
        results = self.batch_analyze(texts)
        return [
            texts[i] for i, result in enumerate(results)
            if result.is_description and result.confidence >= min_confidence
        ]
