from django import forms
from django_filters import FilterSet, CharFilter, NumberFilter, DateFilter
from .models import Post, Product

class PostFilter(FilterSet):
    title = CharFilter(field_name='title', lookup_expr='icontains', label='Заголовок')
    author__user__username = CharFilter(field_name='author__user__username', lookup_expr='icontains', label='Автор')
    created_at = DateFilter(
        field_name='created_at',
        lookup_expr='gt',
        label='Дата после',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Post
        fields = []


class ProductFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains', label='Название')
    price_min = NumberFilter(field_name='price', lookup_expr='gte', label='Цена от')
    price_max = NumberFilter(field_name='price', lookup_expr='lte', label='Цена до')

    class Meta:
        model = Product
        fields = []

