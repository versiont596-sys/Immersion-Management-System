from django.urls import path
from . import views

app_name = 'dean'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    # Students
    path('students/', views.students_list, name='students'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/<int:user_id>/approve/', views.approve_student, name='approve_student'),
    path('students/<int:user_id>/reject/', views.reject_student, name='reject_student'),
    path('students/<int:user_id>/delete/', views.student_delete, name='student_delete'),
    path('students/<int:student_id>/attendance-backup/', views.attendance_backup_download, name='attendance_backup'),
    path('students/<int:student_id>/attendance-delete/', views.delete_student_attendance_records, name='student_attendance_delete'),
    # Companies
    path('companies/', views.companies_list, name='companies'),
    path('companies/create/', views.company_create, name='company_create'),
    path('companies/<int:company_id>/', views.company_detail, name='company_detail'),
    path('companies/<int:company_id>/edit/', views.company_edit, name='company_edit'),
    path('companies/<int:company_id>/delete/', views.company_delete, name='company_delete'),
    # Supervisors
    path('supervisors/', views.supervisors_list, name='supervisors'),
    path('supervisors/create/', views.supervisor_create, name='supervisor_create'),
    path('supervisors/<int:supervisor_id>/edit/', views.supervisor_edit, name='supervisor_edit'),
    path('supervisors/<int:supervisor_id>/delete/', views.supervisor_delete, name='supervisor_delete'),
    path('supervisors/<int:supervisor_id>/remove-company/', views.supervisor_remove_company, name='supervisor_remove_company'),
    # Groups
    path('groups/', views.groups_list, name='groups'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/delete/', views.group_delete, name='group_delete'),
    path('leave-requests/', views.leave_requests, name='leave_requests'),
    path('leave-requests/<int:request_id>/approve/', views.approve_leave_request, name='approve_leave_request'),
    path('leave-requests/<int:request_id>/reject/', views.reject_leave_request, name='reject_leave_request'),
    # Monitoring
    path('attendance/', views.attendance_monitor, name='attendance'),
    path('evaluations/', views.evaluations_monitor, name='evaluations'),
    path('evaluations/<int:evaluation_id>/delete/', views.evaluation_delete, name='evaluation_delete'),
    # Announcements
    path('announcements/', views.announcements_list, name='announcements'),
    path('announcements/<int:announcement_id>/delete/', views.announcement_delete, name='announcement_delete'),
    # Reports
    path('reports/', views.reports, name='reports'),
    # Audit Logs
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('audit-logs/export/pdf/', views.export_audit_logs_pdf, name='export_audit_logs_pdf'),
    path('audit-logs/clear/', views.clear_audit_logs, name='clear_audit_logs'),
    # Settings
    path('settings/', views.settings_view, name='settings'),
]
