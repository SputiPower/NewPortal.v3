from rest_framework import permissions, viewsets
from rest_framework.schemas.openapi import AutoSchema

from .api_serializers import PostApiSerializer
from .models import Post


class BasePostViewSet(viewsets.ModelViewSet):
    serializer_class = PostApiSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    post_type = None

    def get_queryset(self):
        return Post.objects.filter(type=self.post_type).select_related('author__user')

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
