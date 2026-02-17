from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Добавляет CSS-класс к полю формы, чтобы использовать с Bootstrap
    Пример в шаблоне: {{ field|add_class:"form-control" }}
    """
    return field.as_widget(attrs={"class": css_class})

