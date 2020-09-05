# module imports
import os
import re
from zipfile import ZipFile
from PIL import Image

# django imports
import dou.models as models
from django.core.files.base import ContentFile

# script imports
from dou.scripts import log_messages as log

# globals
#FOLDER_PATH = r'F:\Doujinshi_working'
FOLDER_PATH = r'D:\Doujinshi_working'


# # # PRIMARY FUNCTIONS
# scans folder for new zip files, inserts basic book, page info, media to db
def scan_local_content(folder_path=FOLDER_PATH):
    """
    :param folder_path: path to folder containing book zip files.
    """

    log.ScanLocalContent.start(info=folder_path)

    for zip_file in os.listdir(folder_path):
        zip_filename, zip_ext = os.path.splitext(zip_file)

        if zip_ext == '.zip':
            with ZipFile(os.path.join(folder_path, zip_file), 'r') as zip:
                page_files = check_list_of_page_filetype(zip.namelist())

                if page_files and page_files[-1] != '/':
                    page_files = sorted(page_files)
                    book_rec, book_created = models.Book.objects.get_or_create(filename=zip_filename,
                                                                               num_pages_user=len(page_files),
                                                                               extension=zip_ext)

                    if book_created:
                        log.ScanLocalContent.book_added(info=zip_filename)

                        for page_num, page_file in enumerate(page_files, start=1):
                            try:
                                cover_detected = True if page_num == 1 else False
                                page_filename, page_ext = os.path.splitext(page_file)

                                content = ContentFile(zip.read(page_file))
                                img = Image.open(content.file)
                                orientation = get_image_orientation(img=img)

                                page_rec, page_created = models.Page.objects.get_or_create(book=book_rec,
                                                                                           page_num=page_num,
                                                                                           width_orig=img.width,
                                                                                           height_orig=img.height,
                                                                                           orientation_orig=orientation,
                                                                                           is_cover=cover_detected,
                                                                                           filename=page_filename,
                                                                                           extension=page_ext)

                                if page_created:
                                    page_rec.page_thumb_lg.save('pge' + '_' + str(book_rec.id), content)

                            except Exception as e:
                                log.ScanLocalContent.exception_during_page_creation(e)

                        log.ScanLocalContent.pages_added(info=book_rec.id)

                    else:
                        log.ScanLocalContent.warn_book_exists(info=book_rec.id)
                else:
                    log.ScanLocalContent.warn_folder_detected(info=zip_filename)
        else:
            log.ScanLocalContent.warn_not_zip_file(info=zip_filename + zip_ext)
            # todo add support for rar

    log.ScanLocalContent.end(info=folder_path)


# unpacks a book filename components from local storage into a dirty dict
def convert_filename_to_meta_dict(filename):
    """
    :param filename: a string containing a book zip filename, minus extension.
    :return: a dictionary of detected filename tags (e.g. english, decensored), or none.
    """

    log.ConvertFilenameToMetaDict.start()
    meta_dict, tags_dict = {}, {}

    if filename:
        try:
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

            patterns_list = [
                '^' + '\((.*?)\)' + '\s' + '\[(?P<circle>.*?)\((?P<author>.*?)\)\]' + '\s' + '(?P<title>[^(\[{]+)',
                '^' + '\((.*?)\)' + '\s' + '\[(?P<author>[^()]+)\]' + '\s' + '(?P<title>[^(\[{]+)',
                '^' + '\[(?P<circle>.*?)\((?P<author>.*?)\)\]' + '\s' + '(?P<title>[^(\[{]+)',
                '^' + '\[(?P<author>[^()]+)\]' + '\s' + '(?P<title>[^(\[{]+)',
                '^' + '(?P<title>[^(\[{]+)'
            ]

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
                match = re.match(pattern, filename)
                if match:
                    match_dict = match.groupdict()
                    meta_dict.update(match_dict)
                    break

            if meta_dict:
                log.ConvertFilenameToMetaDict.found_meta(info=meta_dict)
            else:
                log.ConvertFilenameToMetaDict.warn_no_meta_detected()

            for tag in re.findall('[\[{]([^()]+?)[}\]]', filename.lower()):
                if tag in lang_user_dict:
                    tags_dict.update({'lang_user': lang_user_dict[tag]})
                elif tag in decensored_dict:
                    tags_dict.update({'is_decensored': decensored_dict[tag]})
                elif tag in colored_dict:
                    tags_dict.update({'is_colored': colored_dict[tag]})
                elif tag in digitized_dict:
                    tags_dict.update({'is_digital': digitized_dict[tag]})

            if tags_dict:
                log.ConvertFilenameToMetaDict.found_tags(info=tags_dict)
            else:
                log.ConvertFilenameToMetaDict.warn_no_tags_detected()

            meta_dict.update(tags_dict)

        except Exception as e:
            log.ConvertFilenameToMetaDict.exception_during_meta_unpack(e)
    else:
        log.ConvertFilenameToMetaDict.warn_no_filename_provided()

    log.ConvertFilenameToMetaDict.end()
    return meta_dict


# remove images from media folder that are no longer in db
def clean_page_images_folder():
    print() # todo


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


# # # SECONDARY FUNCTIONS
# takes a list of filenames, check if image extensions, returns list of image types
def check_list_of_page_filetype(filename_list):
    allowed_extensions = ('.png', '.jfif', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif')

    if filename_list and filename_list[-1] != '/':
        clean_filename_list = [fn for fn in filename_list if fn.lower().endswith(allowed_extensions)]

        if len(clean_filename_list) < len(filename_list):
            log.CheckListOfPageFiletypes.warn_not_all_files_images()  # log

        return clean_filename_list
    else:
        return None


# takes a pil image, check dimensions, returns orientation as string
def get_image_orientation(img):
    if img:
        if img.height > img.width:
            orientation = 'portrait'
        elif img.height < img.width:
            orientation = 'landscape'
        elif img.height == img.width:
            orientation = 'square'
        else:
            orientation = 'unknown'

        return orientation

    else:
        return None


# takes a filepath and filename, opens zip, counts num of pages, returns page count
def count_book_pages_in_zip(folder_path, filename):
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


# testing
#
# takes a folder path, gets all folders in it, adds each to book db table
def scan_book_folders(folder_path=FOLDER_PATH):
    """
    :param folder_path: path to folder containing book zip files.
    :return: a list of all new book ids that were added.
    """

    new_id_list = []
    exts = ('.png',
            '.jfif',
            '.jpg',
            '.jpeg',
            '.tiff',
            '.tif',
            '.bmp',
            '.gif')

    for dir_name in os.listdir(FOLDER_PATH):
        dir_path = os.path.join(FOLDER_PATH, dir_name)

        if os.path.isdir(dir_path):
            files = [f for f in os.listdir(dir_path) if f.endswith(exts)]

            if files:
                book, created = models.Book.objects.get_or_create(foldername=dir_name)

                if created:
                    new_id_list.append(book.id)
                    print('SUCCESS: added book info to db from zip: {0}.'.format(dir_name))
            else:
                print('WARN: no valid page files in folder: {0}. Skipped.'.format(dir_name))
        else:
            print('WARN: invalid folder detected: {0}. Skipped.'.format(dir_name))

    return new_id_list


# takes a single book object and gets related page info (non-images) from related folder
def scan_book_pages_in_folders(book, folder_path=FOLDER_PATH):
    """
    :param book: a single book object with filename and id.
    :param folder_path: path to folder containing book zip files.
    """

    new_page_list = []
    exts = ('.png',
            '.jfif',
            '.jpg',
            '.jpeg',
            '.tiff',
            '.tif',
            '.bmp',
            '.gif')

    dir_path = os.path.join(FOLDER_PATH, book.foldername)
    if os.path.isdir(dir_path):
        files = [f for f in os.listdir(dir_path) if f.endswith(exts)]

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
def scan_page_images_in_folders(book, folder_path=FOLDER_PATH):
    """
    :param book: a single book object with filename and id.
    :param folder_path: path to folder containing book zip files.
    """

    exts = ('.png',
            '.jfif',
            '.jpg',
            '.jpeg',
            '.tiff',
            '.tif',
            '.bmp',
            '.gif')

    dir_path = os.path.join(FOLDER_PATH, book.foldername)
    if os.path.isdir(dir_path):
        files = [f for f in os.listdir(dir_path) if f.endswith(exts)]

        if files:
            pages = book.pages.filter(filename__in=sorted(files))

            for page in pages:
                filepath = os.path.join(dir_path, page.filename)

                with open(filepath, 'rb') as buffer:
                    img = Image.open(buffer, 'r')
                    w, h = img.width, img.height
                    orient = get_image_orientation(img=img)

                    if orient == 'portrait':
                        img_gen = models.ThumbnailPortrait(source=buffer).generate()
                    elif orient == 'landscape':
                        img_gen = models.ThumbnailLandscape(source=buffer).generate()
                    elif orient == 'square':
                        img_gen = models.ThumbnailSquare(source=buffer).generate()

                    if img_gen:
                        # todo page width, height, orientation
                        page.page_thumb_lg.save('pge' + '_' + str(book.id) + '.jpeg', img_gen)
                        print('SUCCESS: processed page image: {0}.'.format(page.filename))
        else:
            print('WARN: no valid page files in folder: {0}. Skipped.'.format(book.filename))
    else:
        print('WARN: invalid folder detected: {0}. Skipped.'.format(book.filename))




"""
from dou.models import *
from dou.scripts import local_data as loc
from dou.scripts import web_data as web

ids = loc.scan_book_zips()
for book_rec in Book.objects.filter(id__in=ids):
    loc.scan_book_pages_from_zips(book_rec=book_rec, folder_path=FOLDER_PATH)
    
"""