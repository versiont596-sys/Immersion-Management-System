from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import HttpResponse
from django.urls import reverse
from django.core.files.base import ContentFile

from core.decorators import dean_required
from accounts.forms import SupervisorCreateForm
from students.models import StudentProfile, StudentRequirement, LeaveRequest
from companies.models import Company, ImmersionGroup, StudentCompanyAssignment
from supervisors.models import SupervisorProfile
from tasks.models import Task, TaskSubmission
from attendance.models import AttendanceRecord, AttendanceBackup
from journals.models import DailyJournal
from evaluations.models import Evaluation
from announcements.models import Announcement
from auditlogs.models import AuditLog, log_action
from notifications.models import Notification, create_notification

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import timedelta
import io

User = get_user_model()


@dean_required
def dashboard(request):
    total_students = StudentProfile.objects.count()
    total_supervisors = SupervisorProfile.objects.count()
    total_companies = Company.objects.filter(is_active=True).count()
    total_groups = ImmersionGroup.objects.count()
    pending_approvals = User.objects.filter(role='student', is_approved=False).count()

    all_tasks = Task.objects.count()
    all_submissions = TaskSubmission.objects.count()
    completion_rate = round((all_submissions / all_tasks * 100), 1) if all_tasks else 0

    recent_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:8]
    recent_students = User.objects.filter(role='student').order_by('-date_joined')[:5]

    companies_data = Company.objects.annotate(
        student_count=Count('groups__assignments', filter=Q(groups__assignments__status='active'))
    )[:5]

    context = {
        'total_students': total_students,
        'total_supervisors': total_supervisors,
        'total_companies': total_companies,
        'total_groups': total_groups,
        'pending_approvals': pending_approvals,
        'completion_rate': completion_rate,
        'recent_logs': recent_logs,
        'recent_students': recent_students,
        'companies_data': companies_data,
    }
    return render(request, 'dean/dashboard.html', context)


@dean_required
def leave_requests(request):
    requests = LeaveRequest.objects.select_related('student__user', 'group', 'reviewed_by').order_by('-submitted_at')
    return render(request, 'dean/leave_requests.html', {
        'requests': requests,
    })


@dean_required
def approve_leave_request(request, request_id):
    leave_request = get_object_or_404(LeaveRequest, id=request_id, status='pending')
    if request.method == 'POST':
        leave_request.status = 'approved'
        leave_request.reviewed_by = request.user
        leave_request.reviewed_at = timezone.now()
        leave_request.response_note = request.POST.get('response_note', '').strip()
        leave_request.save()
        assignment = leave_request.assignment
        if assignment and assignment.status == 'active':
            assignment.status = 'dropped'
            assignment.save()
            log_action(request.user, 'update', 'StudentCompanyAssignment', assignment.id, str(leave_request.student), f'Dean approved leave for group {assignment.group}', request)
        create_notification(
            leave_request.student.user,
            'Leave Request Approved',
            f'Your leave request for {leave_request.group.name} has been approved by the dean.',
            'general',
            reverse('students:dashboard')
        )
        messages.success(request, 'Leave request approved.')
    return redirect('dean:leave_requests')


@dean_required
def reject_leave_request(request, request_id):
    leave_request = get_object_or_404(LeaveRequest, id=request_id, status='pending')
    if request.method == 'POST':
        leave_request.status = 'rejected'
        leave_request.reviewed_by = request.user
        leave_request.reviewed_at = timezone.now()
        leave_request.response_note = request.POST.get('response_note', '').strip()
        leave_request.save()
        create_notification(
            leave_request.student.user,
            'Leave Request Declined',
            f'Your leave request for {leave_request.group.name} has been declined by the dean.',
            'general',
            reverse('students:dashboard')
        )
        messages.success(request, 'Leave request rejected.')
    return redirect('dean:leave_requests')


def _render_attendance_backup_pdf(student, records):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph('Attendance Backup Report', styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f'Student: {student.user.get_full_name()}', styles['Normal']))
    story.append(Paragraph(f'Student ID: {student.student_id}', styles['Normal']))
    story.append(Paragraph(f'Strand: {student.get_strand_display()}', styles['Normal']))
    story.append(Paragraph(f'Date Generated: {timezone.localtime().strftime("%B %d, %Y %I:%M %p")}', styles['Normal']))
    story.append(Spacer(1, 16))

    data = [['Date', 'Time In', 'Break Out', 'Break In', 'Time Out', 'Status', 'Hours']]
    for record in records.order_by('date'):
        data.append([
            record.date.strftime('%Y-%m-%d'),
            record.time_in.strftime('%I:%M %p') if record.time_in else '—',
            record.break_out.strftime('%I:%M %p') if record.break_out else '—',
            record.break_in.strftime('%I:%M %p') if record.break_in else '—',
            record.time_out.strftime('%I:%M %p') if record.time_out else '—',
            record.get_status_display(),
            f'{record.hours_rendered:.2f}' if record.hours_rendered else '0.00',
        ])

    table = Table(data, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()


def _record_backup_session(request, student_id, backup_id):
    request.session[f'attendance_backup_id_for_student_{student_id}'] = backup_id


# ─── STUDENT MANAGEMENT ───────────────────────────────────────────────────────

@dean_required
def students_list(request):
    students = StudentProfile.objects.select_related('user').order_by('-created_at')
    search = request.GET.get('q', '')
    strand = request.GET.get('strand', '')
    status = request.GET.get('status', '')

    if search:
        students = students.filter(
            user__first_name__icontains=search
        ) | students.filter(
            user__last_name__icontains=search
        ) | students.filter(student_id__icontains=search)
    if strand:
        students = students.filter(strand=strand)
    if status == 'approved':
        students = students.filter(user__is_approved=True)
    elif status == 'pending':
        students = students.filter(user__is_approved=False)

    return render(request, 'dean/students.html', {
        'students': students, 'search': search,
        'strand': strand, 'status': status,
        'strand_choices': StudentProfile.STRAND_CHOICES,
    })


@dean_required
def approve_student(request, user_id):
    user = get_object_or_404(User, id=user_id, role='student')
    user.is_approved = True
    user.save()
    log_action(request.user, 'approve', 'User', user.id, str(user), f'Approved student: {user.get_full_name()}', request)
    create_notification(user, 'Account Approved', 'Your immersion account has been approved. You can now log in!', 'approval')
    messages.success(request, f'{user.get_full_name()} approved successfully.')
    return redirect('dean:students')


@dean_required
def reject_student(request, user_id):
    user = get_object_or_404(User, id=user_id, role='student')
    user.is_approved = False
    user.is_active = False
    user.save()
    log_action(request.user, 'reject', 'User', user.id, str(user), f'Rejected student: {user.get_full_name()}', request)
    messages.warning(request, f'{user.get_full_name()} account rejected.')
    return redirect('dean:students')


@dean_required
def student_detail(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    assignment = student.get_active_assignment()
    submissions = TaskSubmission.objects.filter(student=student)
    attendance = AttendanceRecord.objects.filter(student=student)
    total_hours = sum(r.hours_rendered for r in attendance)
    evaluation = Evaluation.objects.filter(student=student).first()

    if request.method == 'POST' and 'assign_group' in request.POST:
        group_id = request.POST.get('group')
        group = get_object_or_404(ImmersionGroup, id=group_id)
        if not StudentCompanyAssignment.objects.filter(student=student, status='active').exists():
            StudentCompanyAssignment.objects.create(student=student, group=group, status='active')
            log_action(request.user, 'assign', 'StudentCompanyAssignment', student.id, str(student), f'Assigned to group {group}', request)
            messages.success(request, f'{student} assigned to {group}.')
        else:
            messages.error(request, 'Student already has an active assignment.')

    groups = ImmersionGroup.objects.filter(is_open=True)
    attendance_count = attendance.count()
    backup_session_key = f'attendance_backup_id_for_student_{student.id}'
    backup_id = request.session.get(backup_session_key)
    if backup_id and not AttendanceBackup.objects.filter(id=backup_id, student=student, created_by=request.user).exists():
        backup_id = None
        request.session.pop(backup_session_key, None)

    return render(request, 'dean/student_detail.html', {
        'student': student, 'assignment': assignment,
        'submissions': submissions, 'total_hours': total_hours,
        'evaluation': evaluation, 'groups': groups,
        'attendance_count': attendance_count,
        'attendance_backup_id': backup_id,
    })


@dean_required
def attendance_backup_download(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    attendance = AttendanceRecord.objects.filter(student=student)
    if not attendance.exists():
        messages.error(request, 'No attendance records found to back up.')
        return redirect('dean:student_detail', student_id=student.id)

    backup = AttendanceBackup.objects.create(student=student, created_by=request.user)
    pdf_bytes = _render_attendance_backup_pdf(student, attendance)
    file_name = f'attendance_backup_{student.student_id}_{backup.token}.pdf'
    backup.backup_file.save(file_name, ContentFile(pdf_bytes), save=False)
    backup.downloaded_at = timezone.now()
    backup.save()
    _record_backup_session(request, student.id, backup.id)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response


@dean_required
def delete_student_attendance_records(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    if request.method != 'POST':
        return redirect('dean:student_detail', student_id=student.id)

    backup_id = request.POST.get('backup_id')
    if not backup_id:
        messages.error(request, 'Please generate and download the attendance backup PDF before deleting records.')
        return redirect('dean:student_detail', student_id=student.id)

    backup = get_object_or_404(AttendanceBackup, id=backup_id, student=student, created_by=request.user)
    if not backup.downloaded_at:
        messages.error(request, 'Backup download must be completed before deleting attendance records.')
        return redirect('dean:student_detail', student_id=student.id)

    if timezone.now() - backup.downloaded_at > timedelta(hours=2):
        messages.error(request, 'The backup PDF is too old. Please generate a fresh backup before deleting records.')
        return redirect('dean:student_detail', student_id=student.id)

    AttendanceRecord.objects.filter(student=student).delete()
    request.session.pop(f'attendance_backup_id_for_student_{student.id}', None)
    log_action(request.user, 'delete', 'AttendanceRecord', student.id, str(student), 'Deleted all attendance records after backup.', request)
    messages.success(request, 'Attendance records deleted successfully after a secure PDF backup.')
    return redirect('dean:student_detail', student_id=student.id)


@dean_required
def announcement_delete(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    if request.method == 'POST':
        title = announcement.title
        announcement.delete()
        log_action(request.user, 'delete', 'Announcement', announcement_id, title, 'Deleted announcement from dean dashboard.', request)
        messages.success(request, 'Announcement deleted successfully.')
    return redirect('dean:announcements')


@dean_required
def evaluation_delete(request, evaluation_id):
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)
    if request.method == 'POST':
        details = f'{evaluation.student.user.get_full_name()} score {evaluation.final_score}'
        evaluation.delete()
        log_action(request.user, 'delete', 'Evaluation', evaluation_id, details, 'Deleted evaluation from dean dashboard.', request)
        messages.success(request, 'Evaluation deleted successfully.')
    return redirect('dean:evaluations')


# ─── COMPANY MANAGEMENT ──────────────────────────────────────────────────────

@dean_required
def companies_list(request):
    companies = Company.objects.annotate(
        group_count=Count('groups'),
    ).order_by('name')
    return render(request, 'dean/companies.html', {'companies': companies})


@dean_required
def company_create(request):
    from students.models import StudentProfile
    if request.method == 'POST':
        accepted_strands = request.POST.getlist('accepted_strands')
        if not accepted_strands:
            accepted_strands = [code for code, _ in StudentProfile.STRAND_CHOICES]
        company = Company.objects.create(
            name=request.POST.get('name'),
            address=request.POST.get('address'),
            contact_person=request.POST.get('contact_person'),
            contact_number=request.POST.get('contact_number'),
            email=request.POST.get('email'),
            industry_type=request.POST.get('industry_type', 'Other'),
            required_hours=request.POST.get('required_hours', 80),
            capacity=request.POST.get('capacity', 50),
            description=request.POST.get('description', ''),
            accepted_strands=accepted_strands,
        )
        log_action(request.user, 'create', 'Company', company.id, company.name, '', request)
        messages.success(request, f'Company "{company.name}" created successfully!')
        return redirect('dean:companies')
    return render(request, 'dean/company_form.html', {
        'company': None,
        'industry_choices': Company.INDUSTRY_CHOICES,
        'strand_choices': StudentProfile.STRAND_CHOICES,
    })


@dean_required
def company_edit(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        accepted_strands = request.POST.getlist('accepted_strands')
        if not accepted_strands:
            accepted_strands = [code for code, _ in StudentProfile.STRAND_CHOICES]
        company.name = request.POST.get('name')
        company.address = request.POST.get('address')
        company.contact_person = request.POST.get('contact_person')
        company.contact_number = request.POST.get('contact_number')
        company.email = request.POST.get('email')
        company.industry_type = request.POST.get('industry_type', 'Other')
        company.required_hours = request.POST.get('required_hours', 80)
        company.capacity = request.POST.get('capacity', 50)
        company.description = request.POST.get('description', '')
        company.accepted_strands = accepted_strands
        company.is_active = request.POST.get('is_active') == 'on'
        company.save()
        log_action(request.user, 'update', 'Company', company.id, company.name, '', request)
        messages.success(request, 'Company updated successfully!')
        return redirect('dean:companies')
    return render(request, 'dean/company_form.html', {
        'company': company,
        'industry_choices': Company.INDUSTRY_CHOICES,
        'strand_choices': StudentProfile.STRAND_CHOICES,
    })


@dean_required
def company_delete(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        company_name = company.name
        company.delete()
        log_action(request.user, 'delete', 'Company', company_id, company_name, '', request)
        messages.success(request, f'Company "{company_name}" deleted successfully.')
        return redirect('dean:companies')
    return redirect('dean:company_detail', company_id=company_id)


@dean_required
def company_detail(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    groups = company.groups.all()
    supervisors = company.supervisors.all()
    student_count = StudentCompanyAssignment.objects.filter(group__company=company, status='active').count()
    return render(request, 'dean/company_detail.html', {
        'company': company, 'groups': groups,
        'supervisors': supervisors, 'student_count': student_count,
    })


# ─── SUPERVISOR MANAGEMENT ───────────────────────────────────────────────────

@dean_required
def supervisors_list(request):
    supervisors = SupervisorProfile.objects.select_related('user', 'company').order_by('user__last_name')
    return render(request, 'dean/supervisors.html', {'supervisors': supervisors})


@dean_required
def supervisor_create(request):
    companies = Company.objects.filter(is_active=True)
    if request.method == 'POST':
        form = SupervisorCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            company_id = request.POST.get('company')
            company = Company.objects.filter(id=company_id).first()

            # Ensure we have a company, create default if none exist
            if not company and not Company.objects.filter(is_active=True).exists():
                company = Company.objects.create(
                    name='Default Company',
                    address='Default Address',
                    contact_person='Default Contact',
                    contact_email='default@company.com',
                    contact_number='0000000000',
                    is_active=True
                )

            # Create or update supervisor profile safely
            profile, created_profile = SupervisorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'company': company,
                    'position': request.POST.get('position', 'Supervisor'),
                    'contact_number': request.POST.get('contact_number', ''),
                    'strand': request.POST.get('strand') or None,
                }
            )

            if not created_profile:
                profile.company = company
                profile.position = request.POST.get('position', 'Supervisor')
                profile.contact_number = request.POST.get('contact_number', '')
                profile.strand = request.POST.get('strand') or None
                profile.save()

            log_action(request.user, 'create', 'SupervisorProfile', user.id, user.get_full_name(), f'Created supervisor account for {company}', request)
            messages.success(request, f'Supervisor account for {user.get_full_name()} created!')
            return redirect('dean:supervisors')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = SupervisorCreateForm()
    return render(request, 'dean/supervisor_form.html', {'form': form, 'companies': companies})


@dean_required
def supervisor_edit(request, supervisor_id):
    supervisor = get_object_or_404(SupervisorProfile, id=supervisor_id)
    companies = Company.objects.filter(is_active=True)
    if request.method == 'POST':
        supervisor.user.first_name = request.POST.get('first_name', supervisor.user.first_name)
        supervisor.user.last_name = request.POST.get('last_name', supervisor.user.last_name)
        supervisor.user.email = request.POST.get('email', supervisor.user.email)
        supervisor.user.is_active = request.POST.get('is_active') == 'on'
        supervisor.user.save()
        company_id = request.POST.get('company')
        supervisor.company = Company.objects.filter(id=company_id).first()
        supervisor.position = request.POST.get('position', '')
        supervisor.contact_number = request.POST.get('contact_number', '')
        supervisor.strand = request.POST.get('strand') or None
        supervisor.save()
        messages.success(request, 'Supervisor updated successfully!')
        return redirect('dean:supervisors')
    return render(request, 'dean/supervisor_edit.html', {
        'supervisor': supervisor,
        'companies': companies,
        'strand_choices': StudentProfile.STRAND_CHOICES,
    })


@dean_required
def supervisor_delete(request, supervisor_id):
    supervisor = get_object_or_404(SupervisorProfile, id=supervisor_id)
    if request.method == 'POST':
        user = supervisor.user
        username = user.username
        user_id = user.id
        user.delete()
        log_action(request.user, 'delete', 'User', user_id, username, f'Deleted supervisor account {username}', request)
        messages.success(request, f'Supervisor account "{username}" deleted successfully.')
        return redirect('dean:supervisors')
    return redirect('dean:supervisors')


@dean_required
def supervisor_remove_company(request, supervisor_id):
    supervisor = get_object_or_404(SupervisorProfile, id=supervisor_id)
    if request.method == 'POST':
        if supervisor.user.supervised_groups.exists():
            messages.error(request, 'Cannot remove company assignment while supervisor is still assigned to a group.')
            return redirect('dean:supervisor_edit', supervisor_id=supervisor_id)
        supervisor.company = None
        supervisor.save()
        messages.success(request, f'Company unassigned from supervisor {supervisor.user.get_full_name()}.')
    return redirect('dean:supervisors')


@dean_required
def student_delete(request, user_id):
    user = get_object_or_404(User, id=user_id, role='student')
    if request.method == 'POST':
        username = user.username
        user.delete()
        log_action(request.user, 'delete', 'User', user_id, username, f'Deleted student account {username}', request)
        messages.success(request, f'Student account "{username}" deleted successfully.')
        return redirect('dean:students')
    return redirect('dean:students')


# ─── IMMERSION GROUPS ────────────────────────────────────────────────────────

@dean_required
def groups_list(request):
    groups = ImmersionGroup.objects.select_related('company', 'supervisor').annotate(
        student_count=Count('assignments', filter=Q(assignments__status='active'))
    ).order_by('-created_at')
    return render(request, 'dean/groups.html', {'groups': groups})


@dean_required
def group_detail(request, group_id):
    group = get_object_or_404(ImmersionGroup.objects.select_related('company', 'supervisor'), id=group_id)
    students = StudentCompanyAssignment.objects.filter(group=group, status='active').select_related('student__user')
    return render(request, 'dean/group_detail.html', {
        'group': group,
        'students': students,
    })


@dean_required
def group_create(request):
    companies = Company.objects.filter(is_active=True)
    supervisors = SupervisorProfile.objects.select_related('user', 'company').annotate(
        group_count=Count('user__supervised_groups')
    ).filter(group_count=0)
    form_data = {}
    if request.method == 'POST':
        form_data = request.POST.copy()
        company = get_object_or_404(Company, id=request.POST.get('company'))
        supervisor_id = request.POST.get('supervisor')
        supervisor_user = User.objects.filter(id=supervisor_id, role='supervisor').first() if supervisor_id else None

        if supervisor_user:
            profile = SupervisorProfile.objects.filter(user=supervisor_user).select_related('company').first()
            if not profile or profile.company_id != company.id:
                messages.error(request, 'Selected supervisor must belong to the same company as the new group.')
                supervisor_user = None
            elif supervisor_user.supervised_groups.exists():
                messages.error(request, 'Selected supervisor already supervises another group.')
                supervisor_user = None

        if supervisor_id and not supervisor_user:
            messages.error(request, 'Selected supervisor is invalid, not available, or already assigned to another group.')
            return render(request, 'dean/group_form.html', {
                'companies': companies,
                'supervisors': supervisors,
                'group': None,
                'form_data': form_data,
            })

        group = ImmersionGroup.objects.create(
            company=company,
            supervisor=supervisor_user,
            name=request.POST.get('name'),
            school_year=request.POST.get('school_year', '2024-2025'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            is_open=request.POST.get('is_open') == 'on',
        )
        log_action(request.user, 'create', 'ImmersionGroup', group.id, group.name, '', request)
        messages.success(request, f'Group "{group.name}" created!')
        return redirect('dean:groups')
    return render(request, 'dean/group_form.html', {
        'companies': companies, 'supervisors': supervisors, 'group': None, 'form_data': form_data
    })


@dean_required
def group_delete(request, group_id):
    group = get_object_or_404(ImmersionGroup, id=group_id)
    if request.method == 'POST':
        group_name = group.name
        group.delete()
        log_action(request.user, 'delete', 'ImmersionGroup', group_id, group_name, '', request)
        messages.success(request, f'Immersion group "{group_name}" deleted successfully.')
        return redirect('dean:groups')
    return redirect('dean:groups')


# ─── ANNOUNCEMENTS ───────────────────────────────────────────────────────────

@dean_required
def announcements_list(request):
    announcements = Announcement.objects.select_related('posted_by', 'group').order_by('-created_at')
    groups = ImmersionGroup.objects.all()
    if request.method == 'POST':
        target_role = request.POST.get('target_role', 'all')
        group_id = request.POST.get('group')
        group = ImmersionGroup.objects.filter(id=group_id).first() if group_id else None
        if target_role == 'group':
            if not group:
                messages.error(request, 'Please select a specific group when posting a group announcement.')
                return redirect('dean:announcements')
        else:
            # Only group announcements should be scoped to a specific group.
            group = None
        ann = Announcement.objects.create(
            posted_by=request.user,
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            target_role=target_role,
            group=group,
            is_pinned=request.POST.get('is_pinned') == 'on',
            attachment=request.FILES.get('attachment'),
        )
        log_action(request.user, 'create', 'Announcement', ann.id, ann.title, '', request)
        messages.success(request, 'Announcement posted!')
        return redirect('dean:announcements')
    return render(request, 'dean/announcements.html', {
        'announcements': announcements, 'groups': groups,
        'target_choices': Announcement.TARGET_CHOICES,
    })


# ─── REPORTS & MONITORING ────────────────────────────────────────────────────

@dean_required
def reports(request):
    total_students = StudentProfile.objects.count()
    total_hours = AttendanceRecord.objects.aggregate(total=Sum('hours_rendered'))['total'] or 0
    completion_data = {
        'submitted': TaskSubmission.objects.count(),
        'graded': TaskSubmission.objects.filter(status='graded').count(),
        'pending': Task.objects.count() - TaskSubmission.objects.count(),
    }
    strand_data = StudentProfile.objects.values('strand').annotate(count=Count('id'))
    company_data = Company.objects.annotate(
        student_count=Count('groups__assignments')
    ).values('name', 'student_count')

    return render(request, 'dean/reports.html', {
        'total_students': total_students,
        'total_hours': total_hours,
        'completion_data': completion_data,
        'strand_data': list(strand_data),
        'company_data': list(company_data),
    })


@dean_required
def attendance_monitor(request):
    records = AttendanceRecord.objects.select_related(
        'student__user', 'group__company'
    ).order_by('-date')
    return render(request, 'dean/attendance_monitor.html', {'records': records[:200]})


@dean_required
def evaluations_monitor(request):
    evaluations = Evaluation.objects.select_related('student__user', 'supervisor').order_by('-created_at')
    return render(request, 'dean/evaluations_monitor.html', {'evaluations': evaluations})


# ─── AUDIT LOGS ──────────────────────────────────────────────────────────────

@dean_required
def audit_logs(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    return render(request, 'dean/audit_logs.html', {'logs': logs[:500]})


@dean_required
def export_audit_logs_pdf(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )
    styles = getSampleStyleSheet()
    elements = [
        Paragraph('Audit Trail Export', styles['Title']),
        Spacer(1, 12),
    ]

    table_data = [[
        'Timestamp',
        'User',
        'Action',
        'Model',
        'Details',
        'IP Address',
    ]]

    for log in logs:
        user_name = log.user.get_full_name() if log.user else 'System'
        action = log.get_action_display()
        details = f"{log.object_repr or ''} {log.details or ''}".strip()
        table_data.append([
            log.timestamp.strftime('%Y-%m-%d %H:%M'),
            user_name,
            action,
            log.model_name,
            details,
            log.ip_address or '—',
        ])

    table = Table(table_data, colWidths=[100, 100, 70, 90, 230, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.pdf"'
    return response


@dean_required
def clear_audit_logs(request):
    if request.method == 'POST':
        AuditLog.objects.all().delete()
        messages.success(request, 'Audit trail cleared successfully.')
    else:
        messages.error(request, 'Invalid request method for clearing audit logs.')
    return redirect('dean:audit_logs')


# ─── SETTINGS ────────────────────────────────────────────────────────────────

@dean_required
def settings_view(request):
    pending_students = User.objects.filter(role='student', is_approved=False).count()
    return render(request, 'dean/settings.html', {
        'pending_students': pending_students,
    })
