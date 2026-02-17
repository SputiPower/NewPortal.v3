from django import template

register = template.Library()

# Список "плохих" слов, которые будем заменять на *
BAD_WORDS = ['плохое', 'нежелательное', 'спам' 'Ниггер' 'Пидорас' 'ЛГБТ']  # добавь свои слова

@register.filter(name='censor')
def censor(value):
    """
    Заменяет все буквы в плохих словах на '*'.
    """
    if not isinstance(value, str):
        return value
    for word in BAD_WORDS:
        value = value.replace(word, '*' * len(word))
    return value
