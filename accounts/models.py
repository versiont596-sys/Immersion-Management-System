from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('supervisor', 'Supervisor'),
        ('dean', 'Administrator'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_approved = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    def is_student(self):
        return self.role == 'student'

    def is_supervisor(self):
        return self.role == 'supervisor'

    def is_dean(self):
        return self.role == 'dean'
