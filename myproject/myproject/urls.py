"""
URL configuration for myproject project.

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
from home import views as core_views

urlpatterns = [
    # Custom admin (admin-dashboard, admin/users/, admin/buildings/, ...) must come first
    path('', include('home.urls')),
    path('map/', core_views.map_view, name='map_view'),
    path('logout/', core_views.logout_view, name='logout'),
    # Django built-in admin at /django-admin/ (optional; you can remove if not needed)
    path('django-admin/', admin.site.urls),
]

