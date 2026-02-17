from django.urls import path
from .views import become_author, PostCreateView, PostUpdateView

urlpatterns = [
    path('become_author/', become_author, name='become_author'),
    path('post/create/', PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/edit/', PostUpdateView.as_view(), name='post_edit'),
]
