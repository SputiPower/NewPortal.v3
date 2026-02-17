from django.urls import reverse_lazy

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.paginator import InvalidPage
from django.http import Http404

from .models import Product
from .filters import ProductFilter

from django.shortcuts import render, redirect
from .forms import ProductForm

def create_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'simpleapp/product_create.html', {
        'form': form
    })


class ProductsList(ListView):
    model = Product
    template_name = 'products.html'
    context_object_name = 'products'
    paginate_by = 4

    def get_queryset(self):
        queryset = super().get_queryset()
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
            raise Http404("Invalid page")


class ProductDetail(DetailView):
   model = Product
   template_name = 'product.html'
   context_object_name = 'product'

class ProductCreate(CreateView):
    form_class = ProductForm
    model = Product
    template_name = 'product_edit.html'

class ProductUpdate(UpdateView):
    form_class = ProductForm
    model = Product
    template_name = 'product_edit.html'

class ProductDelete(DeleteView):
    model = Product
    template_name = 'product_delete.html'
    success_url = reverse_lazy('product_list')

class ProductCreate(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'simpleapp/product_form.html'  # <- указываем новый шаблон
    success_url = '/products/'  # сюда редирект после сохранения









