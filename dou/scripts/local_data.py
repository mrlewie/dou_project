# module imports
import logging
import os
from zipfile import ZipFile
from PIL import Image
from django.core.files.base import ContentFile

# model imports
from dou.models import Book, Page

# script imports
from dou.scripts import log_messages as log


# scans folder for new zip files, inserts basic book, page info, media to db
def scan_local_content(folder_path):
    log.ScanLocalContent.start(info=folder_path)  # log

    for zip_file in os.listdir(folder_path):
        zip_filename, zip_ext = os.path.splitext(zip_file)

        if zip_ext == '.zip':
            with ZipFile(os.path.join(folder_path, zip_file), 'r') as zip:
                page_files = check_list_of_page_filetype(zip.namelist())

                if page_files and page_files[-1] != '/':
                    page_files = sorted(page_files)
                    book_rec, book_created = Book.objects.get_or_create(filename=zip_filename,
                                                                        extension=zip_ext)

                    if book_created:
                        log.ScanLocalContent.book_added(info=zip_filename)  # log

                        for page_num, page_file in enumerate(page_files, start=1):
                            try:
                                content = ContentFile(zip.read(page_file))
                                img = Image.open(content.file)

                                page_filename, page_ext = os.path.splitext(page_file)
                                cover_detected = True if page_num == 1 else False
                                orientation = get_image_orientation(img=img)

                                page_rec, page_created = Page.objects.get_or_create(book=book_rec, page_num=page_num,
                                                                                    width_orig=img.width,
                                                                                    height_orig=img.height,
                                                                                    orientation_orig=orientation,
                                                                                    is_cover=cover_detected,
                                                                                    filename=page_filename,
                                                                                    extension=page_ext)

                                if page_created:
                                    page_rec.page_thumb_lg.save('pge' + '_' + str(book_rec.id), content)

                            except Exception as e:
                                logging.critical(e)

                        log.ScanLocalContent.pages_added(info=book_rec.id)  # log

                    else:
                        log.ScanLocalContent.warn_book_exists(info=book_rec.id)  # log
                else:
                    log.ScanLocalContent.warn_folder_detected(info=zip_filename)  # log
        else:
            log.ScanLocalContent.warn_not_zip_file(info=zip_ext)  # log
            # todo add support for rar

    log.ScanLocalContent.end(info=folder_path)  # log


# take a list of filenames with extensions, check if image types, remove non-image types
def check_list_of_page_filetype(filename_list):
    allowed_extensions = ('.png', '.jfif', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif')

    if filename_list and filename_list[-1] != '/':
        clean_filename_list = [fn for fn in filename_list if fn.lower().endswith(allowed_extensions)]

        if len(clean_filename_list) < len(filename_list):
            log.ScanCheckListOfPageFiletypes.warn_not_all_files_images()  # log

        return clean_filename_list
    else:
        return None


# take a pil image, check dimensions, return orientation as string
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
