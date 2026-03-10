from django.core.paginator import InvalidPage
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .filters import ProductFilter
from .forms import ProductForm
from .models import Product


class ProductsList(ListView):
    model = Product
    template_name = 'simpleapp/product_list.html'
    context_object_name = 'products'
    paginate_by = 6

    def get_queryset(self):
        queryset = Product.objects.select_related('category').order_by('-id')
        self.filterset = ProductFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context

    def paginate_queryset(self, queryset, page_size):
        try:
            return super().paginate_queryset(queryset, page_size)
        except InvalidPage:
            raise Http404('Invalid page')


class ProductDetail(DetailView):
    model = Product
    template_name = 'simpleapp/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.select_related('category')


class ProductCreate(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'simpleapp/product_form.html'
    success_url = reverse_lazy('product_list')


class ProductUpdate(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'simpleapp/product_form.html'
    success_url = reverse_lazy('product_list')


class ProductDelete(DeleteView):
    model = Product
    template_name = 'simpleapp/product_delete.html'
    success_url = reverse_lazy('product_list')
