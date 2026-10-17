from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from .models import StudentProfile


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    """Automatically create StudentProfile when a student user is created."""
    if created and instance.role == 'student':
        StudentProfile.objects.get_or_create(
            user=instance,
            defaults={
                'student_id': f'2024-{instance.id:05d}',
                'strand': 'STEM',
                'section': '12-A',
                'school_year': '2024-2025',
                'contact_number': ''
            }
        )