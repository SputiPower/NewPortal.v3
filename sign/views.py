from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from portal.models import Post, Author


# 🔹 Стать автором
@login_required
def become_author(request):
    authors_group = Group.objects.get(name='authors')
    authors_group.user_set.add(request.user)

    # создаём объект Author если его нет
    Author.objects.get_or_create(user=request.user)

    return redirect('/')


# 🔹 Создание поста
class PostCreateView(PermissionRequiredMixin, CreateView):
    model = Post
    fields = ['type', 'title', 'text', 'image']
    template_name = 'sign/post_form.html'
    success_url = reverse_lazy('news_list')

    permission_required = ('news.add_post',)

    def form_valid(self, form):
        author = Author.objects.get(user=self.request.user)
        form.instance.author = author
        return super().form_valid(form)


# 🔹 Редактирование поста
class PostUpdateView(PermissionRequiredMixin, UpdateView):
    model = Post
    fields = ['type', 'title', 'text', 'image']
    template_name = 'post_form.html'
    success_url = reverse_lazy('news_list')

    permission_required = ('news.change_post',)
