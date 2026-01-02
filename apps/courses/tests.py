from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.courses.models import Course, Enrollment

User = get_user_model()

class CourseTests(TestCase):
    '''Test suite for course management.'''

    def setUp(self):
        self.client = APIClient()

        # Create teacher
        self.teacher = User.objects.create_user(
            email='teacher@gmail.com',
            username='teacher1',
            password='TeacherPass123!',
            first_name='Teacher',
            last_name='One',
            role='teacher'
        )

        # Create student
        self.student = User.objects.create_user(
            email='kodiugos@gmail.com',
            username='student1',
            password='StudentPass123!',
            first_name='Student',
            last_name='One',
            role='student'
        )

        self.course_url = '/api/v1/courses/courses/'

    def test_teacher_can_create_course(self):
        '''Test that teachers can create courses.'''
        self.client.force_authenticate(user=self.teacher)

        course_data = {
            'code': 'CS101',
            'title': 'Intro to CS',
            'description': 'Basic programming',
            'is_active': True
        }

        response = self.client.post(self.course_url, course_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Course.objects.first().code, 'CS101')

    def test_student_cannot_create_course(self):
        '''Test that students cannot create courses.'''
        self.client.force_authenticate(user=self.student)

        course_data = {
            'code': 'CS101',
            'title': 'Intro to CS',
            'description': 'Basic programming',
            'is_active': True
        }

        response = self.client.post(self.course_url, course_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_enroll_in_course(self):
        '''Test student enrollment in a course.'''
        # Create course as teacher
        course = Course.objects.create(
            code='CS101',
            title='Intro to CS',
            created_by=self.teacher,
            is_active=True
        )

        # Enroll as student
        self.client.force_authenticate(user=self.student)
        enroll_url = f'{self.course_url}{course.id}/enroll/'

        response = self.client.post(enroll_url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student,
                course=course
            ).exists()
        )

    def test_duplicate_enrollment_prevented(self):
        '''Test that students cannot enroll twice in same course.'''
        course = Course.objects.create(
            code='CS101',
            title='Intro to CS',
            created_by=self.teacher,
            is_active=True
        )

        # First enrollment
        Enrollment.objects.create(student=self.student, course=course)

        # Try to enroll again
        self.client.force_authenticate(user=self.student)
        enroll_url = f'{self.course_url}{course.id}/enroll/'

        response = self.client.post(enroll_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)