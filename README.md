# ImmersionTrack
### Grade 12 Work Immersion Management System

A complete Django-based web platform for managing Grade 12 student immersion — covering company placement, task submission, attendance, journals, evaluations, and administrative reporting.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip
- (Optional) PostgreSQL — SQLite is used by default for development

### Run on Windows (PowerShell)

Open PowerShell in the project’s main folder. If you are in the folder above it, enter:
```powershell
cd .\immersion_system_fixed
```

#### First time only
Create the environment, install the project packages, prepare the database, and create your admin login:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

Follow the prompts to choose your admin username and password.

#### Every time you want to launch the site
Open PowerShell in the project’s main folder and run:
```powershell
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

Keep PowerShell open while using the site. In your browser, visit **http://127.0.0.1:8000/**. Press **Ctrl+C** in PowerShell to stop it.

If PowerShell says script execution is blocked, run this once in that terminal, then activate the environment again:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

For Linux or macOS, activate with `source venv/bin/activate` instead of the PowerShell activation command.

---

## 🔑 Default Login Credentials
(These demo accounts are created by `setup.sh`. If you followed the Windows steps above, sign in with the admin username and password you chose with `createsuperuser`.)

| Role | Username | Password | URL |
|------|----------|----------|-----|
| System Administrator | `admin` | `admin1234` | `/admin/` |
| Dean | `dean` | `dean1234` | `/dean/dashboard/` |
| Supervisor | `supervisor1` | `super1234` | `/supervisor/dashboard/` |
| Student | `student1` | `student1234` | `/student/dashboard/` |

> ⚠️ **Change all passwords before deploying to production!**

---

## 📁 Project Structure
```
immersion_system/
├── accounts/           # Custom User Model, login, register
├── students/           # Student profiles, requirements
├── companies/          # Companies, immersion groups, join codes
├── supervisors/        # Supervisor profiles
├── tasks/              # Tasks and submissions
├── attendance/         # Daily time records
├── journals/           # Daily logbook entries
├── evaluations/        # Rubric-based evaluation system
├── announcements/      # School and group announcements
├── notifications/      # In-app notification system
├── auditlogs/          # System activity audit trail
├── dean/               # Dean admin portal views and URLs
├── core/               # Role-based redirect, utilities
├── templates/          # All HTML templates
│   ├── base.html       # Shared base layout
│   ├── accounts/       # Login, register
│   ├── students/       # Student portal templates
│   ├── supervisors/    # Supervisor portal templates
│   ├── dean/           # Dean admin panel templates
│   └── errors/         # 404, 500 error pages
├── static/             # CSS, JS, images
├── media/              # User-uploaded files
├── requirements.txt
├── manage.py
└── setup.sh
```

---

## 👥 User Roles & Access

### 🎓 Student
- Register → wait for Dean approval
- Join company using a **Join Code**
- Submit tasks, upload files
- Write daily journal entries
- View attendance records
- Check evaluation and grades
- Receive notifications and announcements

### 🏢 Company Supervisor
- Account **created only by the Dean** (cannot self-register)
- Manage assigned students
- Create and publish tasks
- Grade student submissions with feedback
- Mark daily attendance
- Review and approve journal entries
- Evaluate students using rubric (7 criteria)
- Post group announcements

### 👔 Dean / School Administrator
- Full system access via **custom professional admin panel**
- Approve/reject student registrations
- Create and manage companies with join codes
- **Create supervisor accounts** (exclusive privilege)
- Create immersion groups and assign supervisors
- Monitor all attendance, submissions, evaluations
- Post school-wide announcements
- View complete audit trail
- Generate reports with charts

---

## 🗃️ Database Setup (PostgreSQL)

For production, update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'immersion_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Then install: `pip install psycopg2-binary`

---

## 📧 Email Setup

For production email (password reset, notifications), update `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
```

---

## 🔒 Security Checklist (Before Production)

- [ ] Change `SECRET_KEY` in `settings.py`
- [ ] Set `DEBUG = False`
- [ ] Set `ALLOWED_HOSTS = ['yourdomain.com']`
- [ ] Change all default passwords
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper email backend
- [ ] Set up HTTPS / SSL
- [ ] Run `python manage.py collectstatic`
- [ ] Set `STATIC_ROOT` and serve with nginx

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| Django 4.2+ | Web framework |
| Pillow | Image/profile picture handling |
| Jazzmin | Professional Django Admin UI |
| reportlab | PDF report generation |
| openpyxl | Excel export |

---

## 🏗️ Development Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Complete | Auth, roles, user model, dashboards |
| 2 | ✅ Complete | Companies, groups, join code system |
| 3 | ✅ Complete | Task creation, submission, grading |
| 4 | ✅ Complete | Attendance, journals, logbook |
| 5 | ✅ Complete | Evaluations, reports, audit logs |
| 6 | ✅ Complete | Professional UI, notifications |

---

## 🎨 Design System

- **Primary:** Deep Blue `#1E3A8A`
- **Accent:** Emerald `#10B981`
- **Warning:** Amber `#F59E0B`
- **Danger:** Red `#EF4444`
- **Fonts:** Poppins (headings) + Inter (body)
- **UI:** Bootstrap 5 + Chart.js + Font Awesome 6

---

**Project:** ImmersionTrack — Grade 12 Work Immersion Management System  
**Stack:** Django + Bootstrap 5 + Chart.js + SQLite/PostgreSQL  
**Recommended Title:** *ImmersionTrack: A Web-Based Work Immersion Management System for Grade 12 Students*
