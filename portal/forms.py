from django import forms
from .models import Post, Category

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'type', 'categories']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Введите заголовок статьи',
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Введите текст новости или статьи',
            }),
            'type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'category-checkboxes',
            }),
        }

    def __init__(self, *args, **kwargs):
        """Добавим красивое отображение категорий с цветом и возможность подписки"""
        super().__init__(*args, **kwargs)
        self.fields['categories'].queryset = Category.objects.all()
        self.fields['categories'].help_text = "Выберите одну или несколько категорий для публикации"
        self.fields['categories'].label = "Категории"