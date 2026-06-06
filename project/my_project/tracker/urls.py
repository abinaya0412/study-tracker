from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'tracker'

urlpatterns = [
    # Landing page (home)
    path('', views.landing, name='landing'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='tracker:landing'), name='logout'),
    path('register/', views.register, name='register'),
    
    # Main pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('session/', views.session, name='session'),
    path('reports/', views.reports, name='reports'),
    path('reports/export-pdf/', views.export_pdf, name='export_pdf'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    
    # Subject management
    path('subjects/', views.subjects, name='subjects'),
    path('subjects/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    
    # Goals management
    path('goals/', views.goals, name='goals'),
    path('goals/delete/<int:goal_id>/', views.delete_goal, name='delete_goal'),
    
    # Achievements
    path('achievements/', views.achievements_list, name='achievements'),
    
    # History
    path('history/', views.history, name='history'),
    path('history/delete/<uuid:session_id>/', views.delete_session, name='delete_session'),
    
    # Timer API endpoints
    path('api/timer/start/', views.start_timer, name='start_timer'),
    path('api/timer/pause/', views.pause_timer, name='pause_timer'),
    path('api/timer/resume/', views.resume_timer, name='resume_timer'),
    path('api/timer/stop/', views.stop_timer, name='stop_timer'),
    path('api/timer/status/', views.get_timer_status, name='get_timer_status'),
    
    # Stats API
    path('api/stats/', views.get_stats, name='get_stats'),
]