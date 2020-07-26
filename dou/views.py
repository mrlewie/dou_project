from django.views.generic import View, TemplateView, ListView, DetailView
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from django.shortcuts import render

from .models import Book, Page


# https://www.youtube.com/watch?v=F5mRW0jo-U4 for tutorial on much of this
# https://stackoverflow.com/questions/5827590/css-styling-in-django-forms for example on forms
class BooksView(View):
    template_name = 'dou/books.html'
    queryset = Book.objects.all()

    def get_queryset(self):
        return self.queryset

    def get(self, request, *args, **kwargs):
        context = {'book_list': self.get_queryset()}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = {}

        if request.method == "POST":
            clicked_book_id = request.POST['clicked_book_id']
            book = Book.objects.get(id=clicked_book_id)

            book.refresh_cover_image()
            book.refresh_meta_via_filename()
            book.refresh_meta_via_image()

            context = {'book_id': book.id,
                       'book_web_id': book.web_id,
                       'book_released': book.released,
                       'book_name_en': book.name_en,
                       'book_name_jp': book.name_jp,
                       'book_img_src': book.cover_thumb_lg.url
                       }

        return JsonResponse(context)


class BookView(DetailView):
    template_name = 'dou/book.html'
    context_object_name = 'book'
    model = Book

    def get_object(self):
        book = super().get_object()

        if not book.pages.exists():
            # call func to get grey placeholders quickly
            book.get_page_placeholders()

            # once done, use post in view to call book.refresh_page_images()

        return book

    def post(self, request, *args, **kwargs):
        context = {}

        if request.method == "POST":

            clicked_page_id = request.POST['clicked_page_id']
            page = Page.objects.get(id=clicked_page_id)

            page.refresh_page_image()

            context = {'page_id': page.id,
                       'page_img_src': page.page_thumb_lg.url
                       }

        return JsonResponse(context)
