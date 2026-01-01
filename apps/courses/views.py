from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Course, Enrollment
from .serializers import CourseSerializer, EnrollmentSerializer
from core.permissions import IsTeacher, IsStudent

class CourseViewSet(viewsets.ModelViewSet):
    '''ViewSet for Course CRUD operations.'''

    queryset = Course.objects.filter(is_active=True).select_related('created_by')
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('is_active',)
    search_fields = ('code', 'title', 'description')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacher()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def enroll(self, request, pk=None):
        '''Endpoint for students to enroll in a course.'''
        course = self.get_object()

        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'success': False, 'message': 'Already enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment = Enrollment.objects.create(student=request.user, course=course)

        return Response({
            'success': True,
            'message': 'Successfully enrolled in course',
            'data': EnrollmentSerializer(enrollment).data
        }, status=status.HTTP_201_CREATED)

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    '''ViewSet for viewing enrollments.'''

    serializer_class = EnrollmentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user

        qs = Enrollment.objects.select_related('course', 'student')

        if user.is_staff or user.is_superuser:
            return qs

        return qs.filter(student=user).select_related('course', 'student')
