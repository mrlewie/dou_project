# module imports
import os
import re
from zipfile import ZipFile
from PIL import Image

# django imports
import dou.models as models

# globals
FOLDER_PATH = r'D:\Doujinshi_working'
ALLOWED_EXTS = ('.png',
                '.jfif',
                '.jpg',
                '.jpeg',
                '.tiff',
                '.tif',
                '.bmp',
                '.gif')


# # # PRIMARY FUNCTIONS
# takes a folder path, gets all folders in it, adds each to book db table
def scan_book_folders():
    """
    :return: a list of all new book objects that were added.
    """

    book_list = []

    for dir_name in os.listdir(FOLDER_PATH):
        dir_path = os.path.join(FOLDER_PATH, dir_name)

        if os.path.isdir(dir_path):
            files = [f for f in os.listdir(dir_path) if f.endswith(ALLOWED_EXTS)]

            if files:
                book, created = models.Book.objects.get_or_create(foldername=dir_name)

                if created:
                    book_list.append(book)
                    print('SUCCESS: added book info to db from folder: {0}.'.format(dir_name))
            else:
                print('WARN: no valid page files in folder: {0}. Skipped.'.format(dir_name))
        else:
            print('WARN: invalid folder detected: {0}. Skipped.'.format(dir_name))

    return book_list


# takes a single book object and gets related page info (non-images) from related folder
def scan_book_pages_in_folders(book):
    """
    :param book: a single book object with id and foldername.
    """

    new_page_list = []

    dir_path = os.path.join(FOLDER_PATH, book.foldername)
    if os.path.isdir(dir_path):
        files = [f for f in os.listdir(dir_path) if f.endswith(ALLOWED_EXTS)]

        if files:
            for page_num, page_file in enumerate(sorted(files), start=1):
                cover_detected = True if page_num == 1 else False

                page = models.Page(book=book, page_num=page_num,
                                   is_cover=cover_detected, filename=page_file)

                new_page_list.append(page)

            if new_page_list:
                models.Page.objects.bulk_create(new_page_list)
                print('SUCCESS: added page info to db from folder: {0}.'.format(book.foldername))
        else:
            print('WARN: no valid page files in folder: {0}. Skipped.'.format(book.foldername))
    else:
        print('WARN: invalid folder detected: {0}. Skipped.'.format(book.foldername))


# takes a single page object and gets related page image from related folder
def scan_page_images_in_folders(book):
    """
    :param book: a single book object with filename and id.
    """

    dir_path = os.path.join(FOLDER_PATH, book.foldername)

    if os.path.isdir(dir_path):
        files = [f for f in os.listdir(dir_path) if f.endswith(ALLOWED_EXTS)]

        if files:
            pages = book.pages.filter(filename__in=sorted(files))

            for page in pages:
                filepath = os.path.join(dir_path, page.filename)

                try:
                    with open(filepath, 'rb') as buffer:
                        img = Image.open(buffer, 'r')
                        w, h = img.width, img.height

                        if img.width < img.height:
                            orient = 'portrait'
                            img_gen = models.Thumbnail(source=buffer, width=420, height=595).generate()
                        elif img.width > img.height:
                            orient = 'landscape'
                            img_gen = models.Thumbnail(source=buffer, width=840, height=595).generate()
                        elif img.width == img.height:
                            orient = 'square'
                            img_gen = models.Thumbnail(source=buffer, width=595, height=595).generate()
                        else:
                            orient, img_gen = None, None

                        if img_gen:
                            # todo page width, height, orientation
                            page.page_thumb_lg.save('pge' + '_' + str(book.id) + '.jpeg', img_gen)
                            print('SUCCESS: processed page image: {0}.'.format(page.filename))

                except Exception as e:
                    print(e)
        else:
            print('WARN: no valid page files in folder: {0}. Skipped.'.format(book.filename))
    else:
        print('WARN: invalid folder detected: {0}. Skipped.'.format(book.filename))


# unpacks a book foldername components from local storage into a dirty dict
def convert_foldername_to_meta_dict(foldername):
    """
    :param foldername: a string containing a book foldername.
    :return: a dictionary of detected foldername tags (e.g. english, decensored), or none.
    """

    meta_dict, tags_dict = {}, {}

    if foldername:
        try:
            patterns_list = [
                '^' + '\((.*?)\)' + '\s' + '\[(?P<circle>.*?)\((?P<author>.*?)\)\]' + '\s' + '(?P<title>[^(\[{]+)',
                '^' + '\((.*?)\)' + '\s' + '\[(?P<author>[^()]+)\]' + '\s' + '(?P<title>[^(\[{]+)',
                '^' + '\[(?P<circle>.*?)\((?P<author>.*?)\)\]' + '\s' + '(?P<title>[^(\[{]+)',
                '^' + '\[(?P<author>[^()]+)\]' + '\s' + '(?P<title>[^(\[{]+)',
                '^' + '(?P<title>[^(\[{]+)'
            ]

            meta_dict.update({
                'circle':   None,
                'author':   None,
                'title':    None
            })
            tags_dict.update({
                'lang_user':     0,
                'is_decensored': 0,
                'is_colored':    0,
                'is_digital':    0
            })

            lang_user_dict = {
                'unknown': 1,
                'english': 2,
                'eng': 2,
                'en': 2,
                '英訳': 2,
                'japanese': 3,
                'chinese': 4,
                'korean': 5,
                'french': 6,
                'german': 7,
                'spanish': 8,
                'italian': 9,
                'russian': 10
            }
            decensored_dict = {
                'uncensored': 1,
                'decensored': 1
            }
            colored_dict = {
                'colorised': 1,
                'colorized': 1,
                'colourised': 1,
                'colourized': 1,
                'colored': 1,
                'coloured': 1,
                'color': 1,
                'colour': 1
            }
            digitized_dict = {
                'digital': 1,
                'digitized': 1,
                'digitised': 1
            }

            for pattern in patterns_list:
                match = re.match(pattern, foldername)
                if match:
                    meta_dict.update(match.groupdict())
                    break

            if meta_dict:
                print('SUCCESS: meta {0} detected and converted to dict.'.format(meta_dict))

            for tag in re.findall('[\[{]([^()]+?)[}\]]', foldername.lower()):
                if tag in lang_user_dict:
                    tags_dict.update({'lang_user': lang_user_dict[tag]})
                elif tag in decensored_dict:
                    tags_dict.update({'is_decensored': decensored_dict[tag]})
                elif tag in colored_dict:
                    tags_dict.update({'is_colored': colored_dict[tag]})
                elif tag in digitized_dict:
                    tags_dict.update({'is_digital': digitized_dict[tag]})

            if tags_dict:
                print('SUCCESS: tags {0} detected and converted to dict.'.format(tags_dict))

            meta_dict.update(tags_dict)

        except Exception as e:
            print(e)
    else:
        print('WARN: no filename provided. Skipping.')

    return meta_dict



#
def clean_filenames(folder_path):
    """
    logging.info('START: scanning db records with missing zip files in folder: {0}'.format(folder_path))

    for db_filename in Book.objects.values_list('filename', 'extension'):
        folder_file = os.path.join(FOLDER_PATH, db_filename[0] + db_filename[1])

        if not os.path.isfile(folder_file):
            Book.objects.filter(filename=db_filename[0], extension=db_filename[1]).delete()
            logging.info('FOUND: delete db record with no associated zip file : {0}'.format(db_filename[0]))

    logging.info('FINISH: scanning db record with missing zip files in folder: {0}'.format(folder_path))
    """



"""
# takes a filepath and filename, opens zip, counts num of pages, returns page count
def count_book_pages_in_folder(folder_path, filename):
    log.CountBookPagesInZip.start(info=filename)  # log
    num_pages = None

    if folder_path and filename:
        if filename.endswith('.zip'):

            with ZipFile(os.path.join(folder_path, filename), 'r') as zip:
                page_files = check_list_of_page_filetype(zip.namelist())

                if page_files and page_files[-1] != '/':
                    num_pages = len(page_files)
                    log.CountBookPagesInZip.counted_pages(info=num_pages)  # log
                else:
                    log.CountBookPagesInZip.warn_folder_detected(info=filename)  # log
        else:
            log.CountBookPagesInZip.warn_not_zip_file(info=filename)  # log
            # todo add support for rar
    else:
        log.CountBookPagesInZip.no_folder_or_filename(info=filename)  # log

    log.CountBookPagesInZip.end(info=filename)  # log
    return num_pages
"""




"""
from dou.models import *
from dou.scripts import local_data as loc
from dou.scripts import web_data as web

ids = loc.scan_book_zips()
for book_rec in Book.objects.filter(id__in=ids):
    loc.scan_book_pages_from_zips(book_rec=book_rec, folder_path=FOLDER_PATH)
    
"""