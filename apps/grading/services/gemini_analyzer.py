import os
from typing import Dict, Any, List
from decimal import Decimal
from django.conf import settings
from .base import BaseGradingService

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class GeminiAnalysisService(BaseGradingService):
    '''
    Optional Gemini AI service for advanced analysis and suggestions.
    This service enhances the grading with AI-powered insights.
    '''

    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package is not installed")

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.client = genai.Client(api_key=api_key)

    def grade_submission(self, submission) -> Dict[str, Any]:
        '''
        This service doesn't grade directly but provides analysis.
        Use KeywordGradingService for actual grading.
        '''
        raise NotImplementedError(
            "Gemini service is for analysis only. Use KeywordGradingService for grading."
        )

    def grade_answer(self, answer, question) -> Dict[str, Any]:
        '''Not implemented for Gemini service.'''
        raise NotImplementedError(
            "Gemini service is for analysis only. Use KeywordGradingService for grading."
        )

    def analyze_submission(self, submission) -> Dict[str, Any]:
        '''
        Analyze overall submission performance and provide suggestions.
        This is used AFTER keyword grading is complete.
        '''

        if not submission.is_graded:
            return {
                'error': 'Submission must be graded first'
            }

        # Prepare submission data for analysis
        submission_context = self._prepare_submission_context(submission)

        # Generate AI analysis
        prompt = self._create_analysis_prompt(submission_context)

        try:
            response = self.client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt)
            analysis_text = response.text

            return {
                'summary': self._extract_summary(analysis_text),
                'strengths': self._extract_strengths(analysis_text),
                'areas_for_improvement': self._extract_improvements(analysis_text),
                'suggestions': self._extract_suggestions(analysis_text),
                'full_analysis': analysis_text
            }

        except Exception as e:
            return {
                'error': f'AI analysis failed: {str(e)}'
            }

    def _prepare_submission_context(self, submission) -> Dict[str, Any]:
        '''Prepare submission data for AI analysis.'''

        answers_data = []
        for answer in submission.answers.all():
            answers_data.append({
                'question': answer.question.question_text,
                'expected_answer': answer.question.expected_answer,
                'student_answer': answer.answer_text,
                'marks_obtained': float(answer.marks_obtained),
                'marks_allocated': float(answer.marks_allocated),
                'feedback': answer.feedback
            })

        return {
            'exam_title': submission.exam.title,
            'total_marks': float(submission.total_marks),
            'obtained_marks': float(submission.obtained_marks),
            'percentage': float(submission.percentage),
            'answers': answers_data
        }

    def _create_analysis_prompt(self, context: Dict[str, Any]) -> str:
        '''Create prompt for Gemini analysis.'''

        prompt = f"""
You are an educational assessment expert. Analyze this student's exam performance and provide constructive feedback.

Exam: {context['exam_title']}
Score: {context['obtained_marks']}/{context['total_marks']} ({context['percentage']}%)

Detailed Answers:
"""

        for idx, answer in enumerate(context['answers'], 1):
            prompt += f"""
Question {idx}: {answer['question']}
Expected Answer: {answer['expected_answer']}
Student's Answer: {answer['student_answer']}
Score: {answer['marks_obtained']}/{answer['marks_allocated']}
Initial Feedback: {answer['feedback']}

"""

        prompt += """
Please provide:
1. SUMMARY: A brief overall assessment (2-3 sentences)
2. STRENGTHS: What the student did well (3-4 points)
3. AREAS FOR IMPROVEMENT: What needs work (3-4 points)
4. SUGGESTIONS: Specific actionable recommendations (3-4 points)

Keep the feedback encouraging, constructive, and specific. Focus on learning outcomes.
"""

        return prompt

    def _extract_summary(self, analysis: str) -> str:
        '''Extract summary section from analysis.'''
        return self._extract_section(analysis, 'SUMMARY')

    def _extract_strengths(self, analysis: str) -> List[str]:
        '''Extract strengths from analysis.'''
        return self._extract_bullet_points(analysis, 'STRENGTHS')

    def _extract_improvements(self, analysis: str) -> List[str]:
        '''Extract areas for improvement.'''
        return self._extract_bullet_points(analysis, 'AREAS FOR IMPROVEMENT')

    def _extract_suggestions(self, analysis: str) -> List[str]:
        '''Extract suggestions from analysis.'''
        return self._extract_bullet_points(analysis, 'SUGGESTIONS')

    def _extract_section(self, text: str, section_name: str) -> str:
        '''Extract a specific section from formatted text.'''

        import re
        pattern = rf'{section_name}:(.*?)(?=\n\n|\d+\.|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        return "Analysis not available"

    def _extract_bullet_points(self, text: str, section_name: str) -> List[str]:
        '''Extract bullet points from a section.'''

        import re
        section_text = self._extract_section(text, section_name)

        # Find numbered or bulleted items
        points = re.findall(r'(?:[\d]+\.|[-•*])\s*(.+?)(?=(?:[\d]+\.|[-•*]|\n\n|$))',
                            section_text, re.DOTALL)

        if points:
            return [p.strip() for p in points]

        # If no bullets found, return the whole section as one item
        return [section_text] if section_text else []