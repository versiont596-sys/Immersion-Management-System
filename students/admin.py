from django.contrib import admin
from .models import StudentProfile, StudentRequirement

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'strand', 'section', 'school_year')
    search_fields = ('user__first_name', 'user__last_name', 'student_id')
    list_filter = ('strand', 'school_year')

@admin.register(StudentRequirement)
class StudentRequirementAdmin(admin.ModelAdmin):
    list_display = ('student', 'requirement_type', 'status', 'uploaded_at')
    list_filter = ('requirement_type', 'status')
