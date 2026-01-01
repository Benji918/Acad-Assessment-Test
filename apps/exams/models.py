
from django.db import models
from django.core.validators import MinValueValidator
from apps.courses.models import Course

class Exam(models.Model):
    '''Exam model representing assessments for courses.'''

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_marks = models.PositiveIntegerField(default=0)
    passing_marks = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'exams'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'is_published']),
            models.Index(fields=['start_time', 'end_time']),
        ]

    def __str__(self):
        return f"{self.title} - {self.course.code}"

    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_time <= now <= self.end_time

class Question(models.Model):
    '''Question model for exam questions.'''

    QUESTION_TYPES = (
        ('essay', 'Essay'),
        ('short_answer', 'Short Answer'),
        ('paragraph', 'Paragraph'),
    )

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='essay')
    question_text = models.TextField()
    expected_answer = models.TextField(help_text='Model answer or key points')
    keywords = models.JSONField(
        default=list,
        help_text='List of keywords for grading'
    )
    marks = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    order = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'questions'
        ordering = ['exam', 'order']
        indexes = [
            models.Index(fields=['exam', 'order']),
        ]

    def __str__(self):
        return f"Q{self.order} - {self.exam.title}"