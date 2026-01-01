from rest_framework import serializers
from django.utils import timezone
from .models import Exam, Question

class QuestionSerializer(serializers.ModelSerializer):
    '''Serializer for Question model.'''

    class Meta:
        model = Question
        fields = ('id', 'exam', 'question_type', 'question_text', 'expected_answer',
                  'keywords', 'marks', 'order', 'metadata', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_keywords(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Keywords must be a list.")
        return [kw.strip().lower() for kw in value if kw.strip()]

class QuestionListSerializer(serializers.ModelSerializer):
    '''Simplified serializer for listing questions (hides answers).'''

    class Meta:
        model = Question
        fields = ('id', 'question_type', 'question_text', 'marks', 'order')
        read_only_fields = ('id',)

class ExamSerializer(serializers.ModelSerializer):
    '''Serializer for Exam model.'''

    questions = QuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = ('id', 'course', 'title', 'description', 'duration_minutes',
                  'start_time', 'end_time', 'total_marks', 'passing_marks',
                  'metadata', 'is_published', 'questions', 'questions_count',
                  'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_questions_count(self, obj):
        return obj.questions.count()

    def get_is_active(self, obj):
        return obj.is_active()

    def validate(self, attrs):
        if attrs.get('end_time') and attrs.get('start_time'):
            if attrs['end_time'] <= attrs['start_time']:
                raise serializers.ValidationError("End time must be after start time.")

        if attrs.get('passing_marks', 0) > attrs.get('total_marks', 0):
            raise serializers.ValidationError("Passing marks cannot exceed total marks.")

        return attrs

class ExamListSerializer(serializers.ModelSerializer):
    '''Simplified serializer for listing exams.'''

    course_code = serializers.CharField(source='course.code', read_only=True)
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = ('id', 'course', 'course_code', 'title', 'duration_minutes',
                  'start_time', 'end_time', 'total_marks', 'questions_count',
                  'is_published')

    def get_questions_count(self, obj):
        return obj.questions.count()