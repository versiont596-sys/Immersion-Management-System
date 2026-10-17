from django.core.exceptions import ValidationError
from django.db import models
from accounts.models import User


class StudentProfile(models.Model):
    STRAND_CHOICES = [
        ('ABM', 'Accountancy, Business and Management'),
        ('HUMSS', 'Humanities and Social Sciences'),
        ('STEM', 'Science, Technology, Engineering and Mathematics'),
        ('TVL', 'Technical-Vocational-Livelihood'),
        ('GAS', 'General Academic Strand'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    strand = models.CharField(max_length=10, choices=STRAND_CHOICES)
    section = models.CharField(max_length=100)
    school_year = models.CharField(max_length=20, default='2024-2025')
    contact_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True)
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_contact = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    supervisor = models.ForeignKey(
        'supervisors.SupervisorProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    APPLICATION_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    application_status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_id}"

    def clean(self):
        errors = {}
        if not self.student_id:
            errors['student_id'] = 'LRN is required.'
        if not self.section:
            errors['section'] = 'Section is required.'
        if errors:
            raise ValidationError(errors)

    def get_active_assignment(self):
        return self.assignments.filter(status='active').first()

    def get_total_hours(self):
        from attendance.models import AttendanceRecord
        records = AttendanceRecord.objects.filter(student=self)
        return sum(r.hours_rendered for r in records)

    def get_task_stats(self):
        from tasks.models import TaskSubmission
        submissions = TaskSubmission.objects.filter(student=self)
        return {
            'submitted': submissions.count(),
            'graded': submissions.filter(status='graded').count(),
        }


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='leave_requests')
    assignment = models.ForeignKey('companies.StudentCompanyAssignment', on_delete=models.SET_NULL, null=True, blank=True, related_name='leave_requests')
    group = models.ForeignKey('companies.ImmersionGroup', on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leave_requests')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Leave request for {self.student.user.get_full_name()} - {self.group or self.assignment.group if self.assignment else 'Unknown'}"


class StudentRequirement(models.Model):
    REQUIREMENT_TYPES = [
        ('resume', 'Resume'),
        ('parent_consent', 'Parent Consent'),
        ('medical_certificate', 'Medical Certificate'),
        ('waiver', 'Waiver'),
        ('endorsement_letter', 'Endorsement Letter'),
        ('completion_report', 'Completion Report'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='requirements')
    requirement_type = models.CharField(max_length=50, choices=REQUIREMENT_TYPES)
    file = models.FileField(upload_to='requirements/%Y/%m/')
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requirements')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    supervisor_comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.get_requirement_type_display()}"
