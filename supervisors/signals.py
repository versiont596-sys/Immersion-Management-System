from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from .models import SupervisorProfile
from companies.models import Company


@receiver(post_save, sender=User)
def create_supervisor_profile(sender, instance, created, **kwargs):
    """Automatically create SupervisorProfile when a supervisor user is created."""
    if created and instance.role == 'supervisor':
        try:
            # Get first active company or create default
            company = Company.objects.filter(is_active=True).first()
            if not company:
                company = Company.objects.create(
                    name='Default Company',
                    address='Default Address',
                    contact_person='Default Contact',
                    contact_email='default@company.com',
                    contact_number='0000000000',
                    is_active=True
                )

            SupervisorProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'company': company,
                    'position': 'Supervisor',
                    'contact_number': ''
                }
            )
        except Exception as e:
            # Log the error but don't break user creation
            print(f"Warning: Failed to create supervisor profile for {instance.username}: {e}")
            pass