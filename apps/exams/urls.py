from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ExamViewSet, QuestionViewSet

router = DefaultRouter()
router.register(r'', ExamViewSet, basename='exam')
router.register(r'questions', QuestionViewSet, basename='question')

app_name = 'exams'

urlpatterns = [
    path('', include(router.urls)),
]