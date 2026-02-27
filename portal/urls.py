from django.urls import path, include
from . import views
from .views import (
    IndexView, NewsList, NewsDetail, ArticleList, ArticleDetail,
    like_post, CategoryPosts, ProductList, ProductDetail,
    NewsSearchView, NewsCreateView, ArticleCreateView,
    PostUpdateView, upgrade, subscribe_category, unsubscribe_category, test_email_view
)

urlpatterns = [
    # Главная
    path('', IndexView.as_view(), name='home'),

    # Новости
    path('news/', NewsList.as_view(), name='news_list'),
    path('news/<int:pk>/', NewsDetail.as_view(), name='news_detail'),
    path('news/create/', NewsCreateView.as_view(), name='news_create'),
    path('news/<int:pk>/edit/', PostUpdateView.as_view(), name='post_edit'),
    path('news/<int:post_id>/like/', like_post, name='like_post'),

    # Статьи
    path('articles/', ArticleList.as_view(), name='article_list'),
    path('articles/<int:pk>/', ArticleDetail.as_view(), name='article_detail'),
    path('articles/create/', ArticleCreateView.as_view(), name='article_create'),

    # Категории
    path('category/<int:pk>/', CategoryPosts.as_view(), name='category_posts'),
    path('category/<int:pk>/subscribe/', subscribe_category, name='subscribe_category'),
    path('category/<int:pk>/unsubscribe/', unsubscribe_category, name='unsubscribe_category'),

    # Продукты
    path('products/', ProductList.as_view(), name='products_list'),
    path('products/<int:pk>/', ProductDetail.as_view(), name='product_detail'),

    # Поиск
    path('news/search/', NewsSearchView.as_view(), name='news_search'),

    # Авторизация и регистрация
    path('accounts/', include('allauth.urls')),

    # Upgrade route
    path('upgrade/', upgrade, name='upgrade'),
    path('words/', views.word_box_view, name='word_box'),
    path('test-email/', test_email_view, name='test-email'),
]

