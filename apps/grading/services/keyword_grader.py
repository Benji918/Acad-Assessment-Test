import re
from typing import Dict, Any, List
from decimal import Decimal
from .base import BaseGradingService

class KeywordGradingService(BaseGradingService):
    '''
    Grading service using keyword matching and density analysis.
    Implements Single Responsibility Principle.
    '''

    def __init__(self):
        self.min_keyword_match_percentage = 30  # Minimum 30% keywords must match
        self.max_marks_for_keyword_match = 0.7  # Max 70% of marks for keyword matching
        self.density_weight = 0.3  # 30% weight for content density

    def grade_submission(self, submission) -> Dict[str, Any]:
        '''Grade all answers in a submission.'''

        total_obtained = Decimal('0.00')
        answer_results = []

        for answer in submission.answers.all():
            result = self.grade_answer(answer, answer.question)

            answer.marks_obtained = Decimal(str(result['marks_obtained']))
            answer.feedback = result['feedback']
            answer.save()

            total_obtained += answer.marks_obtained
            answer_results.append(result)

        # Update submission
        submission.obtained_marks = total_obtained
        submission.percentage = submission.calculate_percentage()
        submission.save()

        return {
            'total_obtained': float(total_obtained),
            'total_marks': float(submission.total_marks),
            'percentage': float(submission.percentage),
            'answer_results': answer_results
        }

    def grade_answer(self, answer, question) -> Dict[str, Any]:
        '''Grade an individual answer using keyword matching.'''

        answer_text = answer.answer_text.lower().strip()
        expected_answer = question.expected_answer.lower().strip()
        keywords = [kw.lower() for kw in question.keywords] if question.keywords else []

        # If no keywords provided, extract from expected answer
        if not keywords:
            keywords = self._extract_keywords(expected_answer)

        # Calculate keyword match score
        keyword_score = self._calculate_keyword_match(answer_text, keywords)

        # Calculate content density score
        density_score = self._calculate_content_density(
            answer_text,
            expected_answer,
            question.marks
        )

        # Calculate final marks
        keyword_marks = keyword_score * self.max_marks_for_keyword_match * question.marks
        density_marks = density_score * self.density_weight * question.marks
        total_marks = keyword_marks + density_marks

        # Generate feedback
        feedback = self._generate_feedback(keyword_score, density_score, keywords)

        return {
            'marks_obtained': round(total_marks, 2),
            'marks_allocated': question.marks,
            'keyword_match_percentage': round(keyword_score * 100, 2),
            'density_score': round(density_score * 100, 2),
            'feedback': feedback
        }

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        '''Extract important keywords from text.'''

        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'it', 'its', 'they', 'them', 'their'
        }

        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text)

        # Filter and count
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]

    def _calculate_keyword_match(self, answer_text: str, keywords: List[str]) -> float:
        '''Calculate keyword match percentage.'''

        if not keywords:
            return 0.5  # Default score if no keywords

        matches = 0
        for keyword in keywords:
            if keyword in answer_text:
                matches += 1

        return matches / len(keywords)

    def _calculate_content_density(
            self,
            answer_text: str,
            expected_answer: str,
            max_marks: int
    ) -> float:
        '''Calculate content density score based on answer length and relevance.'''

        answer_words = len(answer_text.split())
        expected_words = len(expected_answer.split())

        if expected_words == 0:
            return 0.5

        # Calculate length ratio (with diminishing returns for very long answers)
        length_ratio = min(answer_words / expected_words, 1.5)

        # Normalize to 0-1 scale
        if length_ratio < 0.3:
            # Too short
            return length_ratio / 0.3 * 0.5
        elif length_ratio > 1.5:
            # Too long (slightly penalize)
            return 0.9
        else:
            # Good length
            return 0.7 + (length_ratio - 0.3) * 0.3 / 1.2

    def _generate_feedback(
            self,
            keyword_score: float,
            density_score: float,
            keywords: List[str]
    ) -> str:
        '''Generate constructive feedback based on scores.'''

        feedback_parts = []

        # Keyword feedback
        if keyword_score >= 0.7:
            feedback_parts.append("Excellent coverage of key concepts.")
        elif keyword_score >= 0.5:
            feedback_parts.append("Good coverage of main points, but some key concepts are missing.")
        else:
            feedback_parts.append("Several important concepts are not addressed.")
            if keywords:
                missing_sample = keywords[:3]
                feedback_parts.append(f"Consider including: {', '.join(missing_sample)}.")

        # Density feedback
        if density_score >= 0.7:
            feedback_parts.append("Answer length and detail are appropriate.")
        elif density_score < 0.4:
            feedback_parts.append("Answer could be more detailed and comprehensive.")

        return " ".join(feedback_parts)