from datetime import datetime, timedelta

from dateparser import parse as parse_date
from django import template
from django.utils import timezone
from humanize import naturaltime


register = template.Library()


@register.filter(name="relativetime")
def relativetime(value: datetime):
    if value.tzinfo is None:
        delta = datetime.now() - value
    else:
        delta = timezone.now() - value
    return naturaltime(delta)


@register.simple_tag
def conditionaltime(value: datetime, interval: str, side_a: str, side_b: str):
    if value is None:
        return side_a

    dt = parse_date(interval)
    if value < dt:
        return side_a
    else:
        return side_b
