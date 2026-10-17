from django.urls import path
from . import views

app_name = 'supervisors'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('students/', views.students_list, name='students'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('companies/', views.companies_list, name='companies'),
    path('companies/create/', views.company_create, name='company_create'),
    path('companies/<int:company_id>/', views.company_detail, name='company_detail'),
    path('tasks/', views.tasks_list, name='tasks'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('submissions/', views.submissions_list, name='submissions'),
    path('submissions/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    path('attendance/', views.attendance_list, name='attendance'),
    path('attendance/excuses/', views.excuse_requests, name='excuse_requests'),
    path('attendance/excuses/<int:excuse_id>/approve/', views.approve_excuse, name='approve_excuse'),
    path('attendance/excuses/<int:excuse_id>/reject/', views.reject_excuse, name='reject_excuse'),
    path('attendance/<int:record_id>/approve/', views.approve_attendance, name='approve_attendance'),
    path('attendance/<int:record_id>/reject/', views.reject_attendance, name='reject_attendance'),
    path('attendance/<int:record_id>/delete/', views.attendance_delete, name='attendance_delete'),
    path('attendance/requirements/', views.requirements_list, name='requirements'),
    path('attendance/requirements/<int:requirement_id>/review/', views.review_requirement, name='review_requirement'),
    path('journals/', views.journals_list, name='journals'),
    path('journals/<int:journal_id>/review/', views.review_journal, name='review_journal'),
    path('evaluations/', views.evaluations_list, name='evaluations'),
    path('evaluations/<int:student_id>/', views.evaluate_student, name='evaluate_student'),
    path('announcements/', views.announcements_list, name='announcements'),
]
