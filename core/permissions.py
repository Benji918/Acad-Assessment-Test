from rest_framework import permissions

class IsStudent(permissions.BasePermission):
    '''Permission class to check if user is a student.'''

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'student'

class IsTeacher(permissions.BasePermission):
    '''Permission class to check if user is a teacher.'''

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'teacher'

class IsOwnerOrReadOnly(permissions.BasePermission):
    '''Object-level permission to only allow owners to edit objects.'''

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.student == request.user

class IsEnrolledInCourse(permissions.BasePermission):
    '''Checks if student is enrolled in the course related to the exam.'''

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'exam'):
            course = obj.exam.course
        else:
            return False

        return course.enrollments.filter(student=request.user, status='active').exists()