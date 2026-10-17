# ImmersionTrack
## Grade 12 Work Immersion Management System

### 1. System Overview
ImmersionTrack is a Django-based web application designed to manage Grade 12 work immersion programs. It provides a centralized platform for students, company supervisors, and the school dean to coordinate placements, attendance, task submissions, daily journals, evaluations, announcements, and reports.

The system supports:
- Role-based access for students, supervisors, and the dean
- Student onboarding, approval workflows, and company placement
- Task management, submissions, grading, and feedback
- Attendance tracking with multi-phase QR code support
- Daily journal/logbook entry review and approval
- Supervisor evaluations with rubric-based scoring
- Announcements and in-app notifications
- Audit logs and administrative monitoring


### 1.1 What’s New in the System
- New multi-phase attendance QR workflow for time-in, break-out, break-in, and time-out tracking
- Student application approval and automated group assignment tracking
- Supervisor task creation and submission review with late/returned statuses
- Daily journal submission review by supervisors with approval/rejection workflow
- Rubric-based evaluation with final score computation and grade generation
- Company join codes for secure student enrollment into immersion groups
- Attendance backups and downloadable records for compliance and audit
- Custom dashboard summaries for dean, supervisor, and student roles


### 2. Core Objectives
- Simplify work immersion administration for Grade 12 programs
- Replace manual spreadsheet tracking with digital workflows
- Improve communication between students, supervisors, and school administrators
- Generate accurate performance, attendance, and completion reports
- Maintain accountability through audit trails and approval workflows


### 3. Technology Stack
- Django 4.2+ web framework
- SQLite by default for development (PostgreSQL recommended for production)
- Bootstrap 5 for responsive interface components
- Django Jazzmin for a polished administration UI
- ReportLab for PDF reports
- OpenPyXL for Excel exports
- QR code generation for attendance tracking
- OpenCV / Pyzbar support for scanning codes and verifying attendance data


### 4. User Roles & Access
#### Student
- Register for immersion and submit profile details
- Await approval from the dean
- Join a company or immersion group using a join code
- Submit task files and receive supervisor feedback
- Log daily journals and reflections
- View attendance records, task grades, and evaluations
- Submit leave or excuse requests with supporting documents

#### Supervisor
- Account created by the dean; cannot self-register
- Manage assigned immersion group(s) and company students
- Publish tasks and set deadlines
- Review and grade student task submissions
- Verify attendance through time-in, break, and time-out records
- Review daily journals and approve or reject entries
- Complete rubric-based evaluations for assigned students
- Post announcements to group or school-wide audiences

#### Dean / Administrator
- Full administrative oversight of the immersion system
- Approve or reject student registration and placement requests
- Create companies, immersion groups, and join codes
- Add and manage supervisors
- Monitor attendance, journal entries, reports, and student progress
- View audit logs for system operations
- Manage announcements and notifications
- Download attendance backups and administrative reports


### 5. Key Modules
#### Accounts
- Custom `User` model with role selection (`student`, `supervisor`, `dean`)
- Student registration with profile creation and approval workflow
- Profile pictures, account activation, and role-specific permissions

#### Students
- `StudentProfile` extends user data with student ID, strand, section, school year, contact details, and application status
- Leave requests and requirement uploads are tracked in this module
- Students can only access their own records via role-based decorators

#### Companies
- `Company` record includes industry type, contact details, required hours, and join code
- `ImmersionGroup` defines the work immersion group, company, supervisor, and date range
- `StudentCompanyAssignment` joins students to groups and tracks assignment status
- Join codes allow students to enroll in groups securely

#### Tasks
- Supervisors create `Task` records with title, description, instructions, due date, score, and attachments
- Students submit `TaskSubmission` files, comments, and later receive scores and feedback
- Submission statuses include submitted, late, reviewed, graded, and returned for revision

#### Attendance
- Multi-phase attendance tracking with `AttendanceRecord` fields for time-in, break-out, break-in, and time-out
- QR code support via `AttendanceQR` for secure attendance capture
- Records include hours rendered, attendance status, approval status, verifier, and remarks
- Students submit excuse requests when absent or unable to report
- Attendance backup files are available for download

#### Journals
- Students submit `DailyJournal` entries describing daily activities, skills learned, challenges, and reflections
- Supervisors review journals and provide remarks
- Entry status is tracked as pending, approved, or rejected

#### Evaluations
- Supervisors rate students across seven criteria: punctuality, attendance, work quality, professionalism, communication, teamwork, initiative
- `Evaluation` computes a combined final score and can derive a grade letter
- Evaluation comments and recommendations are stored for school review

#### Announcements & Notifications
- Announcements can target all users, only students, only supervisors, or a specific immersion group
- Notifications support event types like task creation, submission updates, attendance alerts, journal reviews, evaluations, and approvals
- Users receive real-time alerts in the system dashboard

#### Audit Logs
- All critical actions are recorded in `AuditLog`
- Tracks who performed each action, when, and what object was changed
- Includes action type, model name, object detail, and IP address when available
- Helps administrators maintain accountability and trace changes


### 6. Core System Workflows
#### Student Onboarding
1. Student registers and submits profile details
2. Dean reviews and approves application
3. Dean assigns the student to a company/group or student joins via company join code
4. Supervisor begins monitoring student progress and attendance

#### Task Submission Process
1. Supervisor publishes a task with instructions and deadline
2. Student uploads work and submits it through the portal
3. Supervisor reviews submission, adds feedback, and assigns a score
4. Student can view graded results, comments, and resubmit if returned

#### Attendance and Leave Management
1. Supervisor generates attendance QR codes for time-in, break, and time-out
2. Student scans or records attendance events
3. Attendance record calculates total hours rendered automatically
4. Supervisor approves or rejects attendance and excuse requests

#### Evaluation and Reporting
1. Supervisor completes rubric evaluation once immersion activities progress
2. System computes a final score and outputs a grade letter
3. Dean can view summary reports of student performance and attendance
4. Reports can be exported for administrative review and presentations


### 7. System Architecture & Security
- Built on Django with apps separated by function for maintainability
- Custom role-based access using decorators in `core/decorators.py`
- Professional admin UI powered by Jazzmin for improved usability
- Production recommendation: use PostgreSQL, secure email backend, HTTPS, and change default secrets
- Default setup script creates demo accounts but must be replaced with strong credentials before deployment


### 8. Setup Summary
- Python 3.10+ required
- Install dependencies from `requirements.txt`
- Run migrations for each app module and `python manage.py migrate`
- Optionally use `setup.sh` to create demo users and collect static files
- Start server with `python manage.py runserver 0.0.0.0:8000`


### 9. Default Demo Credentials
| Role | Username | Password | Intended Use |
|------|----------|----------|--------------|
| System Administrator / Dean | `admin` / `dean` | `admin1234` / `dean1234` | Admin panel and dean dashboard |
| Supervisor | `supervisor1` | `super1234` | Supervisor dashboard workflow |
| Student | `student1` | `student1234` | Student portal workflow |

> Note: Change default passwords immediately for production.


### 10. Recommended Presentation Outline
1. Project name and purpose
2. Target users and roles
3. System architecture and technology stack
4. Main features by module
5. Typical student/supervisor/dean workflows
6. Security and deployment notes
7. Live demo or screenshot examples
8. Benefits for schools and companies


### 11. Benefits and Impact
- Promotes consistent documentation of student work immersion
- Reduces manual tracking errors for attendance and evaluations
- Improves supervisor feedback and grade transparency
- Enables dean-level oversight through centralized dashboards
- Provides digital records for compliance, auditing, and reporting


---

**ImmersionTrack** is designed to be a complete digital solution for schools and partner companies managing Grade 12 immersion programs. This report can be used directly for presentation slides, handouts, or executive summaries.
