from django import forms
from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['web_id', 'name_en', 'name_jp', 'released', 'cover_thumb_lg']

