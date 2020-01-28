from django import forms


class BooksForm(forms.Form):
    book_id = forms.IntegerField()

