from django.urls import path, include
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.contrib.auth import views as auth_views
from rest_framework.routers import SimpleRouter
from . import views
from .api_views import NewsApiViewSet, ArticleApiViewSet
from .views import (
    IndexView, NewsList, NewsDetail, ArticleList, ArticleDetail,
    like_post, CategoryPosts, ProductList, ProductDetail,
    NewsSearchView, NewsCreateView, ArticleCreateView,
    PostUpdateView, upgrade, subscribe_category, unsubscribe_category, test_email_view,
    profile_view, SmartFeedView, react_post, subscribe_author, unsubscribe_author,
    UserPasswordChangeView, change_email_view, set_timezone_view,
    PWSignupView, PWVerifyEmailCodeView, PWAdListView, PWAdDetailView,
    PWAdCreateView, PWAdUpdateView, PWAdDeleteView, create_ad_response,
    MyAdResponsesView, accept_ad_response, delete_ad_response,
)

api_router = SimpleRouter(trailing_slash=False)
api_router.register(r'news', NewsApiViewSet, basename='api-news')
api_router.register(r'articles', ArticleApiViewSet, basename='api-articles')

urlpatterns = [
    # REST API (without trailing slash): /news, /articles
    path('', include(api_router.urls)),

    # Главная
    path('', cache_page(60)(vary_on_cookie(IndexView.as_view())), name='home'),

    # Новости
    path('news/', cache_page(60 * 5)(vary_on_cookie(NewsList.as_view())), name='news_list'),
    path('news/<int:pk>/', cache_page(60 * 5)(vary_on_cookie(NewsDetail.as_view())), name='news_detail'),
    path('news/create/', NewsCreateView.as_view(), name='news_create'),
    path('news/<int:pk>/edit/', PostUpdateView.as_view(), name='post_edit'),
    path('news/<int:post_id>/like/', like_post, name='like_post'),

    # Статьи
    path('articles/', ArticleList.as_view(), name='article_list'),
    path('articles/<int:pk>/', ArticleDetail.as_view(), name='article_detail'),
    path('articles/create/', ArticleCreateView.as_view(), name='article_create'),

    # Категории
    path('category/<int:pk>/', cache_page(60 * 5)(vary_on_cookie(CategoryPosts.as_view())), name='category_posts'),
    path('category/<int:pk>/subscribe/', subscribe_category, name='subscribe_category'),
    path('category/<int:pk>/unsubscribe/', unsubscribe_category, name='unsubscribe_category'),
    path('author/<int:author_id>/subscribe/', subscribe_author, name='subscribe_author'),
    path('author/<int:author_id>/unsubscribe/', unsubscribe_author, name='unsubscribe_author'),

    # Реакции
    path('posts/<int:post_id>/react/', react_post, name='react_post'),

    # Профиль / безопасность / лента
    path('profile/', profile_view, name='profile'),
    path('profile/security/password/', UserPasswordChangeView.as_view(), name='password_change'),
    path('profile/security/email/', change_email_view, name='email_change'),
    path('set-timezone/', set_timezone_view, name='set_timezone'),
    path('feed/', SmartFeedView.as_view(), name='smart_feed'),

    # Продукты
    path('products/', ProductList.as_view(), name='products_list'),
    path('products/<int:pk>/', ProductDetail.as_view(), name='product_detail'),

    # Поиск
    path('news/search/', cache_page(60 * 5)(vary_on_cookie(NewsSearchView.as_view())), name='news_search'),

    # Авторизация и регистрация
    path('accounts/', include('allauth.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Upgrade route
    path('upgrade/', upgrade, name='upgrade'),
    path('words/', views.word_box_view, name='word_box'),
    path('test-email/', test_email_view, name='test-email'),

    # Perfect World board
    path('pw/signup/', PWSignupView.as_view(), name='pw_signup'),
    path('pw/verify-email/', PWVerifyEmailCodeView.as_view(), name='pw_verify_email'),
    path('pw/login/', auth_views.LoginView.as_view(template_name='pw/login.html'), name='pw_login'),
    path('pw/logout/', auth_views.LogoutView.as_view(next_page='pw_ad_list'), name='pw_logout'),
    path('pw/', PWAdListView.as_view(), name='pw_ad_list'),
    path('pw/ads/<int:pk>/', PWAdDetailView.as_view(), name='pw_ad_detail'),
    path('pw/ads/create/', PWAdCreateView.as_view(), name='pw_ad_create'),
    path('pw/ads/<int:pk>/edit/', PWAdUpdateView.as_view(), name='pw_ad_edit'),
    path('pw/ads/<int:pk>/delete/', PWAdDeleteView.as_view(), name='pw_ad_delete'),
    path('pw/ads/<int:pk>/response/', create_ad_response, name='pw_ad_response_create'),
    path('pw/responses/', MyAdResponsesView.as_view(), name='pw_my_responses'),
    path('pw/responses/<int:pk>/accept/', accept_ad_response, name='pw_response_accept'),
    path('pw/responses/<int:pk>/delete/', delete_ad_response, name='pw_response_delete'),
]

