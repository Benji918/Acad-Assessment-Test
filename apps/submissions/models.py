from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.exams.models import Exam, Question

class Submission(models.Model):
    '''Student submission for an exam.'''

    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='submissions')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    obtained_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_graded = models.BooleanField(default=False)
    graded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'submissions'
        ordering = ['-created_at']
        unique_together = ('student', 'exam')
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['exam', 'is_graded']),
            models.Index(fields=['submitted_at']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

    def calculate_percentage(self):
        if self.total_marks > 0:
            self.percentage = (self.obtained_marks / self.total_marks) * 100
        else:
            self.percentage = 0
        return self.percentage

class Answer(models.Model):
    '''Individual answer to a question in a submission.'''
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    marks_obtained = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    marks_allocated = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    feedback = models.TextField(blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'answers'
        unique_together = ('submission', 'question')
        indexes = [
            models.Index(fields=['submission', 'question']),
        ]

    def __str__(self):
        return f"Answer to Q{self.question.order} by {self.submission.student.username}"