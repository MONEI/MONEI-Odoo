from datetime import datetime, timedelta
import pytz
from odoo import fields

def get_user_datetime(dt=None):
    """Convert UTC datetime to user's timezone
    Uses the timezone from the current user's context or UTC if not set
    """
    if not dt:
        dt = fields.Datetime.now()
    
    # Get timezone from context or default to UTC
    from odoo.http import request
    user_tz = pytz.timezone(request.env.user.tz if request and request.env.user.tz else 'UTC')
    
    # Make sure dt is timezone naive
    if hasattr(dt, 'tzinfo') and dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    return user_tz.localize(dt.replace(tzinfo=None)).astimezone(user_tz)

def get_utc_datetime(dt):
    """Convert user's timezone datetime back to UTC"""
    # Get timezone from context or default to UTC
    from odoo.http import request
    user_tz = pytz.timezone(request.env.user.tz if request and request.env.user.tz else 'UTC')
    
    # Make sure dt is timezone naive before localizing
    if hasattr(dt, 'tzinfo') and dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    local_dt = user_tz.localize(dt)
    return local_dt.astimezone(pytz.UTC).replace(tzinfo=None)

def get_today_date_range():
    """Get date range for today (00:00:00 to now)"""
    user_now = get_user_datetime()
    today_start = user_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return get_utc_datetime(today_start), fields.Datetime.now()

def get_yesterday_date_range():
    """Get date range for yesterday (00:00:00 to now)"""
    user_now = get_user_datetime()
    yesterday = user_now - timedelta(days=1)
    yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    return get_utc_datetime(yesterday_start), fields.Datetime.now()

def get_week_date_range():
    """Get date range for current week (Monday 00:00:00 to now)"""
    user_now = get_user_datetime()
    monday = user_now - timedelta(days=user_now.weekday())
    week_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return get_utc_datetime(week_start), fields.Datetime.now()

def get_month_date_range():
    """Get date range for current month (1st 00:00:00 to now)"""
    user_now = get_user_datetime()
    month_start = user_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return get_utc_datetime(month_start), fields.Datetime.now() 