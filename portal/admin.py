from django.contrib import admin
from .models import Author, Category, Post, PostCategory, Comment

admin.site.register(Author)
admin.site.register(Category)
admin.site.register(Post)
admin.site.register(PostCategory)
admin.site.register(Comment)


from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'rating', 'created_at')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)

