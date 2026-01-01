from django.contrib import admin
from apps.exams.models import Exam, Question

# Register your models here.
admin.site.register(Exam)
admin.site.register(Question)