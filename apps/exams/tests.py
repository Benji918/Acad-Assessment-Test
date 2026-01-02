from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from apps.courses.models import Course, Enrollment
from apps.exams.models import Exam, Question

User = get_user_model()

class ExamTests(TestCase):
    '''Test suite for exam management.'''

    def setUp(self):
        self.client = APIClient()

        self.teacher = User.objects.create_user(
            email='teacher@example.com',
            username='teacher1',
            password='TeacherPass123!',
            role='teacher'
        )

        self.student = User.objects.create_user(
            email='student@example.com',
            username='student1',
            password='StudentPass123!',
            role='student'
        )

        self.course = Course.objects.create(
            code='CS101',
            title='Intro to CS',
            created_by=self.teacher,
            is_active=True
        )

        # Enroll student
        Enrollment.objects.create(student=self.student, course=self.course)

        self.exam_url = '/api/v1/exams/exams/'

    def test_teacher_can_create_exam(self):
        '''Test that teachers can create exams.'''
        self.client.force_authenticate(user=self.teacher)

        now = timezone.now()
        exam_data = {
            'course': str(self.course.id),
            'title': 'Midterm Exam',
            'description': 'Covers chapters 1-3',
            'duration_minutes': 60,
            'start_time': (now + timedelta(days=1)).isoformat(),
            'end_time': (now + timedelta(days=1, hours=2)).isoformat(),
            'total_marks': 100,
            'passing_marks': 50,
            'is_published': True
        }

        response = self.client.post(self.exam_url, exam_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Exam.objects.count(), 1)

    def test_student_can_view_published_exam(self):
        '''Test that students can view published exams.'''
        exam = Exam.objects.create(
            course=self.course,
            title='Test Exam',
            duration_minutes=60,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            is_published=True
        )

        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.exam_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_student_cannot_view_unpublished_exam(self):
        '''Test that students cannot view unpublished exams.'''
        exam = Exam.objects.create(
            course=self.course,
            title='Draft Exam',
            duration_minutes=60,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            is_published=False
        )

        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.exam_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)