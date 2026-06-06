from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
import uuid


class Subject(models.Model):
    """Subject/Course model for categorizing study sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6366f1')  # Hex color code
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return self.name
    
    def get_total_study_time(self):
        """Get total study time for this subject"""
        total = StudySession.objects.filter(user=self.user, subject=self).aggregate(
            total=models.Sum('duration')
        )['total']
        return total if total else timedelta(0)
    
    def get_session_count(self):
        """Get number of study sessions for this subject"""
        return StudySession.objects.filter(user=self.user, subject=self).count()


class StudySession(models.Model):
    """Study session model for tracking study time"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, related_name='sessions')
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', '-start_time']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.subject} ({self.duration})"
    
    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            self.duration = self.end_time - self.start_time
        super().save(*args, **kwargs)
    
    @staticmethod
    def get_active_session(user):
        """Get the currently active session for a user"""
        return StudySession.objects.filter(
            user=user, 
            status='active'
        ).first()
    
    def calculate_duration(self):
        """Calculate duration from start and end time"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return timedelta(0)


class DailyGoal(models.Model):
    """Daily study goal model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_goals')
    date = models.DateField(default=timezone.now)
    target_duration = models.DurationField(default=timedelta(0))  # No default - user must set
    actual_duration = models.DurationField(default=timedelta(0))
    achieved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    def calculate_actual_duration(self):
        """Calculate total study time for the day"""
        sessions = StudySession.objects.filter(
            user=self.user,
            start_time__date=self.date,
            status='completed'
        )
        total = sum((s.duration for s in sessions if s.duration), timedelta(0))
        self.actual_duration = total
        self.achieved = total >= self.target_duration
        self.save()
        return total
    
    def get_progress_percentage(self):
        """Get progress as percentage"""
        if self.target_duration.total_seconds() == 0:
            return 0
        return min(100, (self.actual_duration.total_seconds() / self.target_duration.total_seconds()) * 100)
    
    @staticmethod
    def get_or_create_today(user):
        """Get or create today's goal"""
        today = timezone.now().date()
        goal, created = DailyGoal.objects.get_or_create(
            user=user,
            date=today,
            defaults={'target_duration': timedelta(0)}  # No default duration
        )
        return goal


class WeeklyGoal(models.Model):
    """Weekly study goal model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_goals')
    week_start = models.DateField()  # Monday of the week
    target_duration = models.DurationField(default=timedelta(0))  # No default - user must set
    actual_duration = models.DurationField(default=timedelta(0))
    achieved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-week_start']
        unique_together = ['user', 'week_start']
    
    def __str__(self):
        return f"{self.user.username} - Week of {self.week_start}"
    
    def calculate_actual_duration(self):
        """Calculate total study time for the week"""
        week_end = self.week_start + timedelta(days=6)
        sessions = StudySession.objects.filter(
            user=self.user,
            start_time__date__gte=self.week_start,
            start_time__date__lte=week_end,
            status='completed'
        )
        total = sum((s.duration for s in sessions if s.duration), timedelta(0))
        self.actual_duration = total
        self.achieved = total >= self.target_duration
        self.save()
        return total
    
    def get_progress_percentage(self):
        """Get progress as percentage"""
        if self.target_duration.total_seconds() == 0:
            return 0
        return min(100, (self.actual_duration.total_seconds() / self.target_duration.total_seconds()) * 100)
    
    @staticmethod
    def get_current_week_start():
        """Get the Monday of the current week"""
        today = timezone.now().date()
        return today - timedelta(days=today.weekday())
    
    @staticmethod
    def get_or_create_current(user):
        """Get or create current week's goal"""
        week_start = WeeklyGoal.get_current_week_start()
        goal, created = WeeklyGoal.objects.get_or_create(
            user=user,
            week_start=week_start,
            defaults={'target_duration': timedelta(0)}  # No default duration
        )
        return goal


class MonthlyGoal(models.Model):
    """Monthly study goal model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_goals')
    month = models.IntegerField(default=1)  # 1-12
    year = models.IntegerField(default=2024)
    target_duration = models.DurationField(default=timedelta(0))  # No default - user must set
    actual_duration = models.DurationField(default=timedelta(0))
    achieved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year}"
    
    def calculate_actual_duration(self):
        """Calculate total study time for the month"""
        from datetime import date
        # Get first and last day of month
        if self.month == 12:
            next_month = date(self.year + 1, 1, 1)
        else:
            next_month = date(self.year, self.month + 1, 1)
        
        first_day = date(self.year, self.month, 1)
        last_day = next_month - timedelta(days=1)
        
        sessions = StudySession.objects.filter(
            user=self.user,
            start_time__date__gte=first_day,
            start_time__date__lte=last_day,
            status='completed'
        )
        total = sum((s.duration for s in sessions if s.duration), timedelta(0))
        self.actual_duration = total
        self.achieved = total >= self.target_duration
        self.save()
        return total
    
    def get_progress_percentage(self):
        """Get progress as percentage"""
        if self.target_duration.total_seconds() == 0:
            return 0
        return min(100, (self.actual_duration.total_seconds() / self.target_duration.total_seconds()) * 100)
    
    @staticmethod
    def get_or_create_current(user):
        """Get or create current month's goal"""
        now = timezone.now()
        goal, created = MonthlyGoal.objects.get_or_create(
            user=user,
            month=now.month,
            year=now.year,
            defaults={'target_duration': timedelta(0)}  # No default duration
        )
        return goal


class Achievement(models.Model):
    """Achievement/Badge model for gamification"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🏆')  # Emoji icon
    requirement = models.TextField()  # Description of how to earn
    points = models.IntegerField(default=10)
    badge_type = models.CharField(max_length=50, default='general')  # general, streak, goal, study_time
    
    class Meta:
        ordering = ['points']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class UserAchievement(models.Model):
    """Tracks which achievements a user has earned"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-earned_at']
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class Streak(models.Model):
    """Tracks user study streaks"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streaks')
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Current: {self.current_streak}, Best: {self.best_streak}"
    
    def update_streak(self, study_date):
        """Update streak based on study date"""
        if self.last_study_date is None:
            self.current_streak = 1
        elif study_date == self.last_study_date:
            pass  # Already counted today
        elif study_date == self.last_study_date + timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1
        
        self.last_study_date = study_date
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
        
        self.save()
        return self.current_streak
    
    @staticmethod
    def get_or_create(user):
        """Get or create streak for user"""
        streak, created = Streak.objects.get_or_create(user=user)
        return streak


class TimerSession(models.Model):
    """Active timer session for real-time tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timer_sessions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timer_sessions')
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    paused_time = models.DateTimeField(null=True, blank=True)
    total_paused_duration = models.DurationField(default=timedelta(0))
    is_paused = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.subject} (Active: {self.is_active})"
    
    def get_elapsed_time(self):
        """Get total elapsed time accounting for pauses"""
        if self.is_paused and self.paused_time:
            return self.paused_time - self.start_time - self.total_paused_duration
        elif self.is_active:
            return timezone.now() - self.start_time - self.total_paused_duration
        return timedelta(0)
    
    def pause(self):
        """Pause the timer"""
        self.is_paused = True
        self.paused_time = timezone.now()
        self.save()
    
    def resume(self):
        """Resume the timer"""
        if self.is_paused and self.paused_time:
            pause_duration = timezone.now() - self.paused_time
            self.total_paused_duration += pause_duration
        self.is_paused = False
        self.paused_time = None
        self.save()
    
    def complete(self, notes=''):
        """Complete the timer and create a study session"""
        self.is_active = False
        self.is_paused = False
        self.notes = notes
        self.save()
        
        # Create actual study session
        end_time = timezone.now()
        duration = end_time - self.start_time - self.total_paused_duration
        
        session = StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            start_time=self.start_time,
            end_time=end_time,
            duration=duration,
            notes=notes,
            status='completed'
        )
        
        return session