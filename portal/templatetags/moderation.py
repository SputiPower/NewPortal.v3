from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from html.parser import HTMLParser
from urllib.parse import urlparse
import re

register = template.Library()

forbidden_words = [
    'плохое',
    'нежелательное',
    'спам',
]


_SCRIPT_STYLE_RE = re.compile(r'(?is)<(script|style)\b.*?>.*?</\1>')
_COMMENT_RE = re.compile(r'(?is)<!--.*?-->')

_ALLOWED_TAGS = {
    'p', 'br', 'strong', 'em', 'b', 'i', 'u',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
    'h1', 'h2', 'h3', 'h4', 'a', 'img',
}
_VOID_TAGS = {'br', 'img'}
_ALLOWED_ATTRS = {
    'a': {'href', 'title', 'target', 'rel'},
    'img': {'src', 'alt', 'title'},
}
_ALLOWED_SCHEMES = {'http', 'https', 'mailto'}


def _is_safe_url(url_value):
    if not url_value:
        return False
    parsed = urlparse(url_value)
    if parsed.scheme and parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        return False
    if url_value.strip().lower().startswith(('javascript:', 'data:', 'vbscript:')):
        return False
    return True


class _HTMLWhitelistSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in _ALLOWED_TAGS:
            return

        safe_attrs = []
        allowed_for_tag = _ALLOWED_ATTRS.get(tag, set())
        for key, value in attrs:
            if key not in allowed_for_tag:
                continue
            if key in {'href', 'src'} and not _is_safe_url(value):
                continue
            safe_attrs.append((key, value or ''))

        if tag == 'a':
            attr_keys = {key for key, _ in safe_attrs}
            if any(key == 'target' and value == '_blank' for key, value in safe_attrs):
                if 'rel' not in attr_keys:
                    safe_attrs.append(('rel', 'noopener noreferrer'))

        rendered_attrs = ''.join(f' {key}="{escape(value)}"' for key, value in safe_attrs)
        if tag in _VOID_TAGS:
            self.parts.append(f'<{tag}{rendered_attrs}>')
        else:
            self.parts.append(f'<{tag}{rendered_attrs}>')

    def handle_endtag(self, tag):
        if tag in _ALLOWED_TAGS and tag not in _VOID_TAGS:
            self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        self.parts.append(escape(data))

    def handle_entityref(self, name):
        self.parts.append(f'&{name};')

    def handle_charref(self, name):
        self.parts.append(f'&#{name};')


@register.filter
def sanitize_rich_html(value):
    """
    Sanitize user-provided rich HTML with a strict whitelist.
    Keeps basic formatting while removing executable markup.
    """
    if not isinstance(value, str):
        return value
    cleaned = _SCRIPT_STYLE_RE.sub('', value)
    cleaned = _COMMENT_RE.sub('', cleaned)

    parser = _HTMLWhitelistSanitizer()
    parser.feed(cleaned)
    parser.close()
    return mark_safe(''.join(parser.parts))


@register.filter
def hide_forbidden(value):
    """
    Replaces inner letters with '*' for words in forbidden_words.
    Keeps first/last character intact for matched words.
    """
    if not isinstance(value, str):
        return value

    words = value.split()
    result = []
    forbidden_set = {word.lower() for word in forbidden_words}

    for word in words:
        normalized = word.lower()
        if normalized in forbidden_set and len(word) > 2:
            result.append(word[0] + "*" * (len(word) - 2) + word[-1])
        elif normalized in forbidden_set and len(word) <= 2:
            result.append("*" * len(word))
        else:
            result.append(word)

    return " ".join(result)
