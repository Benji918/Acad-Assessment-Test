from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Exam, Question
from .serializers import (
    ExamSerializer, ExamListSerializer,
    QuestionSerializer, QuestionListSerializer
)
from core.permissions import IsTeacher, IsStudent, IsEnrolledInCourse

class ExamViewSet(viewsets.ModelViewSet):
    '''ViewSet for Exam CRUD operations.'''

    queryset = Exam.objects.select_related('course').prefetch_related('questions')
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('course', 'is_published')

    def get_serializer_class(self):
        if self.action == 'list':
            return ExamListSerializer
        return ExamSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacher()]
        if self.action == 'start':
            return [IsStudent(), IsEnrolledInCourse()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.role == 'student':
            # Students only see published exams in their enrolled courses
            enrolled_courses = self.request.user.enrollments.filter(
                status='active'
            ).values_list('course_id', flat=True)

            queryset = queryset.filter(
                course_id__in=enrolled_courses,
                is_published=True
            )

        return queryset

    @action(detail=True, methods=['get'], permission_classes=[IsStudent, IsEnrolledInCourse])
    def start(self, request, pk=None):
        '''Endpoint to start an exam (returns questions without answers).'''
        exam = self.get_object()

        if not exam.is_published:
            return Response(
                {'success': False, 'message': 'Exam is not published'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not exam.is_active():
            return Response(
                {'success': False, 'message': 'Exam is not currently active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        questions = exam.questions.all()

        return Response({
            'success': True,
            'data': {
                'exam': ExamListSerializer(exam).data,
                'questions': QuestionListSerializer(questions, many=True).data,
                'started_at': timezone.now()
            }
        })

class QuestionViewSet(viewsets.ModelViewSet):
    '''ViewSet for Question CRUD operations.'''

    queryset = Question.objects.select_related('exam')
    serializer_class = QuestionSerializer
    permission_classes = (IsTeacher,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('exam', 'question_type')

    def perform_create(self, serializer):
        question = serializer.save()
        # Update exam total marks
        exam = question.exam
        exam.total_marks = sum(q.marks for q in exam.questions.all())
        exam.save()