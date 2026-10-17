from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.contrib import messages
from .models import User


class RestrictedAdminSite(AdminSite):
    """Custom admin site that only allows 'admin' user access"""
    site_header = "ImmersionTrack Administration"
    site_title = "ImmersionTrack Admin"
    index_title = "System Administration"
    
    def has_permission(self, request):
        return request.user.username == 'admin' and request.user.is_superuser
    
    def index(self, request, extra_context=None):
        if not self.has_permission(request):
            messages.error(request, 'Admin access denied.')
            return redirect('/core/redirect/')
        return super().index(request, extra_context)


# Create a custom admin site instance
admin_site = RestrictedAdminSite(name='admin-restricted')


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_approved', 'is_active')
    list_filter = ('role', 'is_approved', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Status', {'fields': ('role', 'is_approved', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Status', {'fields': ('role', 'is_approved')}),
    )


admin_site.register(User, CustomUserAdmin)
