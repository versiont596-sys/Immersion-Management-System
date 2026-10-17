#!/bin/bash
# ============================================================
# ImmersionTrack - Quick Setup Script
# Grade 12 Work Immersion Management System
# ============================================================
set -e

echo ""
echo "=========================================="
echo "  ImmersionTrack Setup"
echo "=========================================="
echo ""

# 1. Create virtual environment
echo "[1/6] Creating virtual environment..."
python -m venv venv
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# 2. Install dependencies
echo "[2/6] Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "      ✓ Dependencies installed (including QR code support)"

# 3. Run migrations
echo "[3/6] Running database migrations..."
python manage.py makemigrations accounts
python manage.py makemigrations students
python manage.py makemigrations companies
python manage.py makemigrations supervisors
python manage.py makemigrations tasks
python manage.py makemigrations attendance
python manage.py makemigrations journals
python manage.py makemigrations evaluations
python manage.py makemigrations announcements
python manage.py makemigrations notifications
python manage.py makemigrations auditlogs
python manage.py migrate
echo "      ✓ Database ready"

# 4. Collect static files
echo "[4/6] Collecting static files..."
python manage.py collectstatic --noinput -v 0
echo "      ✓ Static files collected"

# 5. Create/repair demo accounts
echo ""
echo "[5/6] Setting up demo accounts..."
echo ""

python manage.py shell -c "
from accounts.models import User

accounts = [
    {
        'username': 'admin',
        'email': 'admin@school.edu',
        'password': 'admin1234',
        'first_name': 'System',
        'last_name': 'Administrator',
        'role': 'dean',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'username': 'dean',
        'email': 'dean@school.edu',
        'password': 'dean1234',
        'first_name': 'School',
        'last_name': 'Dean',
        'role': 'dean',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'username': 'supervisor1',
        'email': 'supervisor@company.com',
        'password': 'super1234',
        'first_name': 'Maria',
        'last_name': 'Santos',
        'role': 'supervisor',
        'is_staff': False,
        'is_superuser': False,
    },
    {
        'username': 'student1',
        'email': 'student@school.edu',
        'password': 'student1234',
        'first_name': 'Juan',
        'last_name': 'dela Cruz',
        'role': 'student',
        'is_staff': False,
        'is_superuser': False,
    },
]

for data in accounts:
    user, created = User.objects.get_or_create(username=data['username'])
    user.email = data['email']
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.role = data['role']
    user.is_active = True
    user.is_approved = True
    user.is_staff = data['is_staff']
    user.is_superuser = data['is_superuser']
    user.set_password(data['password'])  # Always hash properly
    user.save()
    status = 'Created' if created else 'Repaired'
    print(f'  {status}: {user.username} ({user.role})')

print('')
print('  All accounts are ready.')
"

# Create supervisor profile if it doesn't exist
python manage.py shell -c "
from accounts.models import User
from supervisors.models import SupervisorProfile
try:
    u = User.objects.get(username='supervisor1')
    SupervisorProfile.objects.get_or_create(
        user=u,
        defaults={'position': 'HR Manager', 'contact_number': '09171234567'}
    )
    print('  Supervisor profile ready.')
except Exception as e:
    print(f'  Note: Could not create supervisor profile: {e}')
"

# Create student profile if it doesn't exist
python manage.py shell -c "
from accounts.models import User
from students.models import StudentProfile
try:
    u = User.objects.get(username='student1')
    StudentProfile.objects.get_or_create(
        user=u,
        defaults={
            'student_id': '2024-00001',
            'strand': 'STEM',
            'section': '12-A',
            'school_year': '2024-2025',
            'contact_number': '09181234567',
        }
    )
    print('  Student profile ready.')
except Exception as e:
    print(f'  Note: Could not create student profile: {e}')
"

echo ""
echo "[6/6] Setup complete!"
echo ""
echo "=========================================="
echo "  LOGIN CREDENTIALS"
echo "=========================================="
echo ""
echo "  Django Admin (System Administrator):"
echo "    URL:      http://127.0.0.1:8000/admin/"
echo "    Username: admin"
echo "    Password: admin1234"
echo ""
echo "  Dean Dashboard:"
echo "    URL:      http://127.0.0.1:8000/core/redirect/"
echo "    Username: dean"
echo "    Password: dean1234"
echo ""
echo "  Supervisor:"
echo "    URL:      http://127.0.0.1:8000/core/redirect/"
echo "    Username: supervisor1"
echo "    Password: super1234"
echo ""
echo "  Student:"
echo "    URL:      http://127.0.0.1:8000/core/redirect/"
echo "    Username: student1"
echo "    Password: student1234"
echo ""
echo "=========================================="
echo ""
echo "  Starting development server..."
echo "  Open from this computer: http://127.0.0.1:8000"
echo "  Open from another local device: http://<YOUR_PC_IP>:8000"
echo ""
python manage.py runserver
python manage.py runserver 0.0.0.0:8000
