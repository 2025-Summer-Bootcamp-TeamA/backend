import logging
from typing import Optional
from .script_service import ScriptAnalyzer, AnalysisResult
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)


class HybridAnalyzer:
    """
    하이브리드 텍스트 분석기
    
    전략:
    1단계: ScriptAnalyzer로 빠른 규칙 기반 분석 (90% 케이스)
    2단계: 신뢰도 낮으면 GeminiService로 AI 분석 (10% 케이스)
    
    장점:
    - 빠른 처리 (대부분 규칙 기반)
    - 높은 정확도 (애매한 케이스는 AI)
    - 비용 효율적 (필요시에만 AI 호출)
    """
    
    def __init__(self, gemini_credentials_path: Optional[str] = None, 
                 confidence_threshold: float = 0.75):
        """
        하이브리드 분석기 초기화
        
        Args:
            gemini_credentials_path: Gemini 서비스 계정 파일 경로
            confidence_threshold: AI 사용 기준 신뢰도 (이하면 AI 사용)
        """
        # 1단계: 규칙 기반 분석기 (항상 사용)
        self.script_analyzer = ScriptAnalyzer()
        
        # 2단계: AI 분석기 (조건부 사용)
        self.gemini_service = None
        self.gemini_available = False
        
        try:
            self.gemini_service = GeminiService(gemini_credentials_path)
            # 연결 테스트
            if self.gemini_service.test_connection():
                self.gemini_available = True
                logger.info("✅ Gemini AI 서비스 연결 성공 - 하이브리드 모드 활성화")
            else:
                logger.warning("⚠️ Gemini AI 연결 실패 - 규칙 기반 모드만 사용")
        except Exception as e:
            logger.warning(f"⚠️ Gemini AI 초기화 실패: {e} - 규칙 기반 모드만 사용")
        
        self.confidence_threshold = confidence_threshold
        
        # 통계 추적
        self.stats = {
            "total_analyzed": 0,
            "rule_based_only": 0,
            "ai_assisted": 0,
            "ai_success": 0,
            "ai_fallback": 0
        }
    
    def analyze_text(self, text: str) -> AnalysisResult:
        """
        하이브리드 텍스트 분석
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            AnalysisResult: 분석 결과 (source 메타데이터로 어떤 방식 사용했는지 표시)
        """
        self.stats["total_analyzed"] += 1
        
        if not text or not text.strip():
            return AnalysisResult(
                text_type=self.script_analyzer.analyze_text("").text_type,
                confidence=1.0,
                is_description=False,
                reasoning="빈 텍스트",
                metadata={"source": "rule_based", "stage": "input_validation"}
            )
        
        # 🔥 1단계: 규칙 기반 분석 (빠르고 무료)
        rule_result = self.script_analyzer.analyze_text(text)
        
        # 신뢰도가 높으면 바로 반환 (90% 케이스)
        if rule_result.confidence >= self.confidence_threshold:
            self.stats["rule_based_only"] += 1
            
            # 메타데이터에 소스 정보 추가
            if not rule_result.metadata:
                rule_result.metadata = {}
            rule_result.metadata.update({
                "source": "rule_based",
                "stage": "confident_result",
                "original_confidence": rule_result.confidence
            })
            
            logger.debug(f"규칙 기반 완료 (신뢰도: {rule_result.confidence:.2f}): {text[:50]}...")
            return rule_result
        
        # 🤖 2단계: AI 분석 (애매한 경우만, 10% 케이스)
        if self.gemini_available:
            return self._ai_analysis(text, rule_result)
        else:
            # AI 사용 불가시 규칙 기반 결과 반환
            self.stats["ai_fallback"] += 1
            
            if not rule_result.metadata:
                rule_result.metadata = {}
            rule_result.metadata.update({
                "source": "rule_based_fallback",
                "stage": "ai_unavailable",
                "original_confidence": rule_result.confidence,
                "reason": "AI 서비스 사용 불가"
            })
            
            logger.debug(f"AI 불가 - 규칙 기반 fallback: {text[:50]}...")
            return rule_result
    
    def _ai_analysis(self, text: str, rule_result: AnalysisResult) -> AnalysisResult:
        """AI 분석 수행"""
        self.stats["ai_assisted"] += 1
        
        try:
            # Gemini로 AI 분석
            ai_is_description = self.gemini_service.is_description(text)
            self.stats["ai_success"] += 1
            
            # AI 결과를 AnalysisResult 형식으로 변환
            ai_result = AnalysisResult(
                text_type=rule_result.text_type,  # 텍스트 유형은 규칙 기반 결과 사용
                confidence=0.95,  # AI 결과는 높은 신뢰도
                is_description=ai_is_description,
                reasoning=f"하이브리드 분석: 규칙 기반 신뢰도 {rule_result.confidence:.2f} → AI 분석 적용",
                metadata={
                    "source": "hybrid_ai",
                    "stage": "ai_analysis",
                    "rule_confidence": rule_result.confidence,
                    "rule_result": rule_result.is_description,
                    "ai_result": ai_is_description,
                    "text_length": len(text)
                }
            )
            
            logger.debug(f"AI 분석 완료 (규칙: {rule_result.is_description} → AI: {ai_is_description}): {text[:50]}...")
            return ai_result
            
        except Exception as e:
            # AI 실패시 규칙 기반 결과 사용
            self.stats["ai_fallback"] += 1
            logger.warning(f"AI 분석 실패, 규칙 기반 사용: {e}")
            
            if not rule_result.metadata:
                rule_result.metadata = {}
            rule_result.metadata.update({
                "source": "rule_based_fallback",
                "stage": "ai_error",
                "original_confidence": rule_result.confidence,
                "error": str(e)
            })
            
            return rule_result
    
    def is_description(self, text: str) -> bool:
        """
        간단한 설명 여부 판단 (boolean만 반환)
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            bool: 설명이면 True, 아니면 False
        """
        result = self.analyze_text(text)
        return result.is_description
    
    def get_analysis_stats(self) -> dict:
        """
        분석 통계 반환
        
        Returns:
            dict: 사용 패턴 통계
        """
        total = self.stats["total_analyzed"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "rule_based_percentage": (self.stats["rule_based_only"] / total) * 100,
            "ai_usage_percentage": (self.stats["ai_assisted"] / total) * 100,
            "ai_success_rate": (self.stats["ai_success"] / max(self.stats["ai_assisted"], 1)) * 100,
        }
    

