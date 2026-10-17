from django.db import models
from accounts.models import User
from companies.models import ImmersionGroup


class Announcement(models.Model):
    TARGET_CHOICES = [
        ('all', 'All Users'),
        ('students', 'Students Only'),
        ('supervisors', 'Supervisors Only'),
        ('group', 'Specific Group'),
    ]

    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=255)
    content = models.TextField()
    target_role = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    group = models.ForeignKey(ImmersionGroup, on_delete=models.CASCADE, blank=True, null=True, related_name='announcements')
    attachment = models.FileField(upload_to='announcements/', blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title
