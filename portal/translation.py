from modeltranslation.translator import TranslationOptions, register

from .models import Category, Post


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = ('title', 'text')

