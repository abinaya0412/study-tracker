from django.contrib import admin
from .models import (
    Subject, StudySession, DailyGoal, WeeklyGoal, MonthlyGoal,
    Achievement, UserAchievement, Streak, TimerSession
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color', 'created_at']
    list_filter = ['user', 'color']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'start_time', 'end_time', 'duration', 'status']
    list_filter = ['user', 'subject', 'status', 'start_time']
    search_fields = ['user__username', 'subject__name', 'notes']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    date_hierarchy = 'start_time'


@admin.register(DailyGoal)
class DailyGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'target_duration', 'actual_duration', 'achieved']
    list_filter = ['user', 'date', 'achieved']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'


@admin.register(WeeklyGoal)
class WeeklyGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'week_start', 'target_duration', 'actual_duration', 'achieved']
    list_filter = ['user', 'achieved']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MonthlyGoal)
class MonthlyGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'month', 'year', 'target_duration', 'actual_duration', 'achieved']
    list_filter = ['user', 'year', 'month', 'achieved']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'badge_type', 'points']
    list_filter = ['badge_type']
    search_fields = ['name', 'description', 'requirement']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['user', 'achievement__badge_type']
    search_fields = ['user__username', 'achievement__name']
    readonly_fields = ['earned_at']


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_streak', 'best_streak', 'last_study_date']
    list_filter = ['current_streak', 'best_streak']
    search_fields = ['user__username']
    readonly_fields = ['updated_at']


@admin.register(TimerSession)
class TimerSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'start_time', 'is_active', 'is_paused']
    list_filter = ['user', 'is_active', 'is_paused']
    search_fields = ['user__username', 'subject__name']
    readonly_fields = ['session_id', 'start_time']