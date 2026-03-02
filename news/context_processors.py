from django.utils import timezone


def localization_context(request):
    selected_timezone = request.session.get(
        'django_timezone',
        timezone.get_current_timezone_name(),
    )
    local_now = timezone.localtime(timezone.now())
    is_night_theme = local_now.hour >= 19 or local_now.hour < 7

    timezone_choices = [
        'Europe/Moscow',
        'Europe/Kaliningrad',
        'UTC',
        'Europe/London',
        'America/New_York',
        'Asia/Tokyo',
    ]

    return {
        'selected_timezone': selected_timezone,
        'timezone_choices': timezone_choices,
        'is_night_theme': is_night_theme,
    }

