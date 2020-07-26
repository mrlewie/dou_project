from django.urls import path
from .views import BooksView, BookView

urlpatterns = [
    path('books/', BooksView.as_view(), name='books'),
    path('book/<int:pk>/', BookView.as_view(template_name="dou/test.html"), name='book'),
]