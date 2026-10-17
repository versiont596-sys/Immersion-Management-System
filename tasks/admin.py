from django.contrib import admin
from .models import Task, TaskSubmission

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'due_date', 'max_score', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('title',)

@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ('task', 'student', 'status', 'score', 'submitted_at')
    list_filter = ('status',)
