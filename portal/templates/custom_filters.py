# from django import template
#
#
# register = template.Library()
#
#
# # Регистрируем наш фильтр под именем currency, чтоб Django понимал,
# # что это именно фильтр для шаблонов, а не простая функция.
# @register.filter()
# def currency(value):
#    """
#    value: значение, к которому нужно применить фильтр
#    """
#    # Возвращаемое функцией значение подставится в шаблон.
#    return f'{value} Р'

from django import template

register = template.Library()

BAD_WORDS = ['Борьба', 'Хабиб']

@register.filter(name='truncate_20')
def truncate_20(value):
    """
    Обрезает текст до 20 слов
    """
    if not value:
        return ''
    return ' '.join(value.split()[:20]) + '...'

@register.filter()
def censor(text):
    if not isinstance(text, str):
        return text

    for word in BAD_WORDS:
        text = text.replace(word, '*' * len(word))
    return text