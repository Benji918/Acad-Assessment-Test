import os
from typing import Dict, Any, List
from decimal import Decimal
from django.conf import settings
from .base import BaseGradingService
from mistralai import Mistral


try:
    from google import genai
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

class MistralAnalysisService(BaseGradingService):
    '''
    Optional Mistra AI service for advanced analysis and suggestions.
    This service enhances the grading with AI-powered insights.
    '''

    def __init__(self):
        if not MISTRAL_AVAILABLE:
            raise ImportError("Package is not installed")

        self.model = "mistral-medium-latest"
        api_key = settings.MISTRAL_API_KEY
        if not api_key:
            raise ValueError("MISTRAL_API_KEY is not configured")

        self.client = Mistral(api_key=api_key)


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

        submission_context = self._prepare_submission_context(submission)

        prompt = self._create_analysis_prompt(submission_context)

        try:
            response = self.client.chat.complete(
                model = self.model,
                messages = [
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ]
            )

            analysis_text = response.choices[0].message.content


            return {
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

Keep the feedback encouraging, constructive, and specific. Focus on learning outcomes. Give the response in text format only not MARKDOWN
also do not make any of the texts bold using the *
"""

        return prompt

