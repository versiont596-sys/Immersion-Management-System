from django.contrib import admin
from .models import Evaluation

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('student', 'supervisor', 'final_score', 'is_completed')
    list_filter = ('is_completed',)
