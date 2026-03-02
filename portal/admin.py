from django.contrib import admin

from .models import (
    Author,
    Category,
    Comment,
    Post,
    PostCategory,
    PostMedia,
    Product,
    Reaction,
    Subscription,
)


class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 0


@admin.action(description='Сбросить рейтинг у выбранных постов')
def reset_post_rating(modeladmin, request, queryset):
    queryset.update(rating=0)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'type', 'author', 'created_at', 'rating')
    list_filter = ('type', 'created_at', 'categories')
    search_fields = ('title', 'text', 'author__user__username', 'categories__name')
    date_hierarchy = 'created_at'
    list_select_related = ('author',)
    inlines = [PostMediaInline]
    actions = [reset_post_rating]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'rating', 'instagram', 'telegram')
    list_filter = ('rating',)
    search_fields = ('user__username', 'user__email', 'instagram', 'telegram')
    list_select_related = ('user',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'subscribers_count')
    list_filter = ('color',)
    search_fields = ('name',)

    @staticmethod
    def subscribers_count(obj):
        return obj.subscribers.count()


@admin.register(PostCategory)
class PostCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'category')
    list_filter = ('category',)
    search_fields = ('post__title', 'category__name')
    list_select_related = ('post', 'category')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'created_at', 'rating', 'short_text')
    list_filter = ('created_at', 'rating')
    search_fields = ('text', 'user__username', 'post__title')
    date_hierarchy = 'created_at'
    list_select_related = ('post', 'user')

    @staticmethod
    def short_text(obj):
        return obj.text[:60]


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'created_at', 'image')
    list_filter = ('created_at',)
    search_fields = ('post__title',)
    date_hierarchy = 'created_at'
    list_select_related = ('post',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'author', 'created_at')
    list_filter = ('created_at', 'category', 'author')
    search_fields = ('user__username', 'category__name', 'author__user__username')
    date_hierarchy = 'created_at'
    list_select_related = ('user', 'category', 'author__user')


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'reaction_type', 'created_at', 'updated_at')
    list_filter = ('reaction_type', 'created_at', 'updated_at')
    search_fields = ('user__username', 'post__title')
    date_hierarchy = 'created_at'
    list_select_related = ('user', 'post')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'rating', 'created_at', 'updated_at')
    list_filter = ('category', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'category__name')
    date_hierarchy = 'created_at'
    list_select_related = ('category',)
