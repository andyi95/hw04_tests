from django.contrib import admin
from django.contrib.flatpages import views
from django.urls import include, path

urlpatterns = [
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('', include('posts.urls')),
    path(
        'about-author/',
        views.flatpage,
        {'url': '/about-author/'},
        name='about'
    ),
    path('about-spec/', views.flatpage, {'url': '/about-spec/'}, name='spec'),
]
