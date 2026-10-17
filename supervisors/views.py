from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

from auditlogs.models import log_action
from core.decorators import supervisor_required
from supervisors.models import SupervisorProfile
from students.models import StudentProfile, StudentRequirement
from companies.models import Company, ImmersionGroup, StudentCompanyAssignment
from tasks.models import Task, TaskSubmission
from attendance.models import AttendanceRecord, ExcuseRequest
from journals.models import DailyJournal
from evaluations.models import Evaluation
from announcements.models import Announcement
from notifications.models import Notification, create_notification


@supervisor_required
def dashboard(request):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    groups = request.user.supervised_groups.all()
    students = supervisor.get_assigned_students()

    pending_submissions = TaskSubmission.objects.filter(
        task__group__in=groups, status='submitted'
    ).count()
    pending_journals = DailyJournal.objects.filter(
        student__in=students, status='pending'
    ).count()

    today = timezone.now().date()
    today_attendance = AttendanceRecord.objects.filter(
        group__in=groups, date=today
    ).count()
    active_sessions = AttendanceRecord.objects.filter(
        group__in=groups, time_in__isnull=False, time_out__isnull=True
    ).count()

    recent_submissions = TaskSubmission.objects.filter(
        task__group__in=groups
    ).order_by('-submitted_at')[:5]

    context = {
        'supervisor': supervisor,
        'total_students': students.count(),
        'pending_submissions': pending_submissions,
        'pending_journals': pending_journals,
        'today_attendance': today_attendance,
        'active_sessions': active_sessions,
        'recent_submissions': recent_submissions,
        'groups': groups,
    }
    return render(request, 'supervisors/dashboard.html', context)


@supervisor_required
def students_list(request):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    students = supervisor.get_assigned_students().select_related('user')
    search = request.GET.get('q', '')
    strand = request.GET.get('strand', '')
    if search:
        students = students.filter(
            user__first_name__icontains=search
        ) | students.filter(
            user__last_name__icontains=search
        ) | students.filter(student_id__icontains=search)
    if strand:
        students = students.filter(strand=strand)
    return render(request, 'supervisors/students.html', {
        'students': students, 'search': search,
        'strand': strand,
        'strand_choices': StudentProfile.STRAND_CHOICES,
    })


@supervisor_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'supervisors/notifications.html', {
        'notifications': notifications,
    })


@supervisor_required
def companies_list(request):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    if supervisor.company:
        companies = Company.objects.filter(id=supervisor.company.id, is_active=True)
    else:
        companies = Company.objects.none()
    return render(request, 'supervisors/companies.html', {
        'companies': companies,
    })


@supervisor_required
def company_detail(request, company_id):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    company = get_object_or_404(Company, id=company_id)
    if not supervisor.company or company.id != supervisor.company.id:
        raise Http404('Company not found.')
    groups = company.groups.filter(supervisor=request.user).select_related('supervisor').order_by('name')
    supervisors = [request.user]
    handled_students = StudentProfile.objects.filter(
        assignments__group__company=company,
        assignments__group__supervisor=request.user,
        assignments__status='active'
    ).distinct().select_related('user')

    return render(request, 'supervisors/company_detail.html', {
        'company': company,
        'groups': groups,
        'supervisors': supervisors,
        'student_count': company.get_student_count(),
        'handled_students': handled_students,
    })


@supervisor_required
def company_create(request):
    messages.error(request, 'Only the Dean may add new companies.')
    return redirect('supervisors:companies')


@supervisor_required
def student_detail(request, student_id):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    student = get_object_or_404(StudentProfile, id=student_id)
    groups = request.user.supervised_groups.all()

    # Security: only show students supervised by this supervisor either directly or via group assignments
    if not (student.supervisor == supervisor or StudentCompanyAssignment.objects.filter(
        student=student,
        group__in=groups
    ).exists()):
        messages.error(request, 'Access denied.')
        return redirect('supervisors:students')

    submissions = TaskSubmission.objects.filter(student=student, task__group__in=groups)
    attendance = AttendanceRecord.objects.filter(student=student, group__in=groups).order_by('-date')
    journals = DailyJournal.objects.filter(student=student).order_by('-date')
    total_hours = sum(r.hours_rendered for r in attendance)

    return render(request, 'supervisors/student_detail.html', {
        'student': student,
        'submissions': submissions,
        'attendance': attendance,
        'journals': journals,
        'total_hours': total_hours,
    })


@supervisor_required
def tasks_list(request):
    groups = request.user.supervised_groups.all()
    tasks = Task.objects.filter(group__in=groups).order_by('-created_at')
    return render(request, 'supervisors/tasks.html', {'tasks': tasks, 'groups': groups})


@supervisor_required
def task_create(request):
    groups = request.user.supervised_groups.all()
    if request.method == 'POST':
        group_id = request.POST.get('group')
        group = get_object_or_404(ImmersionGroup, id=group_id, supervisor=request.user)
        task = Task.objects.create(
            group=group,
            created_by=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            instructions=request.POST.get('instructions', ''),
            due_date=request.POST.get('due_date'),
            max_score=request.POST.get('max_score', 100),
            attachment=request.FILES.get('attachment'),
            is_published=request.POST.get('is_published') == 'on',
        )
        # Notify students
        assignments = StudentCompanyAssignment.objects.filter(group=group, status='active')
        for a in assignments:
            create_notification(
                a.student.user,
                f'New Task: {task.title}',
                f'A new task has been posted in {group.name}. Due: {task.due_date}',
                'task',
                reverse('students:task_detail', args=[task.id])
            )
        messages.success(request, 'Task created successfully!')
        return redirect('supervisors:tasks')
    return render(request, 'supervisors/task_form.html', {'groups': groups, 'task': None})


@supervisor_required
def task_edit(request, task_id):
    groups = request.user.supervised_groups.all()
    task = get_object_or_404(Task, id=task_id, group__in=groups)
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        task.instructions = request.POST.get('instructions', '')
        task.due_date = request.POST.get('due_date')
        task.max_score = request.POST.get('max_score', 100)
        task.is_published = request.POST.get('is_published') == 'on'
        if request.FILES.get('attachment'):
            task.attachment = request.FILES['attachment']
        task.save()
        messages.success(request, 'Task updated successfully!')
        return redirect('supervisors:tasks')
    return render(request, 'supervisors/task_form.html', {'task': task, 'groups': groups})


@supervisor_required
def task_delete(request, task_id):
    groups = request.user.supervised_groups.all()
    task = get_object_or_404(Task, id=task_id, group__in=groups)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
    return redirect('supervisors:tasks')


@supervisor_required
def submissions_list(request):
    groups = request.user.supervised_groups.all()
    submissions = TaskSubmission.objects.filter(
        task__group__in=groups
    ).select_related('student__user', 'task').order_by('-submitted_at')
    filter_status = request.GET.get('status', 'all')
    if filter_status != 'all':
        submissions = submissions.filter(status=filter_status)
    return render(request, 'supervisors/submissions.html', {
        'submissions': submissions, 'filter_status': filter_status
    })


@supervisor_required
def grade_submission(request, submission_id):
    groups = request.user.supervised_groups.all()
    submission = get_object_or_404(TaskSubmission, id=submission_id, task__group__in=groups)
    if request.method == 'POST':
        score_text = request.POST.get('score', '').strip()
        status = request.POST.get('status', 'graded')

        if score_text == '':
            if status == 'graded':
                messages.error(request, 'Please enter a numeric score before saving as graded.')
                return render(request, 'supervisors/grade_submission.html', {'submission': submission})
            submission.score = None
        else:
            try:
                score_value = int(score_text)
            except ValueError:
                messages.error(request, 'Score must be a whole number.')
                return render(request, 'supervisors/grade_submission.html', {'submission': submission})

            if score_value < 0 or score_value > submission.task.max_score:
                messages.error(request, f'Score must be between 0 and {submission.task.max_score}.')
                return render(request, 'supervisors/grade_submission.html', {'submission': submission})

            submission.score = score_value

        submission.feedback = request.POST.get('feedback', '')
        submission.status = status
        submission.reviewed_by = request.user
        submission.reviewed_at = timezone.now()
        submission.save()
        create_notification(
            submission.student.user,
            f'Submission Graded: {submission.task.title}',
            f'Your submission has been graded. Score: {submission.score}/{submission.task.max_score}',
            'submission',
            reverse('students:task_detail', args=[submission.task.id])
        )
        messages.success(request, 'Submission graded successfully!')
        return redirect('supervisors:submissions')
    return render(request, 'supervisors/grade_submission.html', {'submission': submission})


@supervisor_required
def attendance_list(request):
    groups = request.user.supervised_groups.all()
    selected_group = request.GET.get('group')
    selected_date = request.GET.get('date', timezone.now().date())
    selected_status = request.GET.get('status', 'all')

    records = AttendanceRecord.objects.filter(group__in=groups)
    if selected_group:
        records = records.filter(group_id=selected_group)
    if selected_date:
        records = records.filter(date=selected_date)
    if selected_status and selected_status != 'all':
        records = records.filter(status=selected_status)

    return render(request, 'supervisors/attendance.html', {
        'records': records.order_by('-date'),
        'groups': groups,
        'selected_date': selected_date,
        'selected_status': selected_status,
        'active_sessions': records.filter(time_in__isnull=False, time_out__isnull=True).count(),
    })


@supervisor_required
def approve_attendance(request, record_id):
    groups = request.user.supervised_groups.all()
    record = get_object_or_404(AttendanceRecord, id=record_id, group__in=groups)
    if request.method == 'POST':
        record.approval_status = 'approved'
        record.approved_by = request.user
        record.approved_at = timezone.now()
        record.save()
        log_action(
            request.user,
            'approve',
            'AttendanceRecord',
            object_id=record.id,
            object_repr=str(record),
            details=f'Approved attendance for {record.student.user.get_full_name()} on {record.date}',
            request=request,
        )
        create_notification(
            record.student.user,
            'Attendance Approved',
            f'Your attendance for {record.date} has been approved.',
            'attendance',
            reverse('students:attendance')
        )
        messages.success(request, 'Attendance approved successfully.')
    return redirect('supervisors:attendance')


@supervisor_required
def reject_attendance(request, record_id):
    groups = request.user.supervised_groups.all()
    record = get_object_or_404(AttendanceRecord, id=record_id, group__in=groups)
    if request.method == 'POST':
        record.approval_status = 'rejected'
        record.approved_by = request.user
        record.approved_at = timezone.now()
        record.save()
        log_action(
            request.user,
            'reject',
            'AttendanceRecord',
            object_id=record.id,
            object_repr=str(record),
            details=f'Rejected attendance for {record.student.user.get_full_name()} on {record.date}',
            request=request,
        )
        create_notification(
            record.student.user,
            'Attendance Rejected',
            f'Your attendance for {record.date} was rejected. Please contact your supervisor.',
            'attendance',
            reverse('students:attendance')
        )
        messages.success(request, 'Attendance rejected successfully.')
    return redirect('supervisors:attendance')


@supervisor_required
def excuse_requests(request):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    requests = ExcuseRequest.objects.filter(
        Q(supervisor=request.user) |
        Q(student__assignments__group__supervisor=request.user)
    ).distinct().order_by('-submitted_at')
    return render(request, 'supervisors/excuse_requests.html', {
        'requests': requests,
    })


@supervisor_required
def approve_excuse(request, excuse_id):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    excuse = get_object_or_404(
        ExcuseRequest,
        Q(supervisor=request.user) | Q(student__assignments__group__supervisor=request.user),
        id=excuse_id,
    )
    if request.method == 'POST':
        excuse.status = 'approved'
        excuse.reviewed_by = request.user
        excuse.reviewed_at = timezone.now()
        excuse.supervisor_comment = request.POST.get('comment', '').strip()
        excuse.save()

        assignment = excuse.student.get_active_assignment()
        group = assignment.group if assignment else None
        if not group:
            fallback_assignment = StudentCompanyAssignment.objects.filter(student=excuse.student).order_by('-id').first()
            group = fallback_assignment.group if fallback_assignment else None

        if group:
            record, created = AttendanceRecord.objects.get_or_create(
                student=excuse.student,
                group=group,
                date=excuse.date,
                defaults={
                    'status': 'excused',
                    'approval_status': 'approved',
                    'approved_by': request.user,
                    'approved_at': timezone.now(),
                    'verified_by': request.user,
                    'remarks': excuse.reason or excuse.supervisor_comment,
                    'hours_rendered': 0,
                }
            )
            if not created:
                record.status = 'excused'
                record.approval_status = 'approved'
                record.approved_by = request.user
                record.approved_at = timezone.now()
                record.verified_by = request.user
                record.remarks = excuse.reason or excuse.supervisor_comment
                record.time_in = None
                record.break_out = None
                record.break_in = None
                record.time_out = None
                record.hours_rendered = 0
                record.save()

        create_notification(
            excuse.student.user,
            'Excuse Approved',
            f'Your excuse for {excuse.date} has been approved. See supervisor feedback in your excuse history.',
            'attendance',
            reverse('students:submit_excuse')
        )

        log_action(
            request.user,
            'approve',
            'ExcuseRequest',
            object_id=excuse.id,
            object_repr=str(excuse),
            details=f'Approved excuse request for {excuse.student.user.get_full_name()} on {excuse.date}',
            request=request,
        )
        messages.success(request, 'Excuse request approved and attendance updated.')
    return redirect('supervisors:excuse_requests')


@supervisor_required
def reject_excuse(request, excuse_id):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    excuse = get_object_or_404(
        ExcuseRequest,
        Q(supervisor=request.user) | Q(student__assignments__group__supervisor=request.user),
        id=excuse_id,
    )
    if request.method == 'POST':
        excuse.status = 'rejected'
        excuse.reviewed_by = request.user
        excuse.reviewed_at = timezone.now()
        excuse.supervisor_comment = request.POST.get('comment', '').strip()
        excuse.save()

        assignment = excuse.student.get_active_assignment()
        group = assignment.group if assignment else None
        if not group:
            fallback_assignment = StudentCompanyAssignment.objects.filter(student=excuse.student).order_by('-id').first()
            group = fallback_assignment.group if fallback_assignment else None

        if group:
            record, created = AttendanceRecord.objects.get_or_create(
                student=excuse.student,
                group=group,
                date=excuse.date,
                defaults={
                    'status': 'absent',
                    'approval_status': 'rejected',
                    'approved_by': request.user,
                    'approved_at': timezone.now(),
                    'verified_by': request.user,
                }
            )
            if not created:
                record.status = 'absent'
                record.approval_status = 'rejected'
                record.approved_by = request.user
                record.approved_at = timezone.now()
                record.verified_by = request.user
                if not record.time_in and not record.time_out:
                    record.hours_rendered = 0
                record.save()

        create_notification(
            excuse.student.user,
            'Excuse Rejected',
            f'Your excuse for {excuse.date} has been rejected. See supervisor feedback in your excuse history.',
            'attendance',
            reverse('students:submit_excuse')
        )

        log_action(
            request.user,
            'reject',
            'ExcuseRequest',
            object_id=excuse.id,
            object_repr=str(excuse),
            details=f'Rejected excuse request for {excuse.student.user.get_full_name()} on {excuse.date}',
            request=request,
        )
        messages.success(request, 'Excuse request rejected and absence recorded.')
    return redirect('supervisors:excuse_requests')


@supervisor_required
def requirements_list(request):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    requirements = StudentRequirement.objects.filter(
        Q(student__supervisor=supervisor) | Q(student__assignments__group__supervisor=request.user)
    ).distinct().order_by('-uploaded_at')
    return render(request, 'supervisors/requirements.html', {
        'requirements': requirements,
    })


@supervisor_required
def review_requirement(request, requirement_id):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    requirement = get_object_or_404(
        StudentRequirement.objects.filter(
            Q(student__supervisor=supervisor) | Q(student__assignments__group__supervisor=request.user)
        ),
        id=requirement_id
    )
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['approved', 'rejected']:
            requirement.status = status
        requirement.supervisor_comment = request.POST.get('supervisor_comment', '').strip()
        requirement.reviewed_by = request.user
        requirement.reviewed_at = timezone.now()
        requirement.save()

        create_notification(
            requirement.student.user,
            'Requirement Reviewed',
            f'Your {requirement.get_requirement_type_display()} has been {requirement.get_status_display()}.',
            'requirement',
            reverse('students:requirements')
        )
        messages.success(request, 'Requirement review submitted successfully.')
        return redirect('supervisors:requirements')

    return render(request, 'supervisors/review_requirement.html', {
        'requirement': requirement,
    })


@supervisor_required
def attendance_delete(request, record_id):
    groups = request.user.supervised_groups.all()
    record = get_object_or_404(AttendanceRecord, id=record_id, group__in=groups)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Attendance record deleted successfully!')
    return redirect('supervisors:attendance')


@supervisor_required
def journals_list(request):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    students = supervisor.get_assigned_students()
    journals = DailyJournal.objects.filter(student__in=students).order_by('-date')
    filter_status = request.GET.get('status', 'all')
    if filter_status != 'all':
        journals = journals.filter(status=filter_status)
    return render(request, 'supervisors/journals.html', {
        'journals': journals, 'filter_status': filter_status
    })


@supervisor_required
def review_journal(request, journal_id):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    students = supervisor.get_assigned_students()
    journal = get_object_or_404(DailyJournal, id=journal_id, student__in=students)
    if request.method == 'POST':
        journal.status = request.POST.get('status', 'approved')
        journal.supervisor_remarks = request.POST.get('remarks', '')
        journal.reviewed_by = request.user
        journal.reviewed_at = timezone.now()
        journal.save()
        messages.success(request, f'Journal {journal.get_status_display()}.')
        return redirect('supervisors:journals')
    return render(request, 'supervisors/review_journal.html', {'journal': journal})


@supervisor_required
def evaluations_list(request):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    students = supervisor.get_assigned_students()
    evaluations = Evaluation.objects.filter(supervisor=request.user)
    return render(request, 'supervisors/evaluations.html', {
        'students': students, 'evaluations': evaluations
    })


@supervisor_required
def evaluate_student(request, student_id):
    supervisor = get_object_or_404(SupervisorProfile, user=request.user)
    students = supervisor.get_assigned_students()
    student = get_object_or_404(StudentProfile, id=student_id)

    if student not in students:
        messages.error(request, 'Access denied.')
        return redirect('supervisors:evaluations')

    evaluation, _ = Evaluation.objects.get_or_create(student=student, supervisor=request.user)

    if request.method == 'POST':
        evaluation.punctuality = int(request.POST.get('punctuality', 0))
        evaluation.attendance = int(request.POST.get('attendance', 0))
        evaluation.work_quality = int(request.POST.get('work_quality', 0))
        evaluation.professionalism = int(request.POST.get('professionalism', 0))
        evaluation.communication = int(request.POST.get('communication', 0))
        evaluation.teamwork = int(request.POST.get('teamwork', 0))
        evaluation.initiative = int(request.POST.get('initiative', 0))
        evaluation.remarks = request.POST.get('remarks', '')
        evaluation.recommendation = request.POST.get('recommendation', '')
        evaluation.is_completed = request.POST.get('is_completed') == 'on'
        evaluation.compute_final_score()
        evaluation.save()
        create_notification(
            student.user,
            'Evaluation Updated',
            f'Your immersion evaluation has been updated. Final Score: {evaluation.final_score}',
            'evaluation',
            reverse('students:evaluation')
        )
        messages.success(request, 'Evaluation saved successfully!')
        return redirect('supervisors:evaluations')

    return render(request, 'supervisors/evaluate_student.html', {
        'student': student,
        'evaluation': evaluation,
        'criteria_fields': [
            ('punctuality', 'Punctuality'),
            ('attendance', 'Attendance'),
            ('work_quality', 'Work Quality'),
            ('professionalism', 'Professionalism'),
            ('communication', 'Communication'),
            ('teamwork', 'Teamwork'),
            ('initiative', 'Initiative'),
        ],
    })


@supervisor_required
def announcements_list(request):
    groups = request.user.supervised_groups.all()
    announcements = Announcement.objects.filter(posted_by=request.user).select_related('group').order_by('-created_at')
    if request.method == 'POST':
        group_id = request.POST.get('group')
        group = get_object_or_404(ImmersionGroup, id=group_id, supervisor=request.user) if group_id else None
        target_role = 'group' if group else 'students'
        ann = Announcement.objects.create(
            posted_by=request.user,
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            target_role=target_role,
            group=group,
            attachment=request.FILES.get('attachment'),
        )

        # Notify students in the selected group or all supervised students
        if group:
            student_users = [a.student.user for a in StudentCompanyAssignment.objects.filter(group=group, status='active').select_related('student__user')]
            message = f'New announcement for {group.name}. Check your announcements.'
        else:
            student_users = [
                assignment.student.user
                for assignment in StudentCompanyAssignment.objects.filter(group__in=groups, status='active').select_related('student__user')
            ]
            message = 'New announcement from your supervisor. Check your announcements.'

        for user in set(student_users):
            create_notification(
                user,
                'New Supervisor Announcement',
                message,
                'announcement',
                reverse('students:announcements')
            )

        messages.success(request, 'Announcement posted!')
        return redirect('supervisors:announcements')
    return render(request, 'supervisors/announcements.html', {
        'announcements': announcements, 'groups': groups
    })
