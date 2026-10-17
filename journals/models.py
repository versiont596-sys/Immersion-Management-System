from django.db import models
from accounts.models import User
from students.models import StudentProfile


class DailyJournal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='journals')
    date = models.DateField()
    activities = models.TextField(help_text='What did you do today?')
    skills_learned = models.TextField(help_text='What skills did you learn?')
    problems_encountered = models.TextField(blank=True, help_text='Any problems or challenges?')
    reflection = models.TextField(help_text='Your thoughts and reflection for the day')
    attachment = models.FileField(upload_to='journals/%Y/%m/', blank=True, null=True)
    supervisor_remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_journals')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} - Journal {self.date}"
