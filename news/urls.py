"""
URL configuration for news project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import JSONOpenAPIRenderer

schema_view = get_schema_view(
    title='NewsPortal API',
    description='REST API schema for news and articles',
    version='1.0.0',
    renderer_classes=[JSONOpenAPIRenderer],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('openapi', schema_view, name='openapi-schema'),
    path('swagger-ui/', TemplateView.as_view(template_name='swagger-ui.html'), name='swagger-ui'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('pages/', include('django.contrib.flatpages.urls')),
    path('products/', include('simpleapp.urls')),
    path('', include('portal.urls')),
    path('accounts/', include('allauth.urls')),
    path('sign/', include('sign.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
