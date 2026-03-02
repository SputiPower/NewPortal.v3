from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Author, Post


class PostApiSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.user.username', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'text', 'author', 'rating', 'created_at', 'type']
        read_only_fields = ['id', 'author', 'rating', 'created_at', 'type']

    def _get_author(self):
        user: User = self.context['request'].user
        author, _ = Author.objects.get_or_create(user=user)
        return author

    def create(self, validated_data):
        post_type = self.context.get('post_type')
        return Post.objects.create(
            author=self._get_author(),
            type=post_type,
            **validated_data,
        )

    def update(self, instance, validated_data):
        # type is bound to endpoint and cannot be switched via API payload.
        validated_data.pop('type', None)
        return super().update(instance, validated_data)

