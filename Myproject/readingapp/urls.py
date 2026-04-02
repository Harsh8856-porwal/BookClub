from django.urls import path
from . import views
from django.contrib import admin
from readingapp.views import *
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',homepage),
    path('bookdata',show),
    path('firstpage',homepage),
    path('card',register),
    path('addbook/', views.addbook, name='addbook'),
    path('register',login),
    path('login',login1),
    path('logout',logout1),
    path('vision',vision),  
    path('blog',blog),
    path('volunteer',volunteer),
    path('tc',tc),
    path('delete_book/<id>/',deletebook),
    path('category/<str:category>/', views.category_books, name='category_books'),
  
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)