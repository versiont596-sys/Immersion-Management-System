import random
import string
from django.db import models
from accounts.models import User


def generate_join_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Company(models.Model):
    INDUSTRY_CHOICES = [
        ('IT', 'Information Technology'),
        ('BPO', 'Business Process Outsourcing'),
        ('Finance', 'Finance & Banking'),
        ('Healthcare', 'Healthcare'),
        ('Education', 'Education'),
        ('Retail', 'Retail & Commerce'),
        ('Manufacturing', 'Manufacturing'),
        ('Government', 'Government'),
        ('NGO', 'Non-Government Organization'),
        ('Media', 'Media & Communications'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_person = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    industry_type = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, default='Other')
    required_hours = models.IntegerField(default=80)
    join_code = models.CharField(max_length=20, unique=True, default=generate_join_code)
    capacity = models.IntegerField(default=50)
    description = models.TextField(blank=True)
    accepted_strands = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def accepts_strand(self, strand_code):
        if not self.accepted_strands:
            return True
        return strand_code in self.accepted_strands

    def get_accepted_strands_display(self):
        from students.models import StudentProfile
        strand_labels = {code: label for code, label in StudentProfile.STRAND_CHOICES}
        return [strand_labels.get(code, code) for code in self.accepted_strands] if self.accepted_strands else []

    def __str__(self):
        return self.name

    def get_student_count(self):
        return StudentCompanyAssignment.objects.filter(group__company=self, status='active').count()

    def regenerate_code(self):
        self.join_code = generate_join_code()
        self.save()


class ImmersionGroup(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='groups')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_groups')
    name = models.CharField(max_length=255)
    school_year = models.CharField(max_length=20, default='2024-2025')
    start_date = models.DateField()
    end_date = models.DateField()
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.company.name}"

    def get_student_count(self):
        return self.assignments.filter(status='active').count()


class StudentCompanyAssignment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('pending', 'Pending Approval'),
    ]

    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='assignments')
    group = models.ForeignKey(ImmersionGroup, on_delete=models.CASCADE, related_name='assignments')
    joined_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    joined_via_code = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'group')

    def __str__(self):
        return f"{self.student} → {self.group}"
