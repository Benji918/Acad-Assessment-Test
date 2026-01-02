from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from apps.courses.models import Course, Enrollment
from apps.exams.models import Exam, Question
from apps.submissions.models import Submission, Answer

User = get_user_model()

class SubmissionTests(TestCase):
    '''Test suite for exam submissions.'''

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

        Enrollment.objects.create(student=self.student, course=self.course)

        now = timezone.now()
        self.exam = Exam.objects.create(
            course=self.course,
            title='Test Exam',
            duration_minutes=60,
            start_time=now - timedelta(minutes=30),
            end_time=now + timedelta(minutes=30),
            total_marks=20,
            is_published=True
        )

        self.question1 = Question.objects.create(
            exam=self.exam,
            question_text='What is polymorphism?',
            expected_answer='Polymorphism allows objects of different types to be treated uniformly.',
            keywords=['polymorphism', 'objects', 'types', 'uniformly'],
            marks=10,
        )

        self.question2 = Question.objects.create(
            exam=self.exam,
            question_text='Explain inheritance.',
            expected_answer='Inheritance allows a class to inherit properties from another class.',
            keywords=['inheritance', 'class', 'properties'],
            marks=10,
        )

        self.submit_url = '/api/v1/submissions/submit_exam/'

    def test_student_can_submit_exam(self):
        '''Test that students can submit exams.'''
        self.client.force_authenticate(user=self.student)

        submission_data = {
            'exam': self.exam.id,
            'answers': [
                {
                    'question_id': self.question1.id,
                    'answer_text': 'Polymorphism is when objects of different types can be treated uniformly through a common interface.'
                },
                {
                    'question_id': str(self.question2.id),
                    'answer_text': 'Inheritance is when a class inherits properties and methods from a parent class.'
                }
            ]
        }

        response = self.client.post(self.submit_url, submission_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(Submission.objects.count(), 1)

        submission = Submission.objects.first()
        self.assertEqual(submission.student, self.student)
        self.assertEqual(submission.answers.count(), 2)
        self.assertTrue(submission.is_graded)

    def test_duplicate_submission_prevented(self):
        '''Test that students cannot submit same exam twice.'''
        Submission.objects.create(
            student=self.student,
            exam=self.exam,
            status='submitted'
        )

        self.client.force_authenticate(user=self.student)

        submission_data = {
            'exam': str(self.exam.id),
            'answers': [
                {
                    'question': str(self.question1.id),
                    'answer_text': 'Test answer'
                }
            ]
        }

        response = self.client.post(self.submit_url, submission_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_can_only_view_own_submissions(self):
        '''Test that students can only see their own submissions.'''
        other_student = User.objects.create_user(
            email='other@example.com',
            username='other1',
            password='Pass123!',
            role='student'
        )

        # Create submissions for both students
        Submission.objects.create(student=self.student, exam=self.exam)
        Submission.objects.create(student=other_student, exam=self.exam)

        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/v1/submissions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['student'],
            self.student.id
        )