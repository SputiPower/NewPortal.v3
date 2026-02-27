from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from .models import Post, Category, Author, Product
from .forms import PostForm
from .filters import PostFilter, ProductFilter


# ----------------- UPGRADE ДО АВТОРА -----------------
@login_required
def upgrade(request):
    authors_group, _ = Group.objects.get_or_create(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        request.user.groups.add(authors_group)
    return redirect(reverse('home'))


# ----------------- ПОДПИСКА НА КАТЕГОРИЮ -----------------
@login_required
def subscribe_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST" and request.user not in category.subscribers.all():
        category.subscribers.add(request.user)
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


# ----------------- ОТПИСКА ОТ КАТЕГОРИИ -----------------
@login_required
def unsubscribe_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST" and request.user in category.subscribers.all():
        category.subscribers.remove(request.user)
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


# ----------------- ГЛАВНАЯ СТРАНИЦА -----------------
class IndexView(TemplateView):
    template_name = 'portal/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_not_author'] = True
        if user.is_authenticated:
            context['is_not_author'] = not user.groups.filter(name='authors').exists()
        context['latest_news'] = Post.objects.filter(type='NW').order_by('-created_at')[:8]
        context['latest_articles'] = Post.objects.filter(type='AR').order_by('-created_at')[:8]
        return context


# ----------------- BASE POST -----------------
class BasePostListView(ListView):
    paginate_by = 10
    context_object_name = 'posts'
    filter_class = None
    type_filter = None

    def get_queryset(self):
        queryset = Post.objects.all()
        if self.type_filter:
            queryset = queryset.filter(type=self.type_filter)
        if self.filter_class:
            self.filterset = self.filter_class(self.request.GET, queryset)
            return self.filterset.qs.order_by('-created_at')
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        if hasattr(self, 'filterset'):
            context['filterset'] = self.filterset
        return context


# ----------------- NEWS -----------------
class NewsList(BasePostListView):
    template_name = 'news/news_list.html'
    context_object_name = 'news'
    type_filter = 'NW'
    filter_class = PostFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # добавляем идентификаторы категорий, на которые подписан пользователь
        if self.request.user.is_authenticated:
            context['subscriber_category_ids'] = list(
                self.request.user.subscribed_categories.values_list('id', flat=True)
            )
        else:
            context['subscriber_category_ids'] = []
        return context


class CategoryPosts(NewsList):
    template_name = 'news/category_posts.html'
    
    def get_queryset(self):
        category_id = self.kwargs['pk']
        queryset = super().get_queryset()
        return queryset.filter(categories__id=category_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(Category, id=self.kwargs['pk'])
        context['current_category'] = category
        context['subscriber_ids'] = list(category.subscribers.values_list('pk', flat=True))
        context['categories'] = Category.objects.all()
        return context


class NewsDetail(DetailView):
    model = Post
    template_name = 'news/news_detail.html'
    context_object_name = 'news_item'

    def get_queryset(self):
        return Post.objects.filter(type='NW')


# ----------------- ARTICLES -----------------
class ArticleList(BasePostListView):
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 5
    type_filter = 'AR'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(title__icontains=query)
        return queryset


class ArticleDetail(DetailView):
    model = Post
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Post.objects.filter(type='AR')


# ----------------- CREATE POST -----------------
class NewsCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'portal/post_create.html'
    success_url = reverse_lazy('news_list')

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

    def form_valid(self, form):
        # ограничение: не больше трёх новостей за последние 24 часа
        author, _ = Author.objects.get_or_create(user=self.request.user)
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=1)
        recent_count = Post.objects.filter(
            author=author, type='NW', created_at__gte=cutoff
        ).count()
        if recent_count >= 3:
            form.add_error(None, 'Вы уже опубликовали 3 новости за последние 24 часа')
            return self.form_invalid(form)

        form.instance.author = author
        form.instance.type = 'NW'
        # письмо рассылки теперь обрабатывается в методе save модели
        return super().form_valid(form)


class ArticleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'portal/post_create.html'
    success_url = reverse_lazy('article_list')

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

    def form_valid(self, form):
        author, _ = Author.objects.get_or_create(user=self.request.user)
        form.instance.author = author
        form.instance.type = 'AR'
        return super().form_valid(form)


# ----------------- UPDATE POST -----------------
class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'portal/post_edit.html'
    success_url = reverse_lazy('news_list')

    def get_queryset(self):
        return Post.objects.filter(author__user=self.request.user)


# ----------------- DELETE POST -----------------
class NewsDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'portal/post_delete.html'
    success_url = reverse_lazy('news_list')

    def get_queryset(self):
        return Post.objects.filter(type='NW')


# ----------------- LIKE -----------------
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.like()
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ----------------- PRODUCTS -----------------
class ProductList(ListView):
    model = Product
    template_name = 'products/products_list.html'
    context_object_name = 'products'
    paginate_by = 6

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-id')
        self.filterset = ProductFilter(self.request.GET or None, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        context['categories'] = Category.objects.all()
        return context


class ProductDetail(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.all()


# ----------------- NEWS SEARCH -----------------
class NewsSearchView(BasePostListView):
    template_name = 'news/news_search.html'
    context_object_name = 'news'
    type_filter = 'NW'
    filter_class = PostFilter
    paginate_by = 10


# ----------------- STATIC / TEST -----------------
def word_box_view(request):
    return render(request, 'portal/word_box.html')


from .utils import send_test_email
def test_email_view(request):
    send_test_email()  # отправка в фоне
    return render(request, "portal/test_email.html", {"message": "✅ Письмо отправляется в фоне! Проверь почту через несколько секунд."})