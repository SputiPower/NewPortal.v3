from django.urls import path
from .views import ProductCreate, ProductUpdate, create_product, ProductsList,ProductDelete, ProductDetail

urlpatterns = [
    path('', ProductsList.as_view(), name='product_list'),
    path('<int:pk>', ProductDetail.as_view(), name='product_detail'),
    path('products/create/', create_product, name='product_create'),
    path('create/', ProductCreate.as_view(), name='product_create'),
    path('<int:pk>/update/', ProductUpdate.as_view(), name='product_update'),
    path('<int:pk>/delete/', ProductDelete.as_view(), name='product_delete'),
]