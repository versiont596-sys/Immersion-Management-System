from django.db import models
from accounts.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('task', 'New Task'),
        ('submission', 'Submission'),
        ('attendance', 'Attendance'),
        ('journal', 'Journal'),
        ('evaluation', 'Evaluation'),
        ('announcement', 'Announcement'),
        ('approval', 'Account Approval'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"


def create_notification(user, title, message, notif_type='general', link=''):
    """Helper to create notifications."""
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notif_type=notif_type,
        link=link,
    )
