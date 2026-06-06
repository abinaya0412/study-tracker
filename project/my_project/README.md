# Study Time Tracker - Complete Django Application

A comprehensive Django-based web application for tracking study time, managing subjects, setting goals, and generating detailed reports with PDF export functionality.

## 🎯 Complete Feature List

### ✅ **Implemented Features**

1. **User Authentication System**
   - Registration with automatic goal creation
   - Login/Logout functionality
   - Password reset capability
   - Profile management with avatar support

2. **Subject Management (CRUD)**
   - Create custom subjects with color coding
   - Edit subject details
   - Delete subjects
   - View subject statistics

3. **Study Timer System**
   - **Start/Pause/Resume/Stop** functionality
   - Real-time server-side tracking
   - Automatic session saving
   - Session recovery on page reload
   - Keyboard shortcuts (Space to start/pause, Escape to stop)

4. **Goal Management**
   - **Daily Goals**: Set custom daily study targets
   - **Weekly Goals**: Set weekly study targets
   - **Monthly Goals**: Set monthly study targets
   - Manual goal setting (no forced defaults)
   - Progress tracking with percentage display
   - Goal achievement notifications

5. **Achievement System**
   - Automatic achievement detection
   - Badge earning system
   - Achievement display with icons
   - Motivational messages on goal completion

6. **Dashboard**
   - Today's progress display
   - Goal completion percentages
   - Current streak counter
   - Recent sessions list
   - Subject distribution chart
   - Active timer alerts

7. **Reports & Analytics**
   - Daily, weekly, monthly breakdown
   - Exact hours:minutes:seconds format
   - Interactive Chart.js charts
   - Subject-wise analysis
   - Time-based patterns

8. **PDF Export**
   - Professional PDF reports
   - Summary statistics
   - Subject breakdown
   - Recent sessions list
   - Formatted with tables and styling

9. **Profile & Settings**
   - Edit profile information
   - Change password
   - Notification preferences
   - Privacy settings

10. **Session History**
    - Filter by subject, date range
    - Delete sessions
    - Export to PDF

## 📁 Project Structure

```
my_project/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
├── my_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── tracker/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── tests.py
    ├── migrations/
    ├── templatetags/
    │   ├── __init__.py
    │   └── tracker_filters.py
    ├── static/
    │   ├── css/
    │   │   ├── base.css
    │   │   ├── animations.css
    │   │   └── components.css
    │   ├── js/
    │   │   └── main.js
    │   └── images/
    └── templates/
        ├── base.html
        ├── tracker/
        │   ├── landing.html
        │   ├── login.html
        │   ├── register.html
        │   ├── dashboard.html
        │   ├── session.html
        │   ├── reports.html
        │   ├── profile.html
        │   ├── settings.html
        │   ├── subjects.html
        │   ├── goals.html
        │   ├── achievements.html
        │   └── history.html
        └── account/
```

## 🗄️ Database Models

### Subject
- `user`: ForeignKey to User
- `name`: CharField (100 chars)
- `color`: CharField (7 chars, hex color)
- `description`: TextField (optional)
- `created_at`, `updated_at`: DateTimeFields

### StudySession
- `user`: ForeignKey to User
- `subject`: ForeignKey to Subject
- `session_id`: UUIDField (unique)
- `start_time`, `end_time`: DateTimeFields
- `duration`: DurationField (auto-calculated)
- `notes`: TextField (optional)
- `status`: CharField (active/paused/completed)

### DailyGoal
- `user`: ForeignKey to User
- `date`: DateField
- `target_duration`: DurationField
- `actual_duration`: DurationField (auto-calculated)
- `achieved`: BooleanField

### WeeklyGoal
- `user`: ForeignKey to User
- `week_start`: DateField (Monday of the week)
- `target_duration`: DurationField
- `actual_duration`: DurationField (auto-calculated)
- `achieved`: BooleanField

### MonthlyGoal
- `user`: ForeignKey to User
- `month`, `year`: IntegerFields
- `target_duration`: DurationField
- `actual_duration`: DurationField (auto-calculated)
- `achieved`: BooleanField

### Achievement
- `name`: CharField
- `description`: TextField
- `icon`: CharField (emoji)
- `requirement`: TextField
- `points`: IntegerField
- `badge_type`: CharField (first_session, streak, goal, study_time)

### UserAchievement
- `user`: ForeignKey to User
- `achievement`: ForeignKey to Achievement
- `earned_at`: DateTimeField
- `notes`: TextField

### Streak
- `user`: ForeignKey to User
- `current_streak`, `best_streak`: IntegerFields
- `last_study_date`: DateField

### TimerSession
- `user`: ForeignKey to User
- `subject`: ForeignKey to Subject
- `session_id`: UUIDField
- `start_time`: DateTimeField
- `paused_time`: DateTimeField (optional)
- `total_paused_duration`: DurationField
- `is_paused`, `is_active`: BooleanFields
- `notes`: TextField

## 🔗 URL Routes

| URL | View | Description |
|-----|------|-------------|
| `/` | landing | Landing page |
| `/login/` | login | User login |
| `/logout/` | logout | User logout |
| `/register/` | register | User registration |
| `/dashboard/` | dashboard | Main dashboard |
| `/session/` | session | Study timer |
| `/reports/` | reports | Reports & analytics |
| `/reports/export-pdf/` | export_pdf | Export PDF |
| `/profile/` | profile | User profile |
| `/settings/` | settings | Settings page |
| `/subjects/` | subjects | Subject management |
| `/subjects/delete/<id>/` | delete_subject | Delete subject |
| `/goals/` | goals | Goals management |
| `/achievements/` | achievements_list | Achievements page |
| `/history/` | history | Session history |
| `/api/timer/start/` | start_timer | Start timer API |
| `/api/timer/pause/` | pause_timer | Pause timer API |
| `/api/timer/resume/` | resume_timer | Resume timer API |
| `/api/timer/stop/` | stop_timer | Stop timer API |
| `/api/timer/status/` | get_timer_status | Get timer status API |
| `/api/stats/` | get_stats | Get statistics API |

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Migrations
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### Step 3: Create Superuser
```bash
python3 manage.py createsuperuser
```

### Step 4: Start Development Server
```bash
python3 manage.py runserver
```

### Step 5: Access Application
- **Main Site**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## 📊 ER Diagram

```
User (1) ----< (Many) Subject
User (1) ----< (Many) StudySession
User (1) ----< (Many) DailyGoal
User (1) ----< (Many) WeeklyGoal
User (1) ----< (Many) MonthlyGoal
User (1) ----< (Many) UserAchievement
User (1) ----< (Many) Streak
User (1) ----< (Many) TimerSession

Subject (1) ----< (Many) StudySession
Subject (1) ----< (Many) TimerSession

Achievement (1) ----< (Many) UserAchievement

StudySession >---- (Many) Subject (through ForeignKey)
```

## 🎨 Frontend Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Clean, professional interface
- **Animations**: Smooth transitions and micro-interactions
- **Real-time Updates**: Live timer and progress tracking
- **Interactive Charts**: Chart.js for data visualization
- **Accessibility**: Keyboard shortcuts and screen reader support

## 🔧 Custom Template Filters

- `seconds_to_time`: Convert seconds to "Xh Ym Zs" format
- `duration_to_time`: Convert timedelta to time string
- `format_duration`: Format as "HH:MM:SS"
- `modulo`: Modulo operation for templates
- `get_item`: Dictionary item access

## 📝 Testing

Run the test suite:
```bash
python3 manage.py test tracker
```

## 🚀 Deployment

### Production Checklist
1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS`
3. Set up PostgreSQL/MySQL database
4. Configure static file serving (WhiteNoise or CDN)
5. Set up HTTPS
6. Use environment variables for sensitive data
7. Configure email backend for password resets

### Recommended Hosting
- **PythonAnywhere**: Easy Django hosting
- **Heroku**: Popular PaaS
- **DigitalOcean**: VPS hosting
- **AWS/GCP/Azure**: Cloud platforms

## 📄 License

This project is open source and available for educational purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## 📧 Support

For issues, questions, or suggestions, please create an issue in the project repository.

---

**Built with Django** | **Study Time Tracker v2.0** | **Final Year College Mini-Project**