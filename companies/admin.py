from django.contrib import admin
from .models import Company, ImmersionGroup, StudentCompanyAssignment

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry_type', 'required_hours', 'join_code', 'is_active')
    search_fields = ('name',)
    list_filter = ('industry_type', 'is_active')

@admin.register(ImmersionGroup)
class ImmersionGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'supervisor', 'school_year', 'is_open')
    list_filter = ('school_year', 'is_open')

@admin.register(StudentCompanyAssignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'status', 'joined_at')
    list_filter = ('status',)
