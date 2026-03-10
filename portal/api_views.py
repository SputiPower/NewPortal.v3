from rest_framework import permissions, viewsets
from rest_framework.schemas.openapi import AutoSchema

from .api_serializers import PostApiSerializer
from .models import Post
from .views import exclude_system_generated_posts


class BasePostViewSet(viewsets.ModelViewSet):
    serializer_class = PostApiSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    post_type = None

    def get_queryset(self):
        queryset = Post.objects.filter(type=self.post_type).select_related('author__user').order_by('-created_at')
        return exclude_system_generated_posts(queryset)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['post_type'] = self.post_type
        return context

    def perform_update(self, serializer):
        serializer.save(type=self.post_type)


class NewsApiViewSet(BasePostViewSet):
    post_type = Post.NEWS
    schema = AutoSchema(operation_id_base='NewsApi')


class ArticleApiViewSet(BasePostViewSet):
    post_type = Post.ARTICLE
    schema = AutoSchema(operation_id_base='ArticlesApi')
