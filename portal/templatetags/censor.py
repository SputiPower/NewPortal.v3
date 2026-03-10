from django import template
from django.utils.html import strip_tags
import html
import re

register = template.Library()

# Список "плохих" слов, которые будем заменять на *
BAD_WORDS = ('плохое', 'нежелательное', 'спам', 'Ниггер', 'Пидорас', 'ЛГБТ')  # добавь свои слова
BR_RE = re.compile(r'(?i)<\s*br\s*/?\s*>')
P_CLOSE_RE = re.compile(r'(?i)</\s*p\s*>')
P_OPEN_RE = re.compile(r'(?i)<\s*p(?:\s+[^>]*)?>')
MULTI_NL_RE = re.compile(r'\n{3,}')

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


@register.filter(name='render_post_text')
def render_post_text(value):
    """
    Нормализует legacy HTML-текст поста в чистый читаемый текст:
    - декодирует HTML entities,
    - превращает <br> в перенос строки,
    - превращает </p> в абзацный разрыв,
    - убирает прочие теги.
    """
    if not isinstance(value, str):
        return value

    text = html.unescape(value)
    text = BR_RE.sub('\n', text)
    text = P_CLOSE_RE.sub('\n\n', text)
    text = P_OPEN_RE.sub('', text)
    text = strip_tags(text)
    text = MULTI_NL_RE.sub('\n\n', text)
    return text.strip()
