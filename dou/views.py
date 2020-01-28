from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.http import HttpResponse

from .models import Book


class BooksView(ListView):
    template_name = 'dou/books.html'
    context_object_name = 'book_list'
    model = Book


class BookView(DetailView):
    template_name = 'dou/book.html'
    context_object_name = 'book'
    model = Book

    # todo this needs a clean up
    def get_object(self):
        print('GET CALLED')
        book = super().get_object()

        return book

    def post(self, request, *args, **kwargs):

        if request.method == 'POST' and request.is_ajax():
            book = super().get_object()

            try:
                if not book.pages.exists():
                    book.refresh_page_images()

                pages = list(book.pages.all().values())
                data = dict()
                data['pages'] = pages

                return JsonResponse(data)
                # return HttpResponse(pages)

            except KeyError:
                return HttpResponse('Error')

            return HttpResponse('done')


def refresh_book(request):
    b_id = None

    if request.method == 'GET':
        b_id = request.GET['book_id']

    if b_id:
        book = Book.objects.get(id=b_id)
        book.refresh_cover_image()
        book.refresh_meta_via_image()

    refreshed = True

    return HttpResponse(refreshed)