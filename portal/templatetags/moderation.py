from django import template

register = template.Library()

forbidden_words = [
    'плохое',
    'нежелательное',
    'спам',
]


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

