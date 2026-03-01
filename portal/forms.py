from django import forms
from django.contrib.auth.models import User
from .models import Post, Category

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        if data is None:
            return []
        return [single_clean(data, initial)]


class PostForm(forms.ModelForm):
    images = MultiFileField(
        required=False,
        widget=MultiFileInput(attrs={
            'accept': 'image/png',
            'multiple': True,
        }),
        label='PNG файлы',
        help_text='Загрузите от 1 до 3 PNG-файлов',
    )

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
        self.require_images = kwargs.pop('require_images', False)
        self.max_images = kwargs.pop('max_images', 3)
        super().__init__(*args, **kwargs)
        self.fields['categories'].queryset = Category.objects.all()
        self.fields['categories'].help_text = "Выберите одну или несколько категорий для публикации"
        self.fields['categories'].label = "Категории"

    def clean_images(self):
        files = self.files.getlist('images')
        existing_count = self.instance.media_files.count() if self.instance and self.instance.pk else 0
        total = existing_count + len(files)

        if self.require_images and existing_count == 0 and len(files) == 0:
            raise forms.ValidationError('Нужно загрузить хотя бы 1 PNG файл.')

        if total > self.max_images:
            raise forms.ValidationError(f'Можно хранить максимум {self.max_images} PNG файла.')

        for file in files:
            if file.content_type != 'image/png':
                raise forms.ValidationError('Разрешены только PNG файлы.')
        return files


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя пользователя',
            }),
        }


class EmailChangeForm(forms.Form):
    email = forms.EmailField(
        label='Новый email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
        }),
    )
    password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите текущий пароль',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError('Этот email уже используется другим аккаунтом.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.user.check_password(password):
            raise forms.ValidationError('Неверный пароль.')
        return password
