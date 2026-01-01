from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseGradingService(ABC):
    '''Abstract base class for grading services following Open/Closed Principle.'''

    @abstractmethod
    def grade_submission(self, submission) -> Dict[str, Any]:
        '''
        Grade a submission and return grading results.

        Args:
            submission: Submission instance to grade

        Returns:
            Dictionary containing grading results
        '''
        pass

    @abstractmethod
    def grade_answer(self, answer, question) -> Dict[str, Any]:
        '''
        Grade an individual answer.

        Args:
            answer: Answer instance
            question: Question instance

        Returns:
            Dictionary containing marks and feedback
        '''
        pass

    def calculate_marks_percentage(self, obtained: float, total: float) -> float:
        '''Calculate percentage of marks obtained.'''
        if total == 0:
            return 0.0
        return round((obtained / total) * 100, 2)