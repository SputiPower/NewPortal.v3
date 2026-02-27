from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    request = context['request']
    dict_ = request.GET.copy()

    for key, value in kwargs.items():
        dict_[key] = value

    return dict_.urlencode()

@register.filter()
def censor(value):
    # простая заглушка: заменим плохие слова на ***
    bad_words = ['плохое_слово1', 'плохое_слово2']
    for word in bad_words:
        value = value.replace(word, '***')
    return value
