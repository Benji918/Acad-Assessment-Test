from rest_framework import serializers
from .models import Course, Enrollment
from apps.users.serializers import UserSerializer

class CourseSerializer(serializers.ModelSerializer):
    '''Serializer for Course model.'''

    created_by_details = UserSerializer(source='created_by', read_only=True)
    total_students = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('id', 'code', 'title', 'description', 'created_by', 'created_by_details',
                  'is_active', 'total_students', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_total_students(self, obj):
        return obj.enrollments.filter(status='active').count()

class EnrollmentSerializer(serializers.ModelSerializer):
    '''Serializer for Enrollment model.'''

    student_details = UserSerializer(source='student', read_only=True)
    course_details = CourseSerializer(source='course', read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'student', 'student_details', 'course', 'course_details',
                  'status', 'enrolled_at')
        read_only_fields = ('id', 'enrolled_at')

    def validate(self, attrs):
        student = attrs.get('student')
        course = attrs.get('course')

        qs = Enrollment.objects.filter(student=student, course=course)

        if self.instance:
            qs = qs.exclude(pk=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                "Student is already enrolled in this course."
            )

        return attrs