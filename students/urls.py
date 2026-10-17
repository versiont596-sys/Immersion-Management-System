from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('join-company/', views.join_company, name='join_company'),
    path('leave-company/', views.leave_company, name='leave_company'),
    path('tasks/', views.tasks_list, name='tasks'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('attendance/', views.attendance, name='attendance'),
    path('record-attendance/', views.record_attendance, name='record_attendance'),
    path('submit-excuse/', views.submit_excuse, name='submit_excuse'),
    path('journals/', views.journals, name='journals'),
    path('requirements/', views.requirements, name='requirements'),
    path('evaluation/', views.evaluation, name='evaluation'),
    path('announcements/', views.announcements_list, name='announcements'),
    path('notifications/', views.notifications_view, name='notifications'),
]
