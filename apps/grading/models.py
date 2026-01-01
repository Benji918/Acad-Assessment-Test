from django.db import models
from apps.submissions.models import Submission

class GradingResult(models.Model):
    '''Stores detailed grading results and AI-generated insights.'''

    GRADING_METHODS = (
        ('keyword', 'Keyword Matching'),
        ('ai_assisted', 'AI Assisted'),
    )

    submission = models.OneToOneField(
        Submission,
        on_delete=models.CASCADE,
        related_name='grading_result'
    )
    grading_method = models.CharField(max_length=20, choices=GRADING_METHODS, default='keyword')

    # Performance analysis (from Gemini)
    performance_analysis = models.JSONField(default=dict, blank=True)
    suggestions = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    detailed_scores = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'grading_results'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['submission', 'grading_method']),
        ]

    def __str__(self):
        return f"Grading Result for {self.submission}"