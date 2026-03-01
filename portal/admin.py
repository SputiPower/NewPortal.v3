from django.contrib import admin
from .models import Author, Category, Post, PostCategory, Comment, PostMedia, Subscription, Reaction


class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'author', 'created_at', 'rating')
    list_filter = ('type', 'created_at', 'categories')
    search_fields = ('title', 'text', 'author__user__username')
    inlines = [PostMediaInline]


admin.site.register(Author)
admin.site.register(Category)
admin.site.register(PostCategory)
admin.site.register(Comment)
admin.site.register(PostMedia)
admin.site.register(Subscription)
admin.site.register(Reaction)


from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'rating', 'created_at')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)

