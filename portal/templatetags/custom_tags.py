from datetime import datetime
from django import template

register = template.Library()

@register.simple_tag
def current_time(format_string="%d.%m.%Y"):
    return datetime.now().strftime(format_string)

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    ...
@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    return query.urlencode()