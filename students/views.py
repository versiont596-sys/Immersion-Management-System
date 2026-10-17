import json
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from auditlogs.models import log_action
from core.decorators import student_required
from students.models import StudentProfile, StudentRequirement, LeaveRequest
from companies.models import Company, ImmersionGroup, StudentCompanyAssignment
from supervisors.models import SupervisorProfile
from tasks.models import Task, TaskSubmission
from accounts.models import User
from attendance.models import AttendanceRecord, ExcuseRequest
from journals.models import DailyJournal
from announcements.models import Announcement
from evaluations.models import Evaluation
from notifications.models import Notification, create_notification


@student_required
def dashboard(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")
    assignment = student.get_active_assignment()
    group = assignment.group if assignment else None

    # Stats
    tasks = Task.objects.filter(group=group) if group else Task.objects.none()
    submissions = TaskSubmission.objects.filter(student=student)
    submitted_ids = submissions.values_list('task_id', flat=True)
    pending_tasks = tasks.exclude(id__in=submitted_ids).filter(is_published=True)
    overdue_tasks = pending_tasks.filter(due_date__lt=timezone.now())

    attendance_records = AttendanceRecord.objects.filter(student=student)
    total_hours = sum(r.hours_rendered for r in attendance_records)
    required_hours = group.company.required_hours if group else 80
    progress_pct = min(int((float(total_hours) / required_hours) * 100), 100) if required_hours else 0
    pending_excuse_count = ExcuseRequest.objects.filter(student=student, status='pending').count()

    # Build announcements queryset without .union() to allow .order_by()
    ann_qs = Announcement.objects.filter(target_role='all') | Announcement.objects.filter(
        target_role='students',
        group__isnull=True
    )
    if group:
        ann_qs = ann_qs | Announcement.objects.filter(
            group=group,
            target_role='group'
        )
    else:
        # Show group announcements to students who are not yet assigned to any group,
        # so they can see join-code related notices and enroll in the immersion program.
        ann_qs = ann_qs | Announcement.objects.filter(
            target_role='group'
        )
    announcements = ann_qs.order_by('-created_at')[:5]

    journals_pending = DailyJournal.objects.filter(student=student, status='pending').count()

    context = {
        'student': student,
        'assignment': assignment,
        'group': group,
        'total_tasks': tasks.count(),
        'pending_tasks_count': pending_tasks.count(),
        'submitted_count': submissions.count(),
        'overdue_count': overdue_tasks.count(),
        'total_hours': total_hours,
        'required_hours': required_hours,
        'progress_pct': progress_pct,
        'pending_excuse_count': pending_excuse_count,
        'announcements': announcements,
        'journals_pending': journals_pending,
        'upcoming_tasks': pending_tasks.order_by('due_date')[:3],
    }
    return render(request, 'students/dashboard.html', context)


@student_required
def profile(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")

    missing_fields = []
    if not student.student_id:
        missing_fields.append('LRN')
    if not student.section:
        missing_fields.append('Section')
    if missing_fields:
        messages.warning(
            request,
            f"Your student profile is missing required information: {', '.join(missing_fields)}. Please contact the administrator to complete your record."
        )

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.email = request.POST.get('email', user.email)
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        user.save()

        student.contact_number = request.POST.get('contact_number', student.contact_number)
        student.address = request.POST.get('address', student.address)
        student.guardian_name = request.POST.get('guardian_name', student.guardian_name)
        student.guardian_contact = request.POST.get('guardian_contact', student.guardian_contact)
        student.emergency_contact = request.POST.get('emergency_contact', student.emergency_contact)
        student.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('students:profile')

    return render(request, 'students/profile.html', {'student': student})


@student_required
def join_company(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")
    existing = StudentCompanyAssignment.objects.filter(student=student, status='active').first()

    if request.method == 'POST':
        code = request.POST.get('join_code', '').strip().upper()
        try:
            company = Company.objects.get(join_code=code, is_active=True)
            group = company.groups.filter(is_open=True).first()
            if not group:
                messages.error(request, 'No active immersion group for this company.')
            elif existing:
                messages.error(request, 'You are already in an active immersion group.')
            elif not company.accepts_strand(student.strand):
                messages.error(request, 'Your strand is not accepted by this company.')
            else:
                previous_assignment = StudentCompanyAssignment.objects.filter(student=student, group=group).first()
                if previous_assignment:
                    previous_assignment.status = 'active'
                    previous_assignment.joined_via_code = True
                    previous_assignment.joined_at = timezone.now()
                    previous_assignment.save()
                    log_action(request.user, 'update', 'StudentCompanyAssignment', previous_assignment.id, str(student), f'Reactivated assignment for group {group}', request)
                else:
                    StudentCompanyAssignment.objects.create(
                        student=student,
                        group=group,
                        status='active',
                        joined_via_code=True,
                    )
                messages.success(request, f'Successfully joined {company.name}!')
                return redirect('students:dashboard')
        except Company.DoesNotExist:
            messages.error(request, 'Invalid join code. Please check and try again.')

    return render(request, 'students/join_company.html', {
        'student': student,
        'existing': existing,
    })


@student_required
def leave_company(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")

    assignment = StudentCompanyAssignment.objects.filter(student=student, status='active').first()
    if not assignment:
        messages.warning(request, 'You do not have an active immersion group to leave.')
        return redirect('students:join_company')

    pending_request = LeaveRequest.objects.filter(student=student, status='pending').first()
    if request.method == 'POST':
        if pending_request:
            messages.warning(request, 'You already have a pending leave request. Please wait for your supervisor to respond.')
            return redirect('students:dashboard')

        reason = request.POST.get('reason', '').strip()
        leave_request = LeaveRequest.objects.create(
            student=student,
            assignment=assignment,
            group=assignment.group,
            reason=reason,
            status='pending'
        )
        log_action(request.user, 'create', 'LeaveRequest', leave_request.id, str(student), f'Submitted leave request for group {assignment.group}', request)

        deans = User.objects.filter(role='dean', is_active=True)
        for dean in deans:
            create_notification(
                dean,
                'Leave Request Submitted',
                f'{student.user.get_full_name()} requested to leave {assignment.group.name}.',
                'approval',
                reverse('dean:leave_requests')
            )

        messages.success(request, 'Leave request submitted. The dean will review it shortly.')
        return redirect('students:dashboard')

    return render(request, 'students/leave_company.html', {
        'assignment': assignment,
        'pending_request': pending_request,
    })


@student_required
def tasks_list(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")
    assignment = student.get_active_assignment()
    group = assignment.group if assignment else None

    tasks = Task.objects.filter(group=group, is_published=True) if group else Task.objects.none()
    submissions = TaskSubmission.objects.filter(student=student)
    submission_map = {s.task_id: s for s in submissions}

    filter_status = request.GET.get('status', 'all')
    task_data = []
    for task in tasks:
        sub = submission_map.get(task.id)
        status = 'not_submitted'
        if sub:
            status = sub.status
        elif task.is_overdue():
            status = 'overdue'
        task_data.append({'task': task, 'submission': sub, 'status': status})

    if filter_status == 'pending':
        task_data = [t for t in task_data if t['status'] == 'not_submitted']
    elif filter_status == 'submitted':
        task_data = [t for t in task_data if t['status'] in ('submitted', 'late')]
    elif filter_status == 'graded':
        task_data = [t for t in task_data if t['status'] == 'graded']
    elif filter_status == 'overdue':
        task_data = [t for t in task_data if t['status'] == 'overdue']

    return render(request, 'students/tasks.html', {
        'task_data': task_data,
        'filter_status': filter_status,
    })


@student_required
def task_detail(request, task_id):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")
    task = get_object_or_404(Task, id=task_id)
    submission = TaskSubmission.objects.filter(task=task, student=student).first()

    if request.method == 'POST' and not submission:
        file = request.FILES.get('file')
        comment = request.POST.get('comment', '')
        if file:
            status = 'late' if task.is_overdue() else 'submitted'
            TaskSubmission.objects.create(
                task=task, student=student,
                file=file, comment=comment, status=status
            )
            messages.success(request, 'Task submitted successfully!')
            return redirect('students:tasks')
        else:
            messages.error(request, 'Please attach a file to submit.')

    return render(request, 'students/task_detail.html', {
        'task': task,
        'submission': submission,
    })


@student_required
def attendance(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")
    records = AttendanceRecord.objects.filter(student=student).order_by('-date')
    total_hours = sum(r.hours_rendered for r in records)
    present = records.filter(status='present').count()
    absent = records.filter(status='absent').count()
    late = records.filter(status='late').count()
    excused = records.filter(status='excused').count()

    return render(request, 'students/attendance.html', {
        'records': records,
        'total_hours': total_hours,
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
    })


@student_required
def submit_excuse(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")

    existing_requests = ExcuseRequest.objects.filter(student=student).order_by('-submitted_at')

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        date = request.POST.get('date')
        notes = request.POST.get('notes', '').strip()
        supporting_document = request.FILES.get('supporting_document')

        if not reason or not date:
            messages.error(request, 'Please fill in all required excuse fields.')
            return redirect('students:submit_excuse')

        if ExcuseRequest.objects.filter(student=student, date=date).exists():
            messages.error(request, 'You have already submitted an excuse request for this date.')
            return redirect('students:submit_excuse')

        supervisor_user = None
        if student.supervisor and student.supervisor.user:
            supervisor_user = student.supervisor.user
        else:
            active_assignment = student.assignments.filter(status='active').select_related('group__supervisor').first()
            if active_assignment and active_assignment.group and active_assignment.group.supervisor:
                supervisor_user = active_assignment.group.supervisor
                supervisor_profile = SupervisorProfile.objects.filter(user=supervisor_user).first()
                if supervisor_profile:
                    student.supervisor = supervisor_profile
                    student.save(update_fields=['supervisor'])

        excuse = ExcuseRequest.objects.create(
            student=student,
            supervisor=supervisor_user,
            reason=reason,
            date=date,
            supporting_document=supporting_document,
            notes=notes,
            status='pending'
        )

        if supervisor_user:
            create_notification(
                supervisor_user,
                'New Excuse Request',
                f'{student.user.get_full_name()} submitted an excuse for {date}.',
                'attendance',
                reverse('supervisors:excuse_requests')
            )

        log_action(
            request.user,
            'create',
            'ExcuseRequest',
            object_id=excuse.id,
            object_repr=str(excuse),
            details=f'Excuse request submitted for {date}',
            request=request,
        )

        messages.success(request, 'Excuse request submitted and sent to your supervisor.')
        return redirect('students:attendance')

    return render(request, 'students/submit_excuse.html', {
        'existing_requests': existing_requests,
    })


@student_required
def record_attendance(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")

    assignments = student.assignments.filter(status='active')
    if not assignments.exists():
        messages.warning(request, "You are not assigned to any company yet.")
        return redirect("students:dashboard")

    current_dt = timezone.localtime(timezone.now())
    today = current_dt.date()
    today_records = list(AttendanceRecord.objects.filter(
        student=student,
        group__in=[assignment.group for assignment in assignments],
        date=today
    ))

    for record in today_records:
        if record.current_timer_start:
            naive_start = datetime.combine(record.date, record.current_timer_start)
            aware_start = timezone.make_aware(naive_start, timezone.get_current_timezone())
            record.timer_start_ms = int(aware_start.timestamp() * 1000)
        else:
            record.timer_start_ms = None

    group_states = {}
    for assignment in assignments:
        group_states[str(assignment.group.id)] = {
            'phase': 'not_started',
            'start_time': None,
            'can_time_in': True,
            'can_break_out': False,
            'can_break_in': False,
            'can_time_out': False,
        }

    for record in today_records:
        phase = record.current_phase
        start_time = record.current_timer_start.strftime('%H:%M:%S') if record.current_timer_start else None
        group_states[str(record.group.id)] = {
            'phase': phase,
            'start_time': start_time,
            'can_time_in': record.can_time_in,
            'can_break_out': record.can_break_out,
            'can_break_in': record.can_break_in,
            'can_time_out': record.can_time_out,
        }

    if request.method == 'POST':
        action = request.POST.get('action')
        group_id = request.POST.get('group')

        if action not in ['time_in', 'break_out', 'break_in', 'time_out']:
            messages.error(request, 'Invalid attendance action.')
            return redirect('students:record_attendance')

        assignment = assignments.filter(group_id=group_id).first()
        if not assignment:
            messages.error(request, 'Invalid immersion group selected.')
            return redirect('students:record_attendance')

        record, created = AttendanceRecord.objects.get_or_create(
            student=student,
            group=assignment.group,
            date=today,
            defaults={'status': 'present'}
        )

        now = current_dt.time()
        if record.time_out:
            messages.error(request, 'Invalid action. Please complete the required previous attendance step.')
            return redirect('students:record_attendance')

        if action == 'time_in':
            if record.time_in:
                messages.error(request, 'Invalid action. Please complete the required previous attendance step.')
                return redirect('students:record_attendance')
            record.time_in = now
        elif action == 'break_out':
            if not record.time_in or record.break_out:
                messages.error(request, 'Invalid action. Please complete the required previous attendance step.')
                return redirect('students:record_attendance')
            record.break_out = now
        elif action == 'break_in':
            if not record.break_out or record.break_in:
                messages.error(request, 'Invalid action. Please complete the required previous attendance step.')
                return redirect('students:record_attendance')
            record.break_in = now
        elif action == 'time_out':
            if not record.time_in or record.time_out or (record.break_out and not record.break_in):
                messages.error(request, 'Invalid action. Please complete the required previous attendance step.')
                return redirect('students:record_attendance')
            record.time_out = now

        try:
            record.save()
            log_action(
                request.user,
                'update' if not created else 'create',
                'AttendanceRecord',
                object_id=record.id,
                object_repr=str(record),
                details=f'{action.replace("_", " ").title()} recorded for {record.date}',
                request=request,
            )
            messages.success(request, 'Attendance action recorded successfully.')
            return redirect('students:attendance')
        except Exception as e:
            messages.error(request, f'Error processing attendance: {str(e)}')
            return redirect('students:record_attendance')

    return render(request, 'students/record_attendance.html', {
        'assignments': assignments,
        'today_records': today_records,
        'today': today,
        'server_time': current_dt,
        'server_time_ms': int(current_dt.timestamp() * 1000),
        'group_states_json': json.dumps(group_states),
    })


@student_required
def journals(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")
    journal_list = DailyJournal.objects.filter(student=student).order_by('-date')

    if request.method == 'POST':
        date = request.POST.get('date')
        if DailyJournal.objects.filter(student=student, date=date).exists():
            messages.error(request, 'You already have a journal entry for this date.')
        else:
            DailyJournal.objects.create(
                student=student,
                date=date,
                activities=request.POST.get('activities', ''),
                skills_learned=request.POST.get('skills_learned', ''),
                problems_encountered=request.POST.get('problems_encountered', ''),
                reflection=request.POST.get('reflection', ''),
                attachment=request.FILES.get('attachment'),
            )
            messages.success(request, 'Journal entry submitted!')
            return redirect('students:journals')

    return render(request, 'students/journals.html', {'journals': journal_list})


@student_required
def requirements(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")
    reqs = StudentRequirement.objects.filter(student=student)

    if request.method == 'POST':
        req_type = request.POST.get('requirement_type')
        file = request.FILES.get('file')
        notes = request.POST.get('notes', '')
        if file and req_type:
            StudentRequirement.objects.create(
                student=student,
                requirement_type=req_type,
                file=file,
                notes=notes,
            )
            messages.success(request, 'Requirement uploaded successfully!')
            return redirect('students:requirements')
        else:
            messages.error(request, 'Please fill in all required fields.')

    checklist_items = []
    for value, label in StudentRequirement.REQUIREMENT_TYPES:
        requirement = reqs.filter(requirement_type=value).order_by('-uploaded_at').first()
        checklist_items.append({
            'value': value,
            'label': label,
            'status': requirement.status if requirement else 'missing',
        })

    return render(request, 'students/requirements.html', {
        'requirements': reqs,
        'requirement_types': StudentRequirement.REQUIREMENT_TYPES,
        'checklist_items': checklist_items,
    })


@student_required
def evaluation(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")
    eval_obj = Evaluation.objects.filter(student=student).first()
    return render(request, 'students/evaluation.html', {
        'student': student,
        'evaluation': eval_obj,
    })


@student_required
def announcements_list(request):
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, "Please complete your student profile first.")
        return redirect("students:profile")
    assignment = student.get_active_assignment()
    group = assignment.group if assignment else None

    ann_list = Announcement.objects.filter(target_role='all') | Announcement.objects.filter(
        target_role='students',
        group__isnull=True
    )
    if group:
        ann_list = ann_list | Announcement.objects.filter(
            group=group,
            target_role='group'
        )
    else:
        ann_list = ann_list | Announcement.objects.filter(
            target_role='group'
        )
    ann_list = ann_list.order_by('-created_at')

    return render(request, 'students/announcements.html', {'announcements': ann_list})


@student_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'students/notifications.html', {'notifications': notifs})
