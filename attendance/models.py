from django.db import models
from accounts.models import User
from students.models import StudentProfile
from companies.models import ImmersionGroup
import uuid


class AttendanceQR(models.Model):
    ATTENDANCE_TYPE_CHOICES = [
        ('time_in', 'Time In'),
        ('break_out', 'Break Out'),
        ('break_in', 'Break In'),
        ('time_out', 'Time Out'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_qrs')
    group = models.ForeignKey(ImmersionGroup, on_delete=models.CASCADE, related_name='attendance_qrs')
    attendance_type = models.CharField(max_length=20, choices=ATTENDANCE_TYPE_CHOICES)
    date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('group', 'attendance_type', 'date')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.group} - {self.attendance_type} ({self.date})"

    @property
    def qr_data(self):
        """Generate QR code data that includes all necessary information"""
        return f"attendance:{self.id}:{self.attendance_type}:{self.group.id}"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('half_day', 'Half Day'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_records')
    group = models.ForeignKey(ImmersionGroup, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    time_in = models.TimeField(blank=True, null=True)
    break_out = models.TimeField(blank=True, null=True)
    break_in = models.TimeField(blank=True, null=True)
    time_out = models.TimeField(blank=True, null=True)
    hours_rendered = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_attendance')
    approved_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_attendance')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'date', 'group')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} - {self.date} ({self.status})"

    @property
    def current_phase(self):
        if self.time_out:
            return 'completed'
        if self.break_out and not self.break_in:
            return 'break'
        if self.break_in:
            return 'resumed'
        if self.time_in:
            return 'working'
        return 'not_started'

    @property
    def current_timer_start(self):
        if self.current_phase == 'break':
            return self.break_out
        if self.current_phase == 'resumed':
            return self.break_in
        if self.current_phase == 'working':
            return self.time_in
        return None

    @property
    def can_time_in(self):
        return self.time_in is None

    @property
    def can_break_out(self):
        return bool(self.time_in and not self.break_out and not self.time_out)

    @property
    def can_break_in(self):
        return bool(self.break_out and not self.break_in and not self.time_out)

    @property
    def can_time_out(self):
        return bool(self.time_in and not self.time_out and (not self.break_out or self.break_in))

    def save(self, *args, **kwargs):
        # Auto-calculate hours rendered using the record's date and stored times.
        if self.time_in and self.time_out:
            from datetime import datetime
            record_date = self.date
            dt_in = datetime.combine(record_date, self.time_in)
            dt_out = datetime.combine(record_date, self.time_out)

            # Calculate break time if both break_out and break_in are present
            break_hours = 0
            if self.break_out and self.break_in:
                dt_break_out = datetime.combine(record_date, self.break_out)
                dt_break_in = datetime.combine(record_date, self.break_in)
                break_diff = dt_break_in - dt_break_out
                break_hours = max(break_diff.total_seconds(), 0) / 3600

            diff = dt_out - dt_in
            total_hours = max(diff.total_seconds(), 0) / 3600
            self.hours_rendered = round(total_hours - break_hours, 2)
        else:
            self.hours_rendered = 0
        super().save(*args, **kwargs)


class ExcuseRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='excuse_requests')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='excuse_requests')
    reason = models.TextField()
    date = models.DateField()
    supporting_document = models.FileField(upload_to='excuses/%Y/%m/', blank=True, null=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_excuse_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    supervisor_comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student} excuse for {self.date} ({self.status})"


class AttendanceBackup(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_backups')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_backups')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    backup_file = models.FileField(upload_to='attendance_backups/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Attendance backup for {self.student} ({self.created_at:%Y-%m-%d %H:%M})"
