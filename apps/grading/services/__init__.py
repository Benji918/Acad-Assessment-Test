from django.conf import settings
from .base import BaseGradingService
from .keyword_grader import SpacyGradingService


def get_gemini_service():
    from .gemini_analyzer import GeminiAnalysisService
    return GeminiAnalysisService()

class GradingServiceFactory:
    '''
    Factory pattern for creating grading service instances.
    Implements Dependency Inversion Principle.
    '''

    @staticmethod
    def get_service() -> BaseGradingService:
        '''Get the primary grading service (always KeywordGradingService).'''
        return SpacyGradingService()

    @staticmethod
    def get_analysis_service():
        '''Get optional AI analysis service if enabled.'''
        if getattr(settings, 'ENABLE_MISTRAL_GRADING', False):
            try:
                return get_gemini_service()
            except (ImportError, ValueError) as e:
                print(f"Gemini service unavailable: {e}")
                return None
        return None