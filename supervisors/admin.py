from django.contrib import admin
from .models import SupervisorProfile

@admin.register(SupervisorProfile)
class SupervisorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'position')
    search_fields = ('user__first_name', 'user__last_name')
