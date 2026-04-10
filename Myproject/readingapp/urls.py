from django.urls import path
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage),
    path('bookdata', views.show),
    path('firstpage', views.homepage),
    path('card', views.register),
    path('addbook/', views.addbook, name='addbook'),
    path('register', views.login),
    path('login', views.login1),
    path('logout', views.logout1),
    path('vision', views.vision),
    path('blog', views.blog),
    path('volunteer', views.volunteer),
    path('tc', views.tc),
    path('chat/', views.chat, name='chat'),
    path('delete_book/<id>/', views.deletebook),
    path('category/<str:category>/', views.category_books, name='category_books'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)