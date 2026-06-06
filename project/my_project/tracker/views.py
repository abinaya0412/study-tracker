from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDate, TruncHour
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.serializers import serialize
import json

from .models import (
    Subject, StudySession, DailyGoal, WeeklyGoal, MonthlyGoal,
    Achievement, UserAchievement, Streak, TimerSession
)


def landing(request):
    """Landing page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('tracker:dashboard')
    return render(request, 'tracker/landing.html')


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('tracker:dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            
            # Create streak tracker
            Streak.get_or_create(user)
            
            messages.success(request, 'Account created successfully! Welcome to StudyTracker. Set your first study goal to get started!')
            return redirect('tracker:dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'tracker/register.html', {'form': form})


@login_required
def dashboard(request):
    """Main dashboard view with real-time statistics"""
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Get or create goals
    daily_goal = DailyGoal.get_or_create_today(request.user)
    weekly_goal = WeeklyGoal.get_or_create_current(request.user)
    monthly_goal = MonthlyGoal.get_or_create_current(request.user)
    
    # Calculate actual durations
    daily_goal.calculate_actual_duration()
    weekly_goal.calculate_actual_duration()
    monthly_goal.calculate_actual_duration()
    
    # Calculate study times
    today_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date=today,
        status='completed'
    )
    today_seconds = sum(s.duration.total_seconds() for s in today_sessions if s.duration)
    
    week_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date__gte=start_of_week,
        start_time__date__lte=today,
        status='completed'
    )
    week_seconds = sum(s.duration.total_seconds() for s in week_sessions if s.duration)
    
    month_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date__gte=start_of_month,
        start_time__date__lte=today,
        status='completed'
    )
    month_seconds = sum(s.duration.total_seconds() for s in month_sessions if s.duration)
    
    # Get streak
    streak = Streak.get_or_create(request.user)
    
    # Get recent sessions
    recent_sessions = StudySession.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('subject')[:5]
    
    # Get subjects with study time
    subjects_data = []
    for subject in Subject.objects.filter(user=request.user):
        subject_sessions = StudySession.objects.filter(
            user=request.user,
            subject=subject,
            status='completed',
            start_time__date__gte=start_of_month
        )
        subject_seconds = sum(s.duration.total_seconds() for s in subject_sessions if s.duration)
        if subject_seconds > 0:
            subjects_data.append({
                'name': subject.name,
                'color': subject.color,
                'seconds': subject_seconds,
                'percentage': round((subject_seconds / month_seconds * 100) if month_seconds > 0 else 0, 1)
            })
    
    # Check for active timer
    active_timer = TimerSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()
    
    # Get user achievements
    user_achievements = UserAchievement.objects.filter(
        user=request.user
    ).select_related('achievement')[:5]
    
    # Calculate total study time
    total_sessions = StudySession.objects.filter(
        user=request.user,
        status='completed'
    )
    total_seconds = sum(s.duration.total_seconds() for s in total_sessions if s.duration)
    
    context = {
        'user': request.user,
        'today_seconds': today_seconds,
        'week_seconds': week_seconds,
        'month_seconds': month_seconds,
        'total_seconds': total_seconds,
        'daily_goal': daily_goal,
        'weekly_goal': weekly_goal,
        'monthly_goal': monthly_goal,
        'daily_progress': daily_goal.get_progress_percentage(),
        'weekly_progress': weekly_goal.get_progress_percentage(),
        'monthly_progress': monthly_goal.get_progress_percentage(),
        'streak': streak,
        'recent_sessions': recent_sessions,
        'subjects_data': subjects_data,
        'active_timer': active_timer,
        'user_achievements': user_achievements,
    }
    
    return render(request, 'tracker/dashboard.html', context)


@login_required
def session(request):
    """Study session tracking view"""
    subjects = Subject.objects.filter(user=request.user)
    
    # Check for active timer
    active_timer = TimerSession.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('subject').first()
    
    # Get recent sessions
    recent_sessions = StudySession.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('subject')[:10]
    
    # Today's stats
    today = timezone.now().date()
    today_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date=today,
        status='completed'
    )
    today_seconds = sum(s.duration.total_seconds() for s in today_sessions if s.duration)
    
    context = {
        'user': request.user,
        'subjects': subjects,
        'active_timer': active_timer,
        'recent_sessions': recent_sessions,
        'today_seconds': today_seconds,
        'today_session_count': today_sessions.count(),
    }
    
    return render(request, 'tracker/session.html', context)


@login_required
@require_POST
def start_timer(request):
    """Start a new timer session"""
    subject_id = request.POST.get('subject_id')
    subject = get_object_or_404(Subject, id=subject_id, user=request.user)
    
    # Check if user already has an active timer
    existing_timer = TimerSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()
    
    if existing_timer:
        return JsonResponse({
            'success': False,
            'message': 'You already have an active timer. Please stop it first.'
        })
    
    # Create new timer session
    timer = TimerSession.objects.create(
        user=request.user,
        subject=subject
    )
    
    return JsonResponse({
        'success': True,
        'timer_id': str(timer.session_id),
        'start_time': timer.start_time.isoformat(),
        'subject': subject.name,
        'subject_color': subject.color
    })


@login_required
@require_POST
def pause_timer(request):
    """Pause the active timer"""
    timer = TimerSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()
    
    if not timer:
        return JsonResponse({
            'success': False,
            'message': 'No active timer found.'
        })
    
    timer.pause()
    
    return JsonResponse({
        'success': True,
        'is_paused': True,
        'elapsed_seconds': timer.get_elapsed_time().total_seconds()
    })


@login_required
@require_POST
def resume_timer(request):
    """Resume the paused timer"""
    timer = TimerSession.objects.filter(
        user=request.user,
        is_active=True,
        is_paused=True
    ).first()
    
    if not timer:
        return JsonResponse({
            'success': False,
            'message': 'No paused timer found.'
        })
    
    timer.resume()
    
    return JsonResponse({
        'success': True,
        'is_paused': False,
        'elapsed_seconds': timer.get_elapsed_time().total_seconds()
    })


@login_required
@require_POST
def stop_timer(request):
    """Stop the timer and save the session"""
    timer = TimerSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()
    
    if not timer:
        return JsonResponse({
            'success': False,
            'message': 'No active timer found.'
        })
    
    notes = request.POST.get('notes', '')
    session = timer.complete(notes)
    
    # Update streak
    streak = Streak.get_or_create(request.user)
    streak.update_streak(session.start_time.date())
    
    # Check for achievements
    check_achievements(request.user, session)
    
    # Check if daily goal achieved
    daily_goal = DailyGoal.get_or_create_today(request.user)
    daily_goal.calculate_actual_duration()
    
    return JsonResponse({
        'success': True,
        'session_id': str(session.session_id),
        'duration_seconds': session.duration.total_seconds(),
        'subject': session.subject.name if session.subject else 'No Subject',
        'goal_achieved': daily_goal.achieved,
        'daily_progress': daily_goal.get_progress_percentage()
    })


@login_required
@require_GET
def get_timer_status(request):
    """Get current timer status"""
    timer = TimerSession.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('subject').first()
    
    if not timer:
        return JsonResponse({'active': False})
    
    return JsonResponse({
        'active': True,
        'timer_id': str(timer.session_id),
        'subject': timer.subject.name,
        'subject_color': timer.subject.color,
        'is_paused': timer.is_paused,
        'elapsed_seconds': timer.get_elapsed_time().total_seconds(),
        'start_time': timer.start_time.isoformat()
    })


def check_achievements(user, session=None):
    """Check and award achievements based on user activity"""
    today = timezone.now().date()
    
    # Get achievements that user doesn't have yet
    earned_achievements = UserAchievement.objects.filter(user=user).values_list(
        'achievement_id', flat=True
    )
    available_achievements = Achievement.objects.exclude(id__in=earned_achievements)
    
    new_achievements = []
    
    for achievement in available_achievements:
        should_award = False
        
        if achievement.badge_type == 'first_session':
            # First study session
            total_sessions = StudySession.objects.filter(user=user, status='completed').count()
            should_award = total_sessions >= 1
        
        elif achievement.badge_type == 'streak':
            # Streak achievements
            streak = Streak.get_or_create(user)
            required_days = int(achievement.requirement.split(':')[1]) if ':' in achievement.requirement else 7
            should_award = streak.current_streak >= required_days
        
        elif achievement.badge_type == 'goal':
            # Goal completion
            daily_goal = DailyGoal.get_or_create_today(user)
            should_award = daily_goal.achieved
        
        elif achievement.badge_type == 'study_time':
            # Total study time achievements
            total_seconds = StudySession.objects.filter(
                user=user, status='completed'
            ).aggregate(total=Sum('duration'))['total']
            total_seconds = total_seconds.total_seconds() if total_seconds else 0
            required_hours = int(achievement.requirement.split(':')[1]) if ':' in achievement.requirement else 10
            should_award = total_seconds >= (required_hours * 3600)
        
        if should_award:
            UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                notes=f'Awarded for: {achievement.requirement}'
            )
            new_achievements.append(achievement)
    
    return new_achievements


@login_required
def reports(request):
    """Reports and analytics view"""
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Get report type (daily, weekly, monthly)
    report_type = request.GET.get('type', 'daily')
    
    # Calculate total study time
    total_sessions = StudySession.objects.filter(user=request.user, status='completed')
    total_seconds = sum(s.duration.total_seconds() for s in total_sessions if s.duration)
    
    # Today's study time
    today_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date=today,
        status='completed'
    )
    today_seconds = sum(s.duration.total_seconds() for s in today_sessions if s.duration)
    
    # This week's study time
    week_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date__gte=start_of_week,
        status='completed'
    )
    week_seconds = sum(s.duration.total_seconds() for s in week_sessions if s.duration)
    
    # This month's study time
    month_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date__gte=start_of_month,
        status='completed'
    )
    month_seconds = sum(s.duration.total_seconds() for s in month_sessions if s.duration)
    
    # Get goals for comparison
    daily_goal = DailyGoal.get_or_create_today(request.user)
    weekly_goal = WeeklyGoal.get_or_create_current(request.user)
    monthly_goal = MonthlyGoal.get_or_create_current(request.user)
    
    # Calculate actual durations
    daily_goal.calculate_actual_duration()
    weekly_goal.calculate_actual_duration()
    monthly_goal.calculate_actual_duration()
    
    # Study by subject
    subjects_data = []
    for subject in Subject.objects.filter(user=request.user):
        subject_sessions = StudySession.objects.filter(
            user=request.user,
            subject=subject,
            status='completed'
        )
        subject_seconds = sum(s.duration.total_seconds() for s in subject_sessions if s.duration)
        if subject_seconds > 0:
            subjects_data.append({
                'name': subject.name,
                'color': subject.color,
                'seconds': subject_seconds,
                'percentage': round((subject_seconds / total_seconds * 100) if total_seconds > 0 else 0, 1)
            })
    
    # Daily breakdown for charts (last 7 days)
    daily_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_sessions = StudySession.objects.filter(
            user=request.user,
            start_time__date=date,
            status='completed'
        )
        day_seconds = sum(s.duration.total_seconds() for s in day_sessions if s.duration)
        daily_data.append({
            'date': date.strftime('%b %d'),
            'seconds': day_seconds,
            'hours': round(day_seconds / 3600, 1)
        })
    
    # Weekly breakdown (last 4 weeks)
    weekly_data = []
    for i in range(3, -1, -1):
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        week_sessions = StudySession.objects.filter(
            user=request.user,
            start_time__date__gte=week_start,
            start_time__date__lte=week_end,
            status='completed'
        )
        week_seconds_val = sum(s.duration.total_seconds() for s in week_sessions if s.duration)
        weekly_data.append({
            'week': f"Week {13-i}",
            'seconds': week_seconds_val,
            'hours': round(week_seconds_val / 3600, 1)
        })
    
    # Recent sessions
    recent_sessions = StudySession.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('subject')[:10]
    
    context = {
        'user': request.user,
        'report_type': report_type,
        'total_seconds': total_seconds,
        'today_seconds': today_seconds,
        'week_seconds': week_seconds,
        'month_seconds': month_seconds,
        'daily_goal': daily_goal,
        'weekly_goal': weekly_goal,
        'monthly_goal': monthly_goal,
        'subjects_data': subjects_data,
        'daily_data': daily_data,
        'weekly_data': weekly_data,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'tracker/reports.html', context)


@login_required
def export_pdf(request):
    """Export study reports as PDF"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    
    today = timezone.now().date()
    
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="study_report_{today}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    
    # Title
    elements.append(Paragraph("Study Time Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # User info
    user_info = f"<b>Student:</b> {request.user.username} | <b>Generated:</b> {today.strftime('%B %d, %Y')}"
    elements.append(Paragraph(user_info, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary statistics
    total_sessions = StudySession.objects.filter(user=request.user, status='completed')
    total_seconds = sum(s.duration.total_seconds() for s in total_sessions if s.duration)
    
    # Calculate daily, weekly, monthly
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    today_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date=today,
        status='completed'
    )
    today_seconds = sum(s.duration.total_seconds() for s in today_sessions if s.duration)
    
    week_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date__gte=start_of_week,
        status='completed'
    )
    week_seconds = sum(s.duration.total_seconds() for s in week_sessions if s.duration)
    
    month_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date__gte=start_of_month,
        status='completed'
    )
    month_seconds = sum(s.duration.total_seconds() for s in month_sessions if s.duration)
    
    def format_duration(seconds):
        """Format seconds as hours:minutes:seconds"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    # Summary table
    summary_data = [
        ['Period', 'Hours Studied'],
        ['Today', format_duration(today_seconds)],
        ['This Week', format_duration(week_seconds)],
        ['This Month', format_duration(month_seconds)],
        ['Total', format_duration(total_seconds)],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(Paragraph("Summary Statistics", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Study by subject
    subjects_data = []
    for subject in Subject.objects.filter(user=request.user):
        subject_sessions = StudySession.objects.filter(
            user=request.user,
            subject=subject,
            status='completed'
        )
        subject_seconds = sum(s.duration.total_seconds() for s in subject_sessions if s.duration)
        if subject_seconds > 0:
            subjects_data.append([subject.name, format_duration(subject_seconds)])
    
    if subjects_data:
        subjects_data.insert(0, ['Subject', 'Time Spent'])
        subjects_table = Table(subjects_data, colWidths=[3*inch, 2*inch])
        subjects_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(Paragraph("Study Time by Subject", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(subjects_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # Recent sessions
    recent_sessions = StudySession.objects.filter(
        user=request.user,
        status='completed'
    ).order_by('-start_time')[:15]
    
    if recent_sessions:
        sessions_data = [['Subject', 'Date', 'Duration']]
        for session in recent_sessions:
            sessions_data.append([
                str(session.subject) if session.subject else 'No Subject',
                session.start_time.strftime('%Y-%m-%d'),
                format_duration(session.duration.total_seconds() if session.duration else 0)
            ])
        
        sessions_table = Table(sessions_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        sessions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(Paragraph("Recent Study Sessions", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(sessions_table)
    
    # Build PDF
    doc.build(elements)
    
    return response


@login_required
def profile(request):
    """User profile view with edit functionality"""
    if request.method == 'POST':
        # Update user profile
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        
        # Check if email is already taken
        if email and email != request.user.email:
            if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                messages.error(request, 'This email is already in use.')
                return redirect('tracker:profile')
        
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('tracker:profile')
    
    context = {
        'user': request.user,
    }
    return render(request, 'tracker/profile.html', context)


@login_required
def settings_view(request):
    """User settings view with password change"""
    if request.method == 'POST':
        # Change password
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
        
        return redirect('tracker:settings')
    
    context = {
        'user': request.user,
    }
    return render(request, 'tracker/settings.html', context)


@login_required
def subjects(request):
    """Subject management view - list all subjects"""
    subjects = Subject.objects.filter(user=request.user).annotate(
        total_hours=Sum('sessions__duration'),
        session_count=Count('sessions')
    )
    
    # Convert timedelta to hours for display
    for subject in subjects:
        if subject.total_hours:
            subject.total_hours = round(subject.total_hours.total_seconds() / 3600, 1)
        else:
            subject.total_hours = 0
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        name = request.POST.get('name')
        color = request.POST.get('color', '#6366f1')
        description = request.POST.get('description', '')
        
        if subject_id:
            # Edit existing subject
            subject = get_object_or_404(Subject, id=subject_id, user=request.user)
            subject.name = name
            subject.color = color
            subject.description = description
            subject.save()
            messages.success(request, 'Subject updated successfully!')
        else:
            # Create new subject
            Subject.objects.create(
                user=request.user,
                name=name,
                color=color,
                description=description
            )
            messages.success(request, 'Subject created successfully!')
        
        return redirect('tracker:subjects')
    
    context = {
        'user': request.user,
        'subjects': subjects,
    }
    return render(request, 'tracker/subjects.html', context)


@login_required
def delete_subject(request, subject_id):
    """Delete a subject"""
    subject = get_object_or_404(Subject, id=subject_id, user=request.user)
    subject.delete()
    messages.success(request, 'Subject deleted successfully!')
    return redirect('tracker:subjects')


@login_required
def goals(request):
    """Goals management view - create, edit, delete daily, weekly, monthly goals"""
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Get all goals for the user
    daily_goals = DailyGoal.objects.filter(user=request.user).order_by('-date')[:4]
    weekly_goals = WeeklyGoal.objects.filter(user=request.user).order_by('-week_start')[:4]
    monthly_goals = MonthlyGoal.objects.filter(user=request.user).order_by('-year', '-month')[:4]
    
    # Calculate actual durations for each goal
    for goal in daily_goals:
        goal.calculate_actual_duration()
    for goal in weekly_goals:
        goal.calculate_actual_duration()
    for goal in monthly_goals:
        goal.calculate_actual_duration()
    
    # Handle goal creation/update
    if request.method == 'POST':
        goal_type = request.POST.get('goal_type_select') or request.POST.get('goal_type')
        goal_id = request.POST.get('goal_id')
        hours = float(request.POST.get('hours', 0))
        minutes = int(request.POST.get('minutes', 0))
        
        target_duration = timedelta(hours=hours, minutes=minutes)
        
        if goal_type == 'daily':
            if goal_id:
                # Edit existing goal
                goal = get_object_or_404(DailyGoal, id=goal_id, user=request.user)
                goal.target_duration = target_duration
                goal.save()
                messages.success(request, 'Daily goal updated successfully!')
            else:
                # Create new goal for today
                DailyGoal.objects.create(
                    user=request.user,
                    date=today,
                    target_duration=target_duration
                )
                messages.success(request, 'Daily goal created successfully!')
        elif goal_type == 'weekly':
            if goal_id:
                goal = get_object_or_404(WeeklyGoal, id=goal_id, user=request.user)
                goal.target_duration = target_duration
                goal.save()
                messages.success(request, 'Weekly goal updated successfully!')
            else:
                week_start = WeeklyGoal.get_current_week_start()
                WeeklyGoal.objects.get_or_create(
                    user=request.user,
                    week_start=week_start,
                    defaults={'target_duration': target_duration}
                )
                messages.success(request, 'Weekly goal created successfully!')
        elif goal_type == 'monthly':
            if goal_id:
                goal = get_object_or_404(MonthlyGoal, id=goal_id, user=request.user)
                goal.target_duration = target_duration
                goal.save()
                messages.success(request, 'Monthly goal updated successfully!')
            else:
                now = timezone.now()
                MonthlyGoal.objects.get_or_create(
                    user=request.user,
                    month=now.month,
                    year=now.year,
                    defaults={'target_duration': target_duration}
                )
                messages.success(request, 'Monthly goal created successfully!')
        
        return redirect('tracker:goals')
    
    # Get user achievements
    user_achievements = UserAchievement.objects.filter(
        user=request.user
    ).select_related('achievement')[:6]
    
    # Get all available achievements
    all_achievements = Achievement.objects.all()
    
    context = {
        'user': request.user,
        'daily_goals': daily_goals,
        'weekly_goals': weekly_goals,
        'monthly_goals': monthly_goals,
        'user_achievements': user_achievements,
        'all_achievements': all_achievements,
    }
    
    return render(request, 'tracker/goals.html', context)


@login_required
@require_POST
def delete_goal(request, goal_id):
    """Delete a goal"""
    # Try to find the goal in any of the goal models
    for model in [DailyGoal, WeeklyGoal, MonthlyGoal]:
        goal = model.objects.filter(id=goal_id, user=request.user).first()
        if goal:
            goal.delete()
            messages.success(request, 'Goal deleted successfully!')
            break
    
    return redirect('tracker:goals')


@login_required
def achievements_list(request):
    """View all achievements"""
    user_achievements = UserAchievement.objects.filter(
        user=request.user
    ).select_related('achievement')
    
    all_achievements = Achievement.objects.all()
    
    context = {
        'user_achievements': user_achievements,
        'all_achievements': all_achievements,
    }
    
    return render(request, 'tracker/achievements.html', context)


@login_required
def history(request):
    """Session history view"""
    # Get filter parameters
    subject_id = request.GET.get('subject')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    sessions = StudySession.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('subject')
    
    # Apply filters
    if subject_id:
        sessions = sessions.filter(subject_id=subject_id)
    if date_from:
        sessions = sessions.filter(start_time__date__gte=date_from)
    if date_to:
        sessions = sessions.filter(start_time__date__lte=date_to)
    
    # Pagination could be added here
    
    subjects = Subject.objects.filter(user=request.user)
    
    context = {
        'user': request.user,
        'sessions': sessions,
        'subjects': subjects,
        'selected_subject': subject_id,
    }
    
    return render(request, 'tracker/history.html', context)


@login_required
def delete_session(request, session_id):
    """Delete a study session"""
    session = get_object_or_404(StudySession, session_id=session_id, user=request.user)
    session.delete()
    messages.success(request, 'Session deleted successfully!')
    return redirect('tracker:history')


@login_required
def get_stats(request):
    """API endpoint to get real-time statistics"""
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Today's stats
    today_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date=today,
        status='completed'
    )
    today_seconds = sum(s.duration.total_seconds() for s in today_sessions if s.duration)
    
    # Week stats
    week_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date__gte=start_of_week,
        status='completed'
    )
    week_seconds = sum(s.duration.total_seconds() for s in week_sessions if s.duration)
    
    # Month stats
    month_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__date__gte=start_of_month,
        status='completed'
    )
    month_seconds = sum(s.duration.total_seconds() for s in month_sessions if s.duration)
    
    # Streak
    streak = Streak.get_or_create(request.user)
    
    # Daily goal progress
    daily_goal = DailyGoal.get_or_create_today(request.user)
    daily_goal.calculate_actual_duration()
    
    return JsonResponse({
        'today_seconds': today_seconds,
        'week_seconds': week_seconds,
        'month_seconds': month_seconds,
        'streak': streak.current_streak,
        'daily_progress': daily_goal.get_progress_percentage(),
        'daily_achieved': daily_goal.achieved,
    })