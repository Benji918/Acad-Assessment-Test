from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

from .models import Submission, Answer
from .serializers import (
    SubmissionSerializer, SubmissionListSerializer,
    SubmissionCreateSerializer, AnswerSerializer
)
from apps.exams.models import Exam, Question
from apps.grading.services import GradingServiceFactory
from apps.grading.serializers import GradingResultSerializer
from core.permissions import IsStudent, IsOwnerOrReadOnly

class SubmissionViewSet(viewsets.ModelViewSet):
    '''ViewSet for Submission operations with secure student access.'''

    queryset = Submission.objects.select_related(
        'student', 'exam'
    ).prefetch_related('answers', 'answers__question')
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('exam', 'status', 'is_graded')

    def get_serializer_class(self):
        if self.action == 'list':
            return SubmissionListSerializer
        elif self.action == 'submit_exam':
            return SubmissionCreateSerializer
        return SubmissionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Students can only see their own submissions
        if self.request.user.role == 'student':
            queryset = queryset.filter(student=self.request.user)

        return queryset

    def get_permissions(self):
        if self.action in ['submit_exam']:
            return [IsStudent()]
        elif self.action in ['retrieve', 'list']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], permission_classes=[IsStudent])
    @transaction.atomic
    def submit_exam(self, request):
        '''Secure endpoint for students to submit exam answers.'''

        serializer = SubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exam_id = serializer.validated_data['exam']
        answers_data = serializer.validated_data['answers']

        try:
            exam = Exam.objects.get(id=exam_id, is_published=True)
        except Exam.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Exam not found or not published'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if exam is active
        if not exam.is_active():
            return Response(
                {'success': False, 'message': 'Exam is not currently active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if student is enrolled in the course
        if not exam.course.enrollments.filter(
                student=request.user,
                status='active'
        ).exists():
            return Response(
                {'success': False, 'message': 'You are not enrolled in this course'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if submission already exists
        if Submission.objects.filter(student=request.user, exam=exam).exists():
            return Response(
                {'success': False, 'message': 'You have already submitted this exam'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create submission
        submission = Submission.objects.create(
            student=request.user,
            exam=exam,
            status='submitted',
            submitted_at=timezone.now(),
            total_marks=exam.total_marks
        )

        # Create answers
        for answer_data in answers_data:
            try:
                question = Question.objects.get(
                    id=answer_data['question'],
                    exam=exam
                )
            except Question.DoesNotExist:
                transaction.set_rollback(True)
                return Response(
                    {'success': False, 'message': f"Invalid question ID: {answer_data['question']}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Answer.objects.create(
                submission=submission,
                question=question,
                answer_text=answer_data['answer_text'],
                marks_allocated=question.marks
            )

            # Trigger automated grading
            try:
                grading_service = GradingServiceFactory.get_service()
                grading_result = grading_service.grade_submission(submission)

                submission.status = 'graded'
                submission.is_graded = True
                submission.graded_at = timezone.now()
                submission.save()

            except Exception as e:
                # Log error but don't fail the submission
                print(f"Grading error: {str(e)}")

            return Response({
                'success': True,
                'message': 'Exam submitted successfully',
                'data': SubmissionSerializer(submission).data
            }, status=status.HTTP_201_CREATED)

        @action(detail=True, methods=['get'])
        def results(self, request, pk=None):
            '''Endpoint to retrieve submission results.'''

            submission = self.get_object()

            if not submission.is_graded:
                return Response(
                    {'success': False, 'message': 'Submission is not yet graded'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get grading result if available
            grading_result = None
            if hasattr(submission, 'grading_result'):
                grading_result = GradingResultSerializer(submission.grading_result).data

            return Response({
                'success': True,
                'data': {
                    'submission': SubmissionSerializer(submission).data,
                    'grading_result': grading_result
                }
            })