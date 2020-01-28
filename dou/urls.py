from django.urls import path
from django.conf.urls import url

from .views import BooksView, BookView, refresh_book

urlpatterns = [
    path('books/', BooksView.as_view(template_name="dou/books.html")),
    path('book/<int:pk>/', BookView.as_view(template_name="dou/book.html"), name='book'),
    url(r'^refresh_book/$', refresh_book, name='refresh_book'),

]