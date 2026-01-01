from django.contrib import admin
from apps.submissions.models import Submission, Answer


# Register your models here.
admin.site.register(Submission)
admin.site.register(Answer)