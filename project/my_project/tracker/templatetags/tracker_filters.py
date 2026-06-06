from django import template
from datetime import timedelta

register = template.Library()


@register.filter
def seconds_to_time(total_seconds):
    """Convert seconds to formatted time string (Xh Ym Zs)"""
    if total_seconds is None:
        return "0h 0m"
    
    try:
        total_seconds = float(total_seconds)
    except (ValueError, TypeError):
        return "0h 0m"
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


@register.filter
def duration_to_time(duration):
    """Convert timedelta to formatted time string"""
    if duration is None:
        return "0h 0m"
    
    if isinstance(duration, timedelta):
        total_seconds = int(duration.total_seconds())
        return seconds_to_time(total_seconds)
    
    return "0h 0m"


@register.filter
def format_duration(duration):
    """Format duration as HH:MM:SS"""
    if duration is None:
        return "00:00:00"
    
    if isinstance(duration, timedelta):
        total_seconds = int(duration.total_seconds())
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    return "00:00:00"


@register.filter
def modulo(a, b):
    """Modulo operation for template"""
    try:
        return float(a) % float(b)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)