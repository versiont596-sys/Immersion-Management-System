from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic.base import RedirectView
from accounts.admin import admin_site

admin_site.site_header = "ImmersionTrack Administration"
admin_site.site_title = "ImmersionTrack Admin"
admin_site.index_title = "Welcome to ImmersionTrack"

urlpatterns = [
    path('admin/', admin_site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('core/', include('core.urls', namespace='core')),
    path('student/', include('students.urls', namespace='students')),
    path('students/', RedirectView.as_view(url='/student/', permanent=False)),
    path('students/<path:path>/', RedirectView.as_view(url='/student/%(path)s/', permanent=False)),
    path('supervisor/', include('supervisors.urls', namespace='supervisors')),
    path('dean/', include('dean.urls', namespace='dean')),
    path('', lambda request: redirect('accounts:login'), name='home'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'
