from django.db import models
from django.utils import timezone
from accounts.models import User
from companies.models import ImmersionGroup
from students.models import StudentProfile


class Task(models.Model):
    group = models.ForeignKey(ImmersionGroup, on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    due_date = models.DateTimeField()
    max_score = models.IntegerField(default=100)
    attachment = models.FileField(upload_to='task_attachments/%Y/%m/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.group}"

    def is_overdue(self):
        return timezone.now() > self.due_date

    def get_submission_count(self):
        return self.submissions.count()

    def get_submission_for_student(self, student):
        return self.submissions.filter(student=student).first()


class TaskSubmission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('late', 'Late Submitted'),
        ('reviewed', 'Reviewed'),
        ('graded', 'Graded'),
        ('returned', 'Returned for Revision'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='submissions/%Y/%m/')
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(blank=True, null=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')

    class Meta:
        unique_together = ('task', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student} - {self.task.title}"

    def is_late(self):
        return self.submitted_at > self.task.due_date
