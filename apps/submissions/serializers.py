from rest_framework import serializers
from django.utils import timezone
from .models import Submission, Answer
from apps.exams.serializers import QuestionListSerializer
from core.validators import sanitize_html_input, validate_answer_length

class AnswerSerializer(serializers.ModelSerializer):
    '''Serializer for Answer model.'''

    question_details = QuestionListSerializer(source='question', read_only=True)

    class Meta:
        model = Answer
        fields = ('id', 'submission', 'question', 'question_details', 'answer_text',
                  'marks_obtained', 'marks_allocated', 'feedback', 'answered_at')
        read_only_fields = ('id', 'marks_obtained', 'marks_allocated', 'feedback', 'answered_at')

    def validate_answer_text(self, value):
        validate_answer_length(value)
        # Sanitize input to prevent XSS
        return sanitize_html_input(value)

class SubmissionCreateSerializer(serializers.Serializer):
    '''Serializer for creating submissions with answers.'''

    exam = serializers.UUIDField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("At least one answer is required.")

        for answer in value:
            if 'question' not in answer or 'answer_text' not in answer:
                raise serializers.ValidationError(
                    "Each answer must have 'question' and 'answer_text' fields."
                )

            # Validate and sanitize each answer
            answer_text = answer['answer_text']
            validate_answer_length(answer_text)
            answer['answer_text'] = sanitize_html_input(answer_text)

        return value

class SubmissionSerializer(serializers.ModelSerializer):
    '''Serializer for Submission model.'''

    answers = AnswerSerializer(many=True, read_only=True)
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)

    class Meta:
        model = Submission
        fields = ('id', 'student', 'student_name', 'exam', 'exam_title',
                  'started_at', 'submitted_at', 'status', 'obtained_marks',
                  'total_marks', 'percentage', 'is_graded', 'graded_at',
                  'answers', 'created_at')
        read_only_fields = ('id', 'student', 'started_at', 'submitted_at',
                            'status', 'obtained_marks', 'total_marks', 'percentage',
                            'is_graded', 'graded_at', 'created_at')

class SubmissionListSerializer(serializers.ModelSerializer):
    '''Simplified serializer for listing submissions.'''

    exam_title = serializers.CharField(source='exam.title', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)

    class Meta:
        model = Submission
        fields = ('id', 'student', 'student_name', 'exam', 'exam_title',
                  'submitted_at', 'status', 'obtained_marks', 'total_marks',
                  'percentage', 'is_graded')