from django.db import models
from accounts.models import User
from companies.models import Company
from students.models import StudentProfile


class SupervisorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supervisor_profile')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervisors')
    position = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    strand = models.CharField(
        max_length=10,
        choices=StudentProfile.STRAND_CHOICES,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company}"

    def get_assigned_students(self):
        from django.db.models import Q
        groups = self.user.supervised_groups.all()
        return StudentProfile.objects.filter(
            Q(supervisor=self) | Q(assignments__group__supervisor=self.user)
        ).distinct()
