# module imports
import logging
import os
import requests
from django.db import models
from dou_project import settings
from django.core.files.base import ContentFile
from lxml import html, etree
from zipfile import ZipFile
from imagekit import ImageSpec
from imagekit.models import ProcessedImageField
from imagekit.processors import SmartResize, Adjust

# script imports
from dou.scripts import local_data, web_data

# globals
DEFAULT_BOOK_IMG_PATH = r'placeholders/book_default_thumb.jpg'
SETTINGS_MEDIA_PATH = settings.MEDIA_ROOT
PAGE_IMG_LG_PATH = r'pages/'
#FOLDER_PATH = r'F:\Doujinshi_working'
FOLDER_PATH = r'D:\Doujinshi_working'
META_SCRAPE = 'https://www.doujinshi.org/browse'


# # # CHOICE CLASSES
# language choice list for official doujinshi.org values
class LangChoices(models.IntegerChoices):
    UNKNOWN = 1, 'Unknown'
    ENGLISH = 2, 'English'
    JAPANESE = 3, 'Japanese'
    CHINESE = 4, 'Chinese'
    KOREAN = 5, 'Korean'
    FRENCH = 6, 'French'
    GERMAN = 7, 'German'
    SPANISH = 8, 'Spanish'
    ITALIAN = 9, 'Italian'
    RUSSIAN = 10, 'Russian'


# general choice list for official doujinshi.org values
class GenChoices(models.IntegerChoices):
    NO = 0, 'No',
    YES = 1, 'Yes'


# # # PRIMARY MODEL CLASSES
class Book(models.Model):
    web_id = models.CharField(max_length=25, null=True, blank=True)
    version = models.IntegerField(null=True, blank=True, default=0)
    name_en = models.CharField(max_length=150, null=True, blank=True)
    name_jp = models.CharField(max_length=150, null=True, blank=True)
    name_rj = models.CharField(max_length=150, null=True, blank=True)
    released = models.DateField(null=True, blank=True)
    num_pages_orig = models.IntegerField(null=True, blank=True)
    num_pages_user = models.IntegerField(null=True, blank=True)
    lang_orig = models.IntegerField(choices=LangChoices.choices, null=True, blank=True, default=LangChoices.UNKNOWN)
    lang_user = models.IntegerField(choices=LangChoices.choices, null=True, blank=True, default=LangChoices.UNKNOWN)
    user_rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    is_adult = models.BooleanField(choices=GenChoices.choices, null=False, blank=False, default=GenChoices.YES)
    is_anthology = models.BooleanField(choices=GenChoices.choices, null=False, blank=False, default=GenChoices.NO)
    is_decensored = models.BooleanField(choices=GenChoices.choices, null=False, blank=False, default=GenChoices.NO)
    is_colored = models.BooleanField(choices=GenChoices.choices, null=False, blank=False, default=GenChoices.NO)
    is_digital = models.BooleanField(choices=GenChoices.choices, null=False, blank=False, default=GenChoices.NO)
    is_favorite = models.BooleanField(choices=GenChoices.choices, null=False, blank=False, default=GenChoices.NO)
    is_viewed = models.BooleanField(choices=GenChoices.choices, null=False, blank=False, default=GenChoices.NO)
    is_hidden = models.BooleanField(choices=GenChoices.choices, null=False, blank=False, default=GenChoices.NO)
    conventions = models.ManyToManyField('Convention', blank=True)
    types = models.ManyToManyField('Type', blank=True)
    circles = models.ManyToManyField('Circle', blank=True)
    publishers = models.ManyToManyField('Publisher', blank=True)
    authors = models.ManyToManyField('Author', blank=True)
    parodies = models.ManyToManyField('Parody', blank=True)
    contents = models.ManyToManyField('Content', blank=True)
    foldername = models.TextField(unique=True, null=False, blank=False)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)

    # # # PRIMARY FUNCTIONS
    # takes a web_id, filename or cover image from a book record, queries web, updates meta if new version
    def refresh_book_meta(self, refresh_type='cover_image', manual_web_id=None, min_accuracy=0.7):
        """
        :param refresh_type: sets the refresh method. value of 'web_id', 'filename' or 'cover_image' allowed.
        :param manual_web_id: user-set web_id to manually override auto-detected web_id.
        :param min_accuracy: sets the minimum allowed match accuracy for filename and cover_image match methods.
        """

        # todo logs
        # todo else statements and error handles
        xml = None

        if refresh_type in ['web_id', 'filename', 'cover_image']:
            if self.foldername:
                cover_image_path = self.fetch_cover_image_path()
                file_tags_dict = local_data.convert_filename_to_meta_dict(filename=self.foldername)

                if refresh_type == 'web_id' or manual_web_id:
                    web_id = manual_web_id if manual_web_id else self.web_id
                    if web_id:
                        xml = web_data.fetch_meta_xml_via_web_id(web_id=web_id)

                elif refresh_type == 'filename' and self.foldername:
                    xmls = web_data.fetch_meta_xml_via_filename(filename=self.foldername)
                    if xmls is not None:
                        xml = web_data.select_most_similar_xml_book(xmls,
                                                                    known_title=file_tags_dict['title'],
                                                                    min_accuracy=min_accuracy)

                elif refresh_type == 'cover_image' and cover_image_path:
                    xmls = web_data.fetch_meta_xml_via_cover_image(cover_img_path=cover_image_path)
                    if xmls is not None:
                        xml = web_data.select_most_similar_xml_book(xmls,
                                                                    known_title=file_tags_dict['title'],
                                                                    min_accuracy=min_accuracy)

                if xml is not None:
                    meta_dict = web_data.convert_meta_xml_to_dict(xml=xml)
                    if self.version < meta_dict['version']:
                        self.update_book_via_meta_dict(meta_dict=meta_dict,
                                                       file_tags_dict=file_tags_dict)
                    else:
                        print('Same version detected. Not updating.')

    # # # SECONDARY FUNCTIONS
    # update and save a book record using a meta dictionary
    def update_book_via_meta_dict(self, meta_dict, file_tags_dict):
        # todo log
        if meta_dict:
            try:
                self.web_id = meta_dict['web_id']
                self.version = meta_dict['version']
                self.name_en = meta_dict['name_en']
                self.name_jp = meta_dict['name_jp']
                self.name_rj = meta_dict['name_rj']
                self.released = meta_dict['released']
                self.num_pages_orig = meta_dict['num_pages_orig']
                self.lang_orig = meta_dict['lang_orig']
                self.is_adult = meta_dict['is_adult']
                self.save()
            except:
                print('error')
                # handle year 0000-00-00

        if file_tags_dict:
            try:
                #self.num_pages_user = file_tags_dict['num_pages_user']  # todo check this populates earlier
                self.lang_user = file_tags_dict['lang_user']
                self.is_decensored = file_tags_dict['is_decensored']
                self.is_colored = file_tags_dict['is_colored']
                self.is_digital = file_tags_dict['is_digital']
                self.save()
            except:
                print('error')

        # todo secondary meta loops


            """
              msg = 'None' if self.version is None else 'older than xml'
                        logging.info('INFO: db book version is {0}: updating'.format(msg))
    
                        self.web_id = xml.attrib['ID']
                        self.version = xml.attrib['VER']
                        self.name_en = xml.find('NAME_EN').text
                        self.name_jp = xml.find('NAME_JP').text
                        self.name_rj = xml.find('NAME_R').text
                        self.released = xml.find('DATE_RELEASED').text
                        self.num_pages = xml.find('DATA_PAGES').text
                        self.is_adult = xml.find('DATA_AGE').text
                        self.is_anthology = xml.find('DATA_ANTHOLOGY').text
                        self.lang_orig = xml.find('DATA_LANGUAGE').text
                        self.save()
    
                        obj_dict = {'convention': Convention, 'publisher': Publisher, 'type': Type, 'circle': Circle,
                                    'author': Author, 'parody': Parody, 'contents': Content}
    
                        for key, val in obj_dict.items():
                            for elem in xml.iter('ITEM'):
                                if key == elem.attrib['TYPE']:
                                    obj, created = val.objects.get_or_create(web_id=elem.attrib['ID'])
                                    rel_field = val.book_set.field.name
                                    if created:
                                        obj.update_via_xml(elem)
                                    self.__getattribute__(rel_field).add(obj)
    
                        logging.info('FOUND: book metadata updated from dou.org web_id: {0}'.format(self.web_id))
    
                        if extra_tags:
                            logging.info('START: extra tags provided, adding to book metadata in db via dict')
    
                            self.lang_trans = extra_tags['translation']
                            self.is_decensored = extra_tags['decensored']
                            self.is_colored = extra_tags['colored']
                            self.is_digital = extra_tags['digital']
                            self.save()
    
                            logging.info('FOUND: extra tags added to boom metadata in db: {0}'.format(self.web_id))
                            logging.info('FINISH: extra tags provided, adding to book metadata in db via dict')
    
                    else:
                        logging.warning('WARN: book version same as dj.org: skipping')
    
                except Exception as e:
                    logging.critical(e)

                """

    # fetch the underlying cover image path and filename
    def fetch_cover_image_path(self):
        cover_exists = self.pages.filter(is_cover=True)

        if cover_exists:
            cover_page = self.pages.get(is_cover=True)
            cover_path = cover_page.page_thumb_lg.file.name
            return cover_path
        else:
            return None


# thumbnail portrait image processor
class ThumbnailPortrait(ImageSpec):
    processors = [Adjust(contrast=1.1, sharpness=1.1), SmartResize(420, 595)]
    format = 'JPEG'
    options = {'quality': 90}


# thumbnail landscape image processor
class ThumbnailLandscape(ImageSpec):
    processors = [Adjust(contrast=1.1, sharpness=1.1), SmartResize(595, 420)]
    format = 'JPEG'
    options = {'quality': 90}


# thumbnail square image processor
class ThumbnailSquare(ImageSpec):
    processors = [Adjust(contrast=1.1, sharpness=1.1), SmartResize(595, 595)]
    format = 'JPEG'
    options = {'quality': 90}


class Page(models.Model):
    page_num = models.IntegerField(null=False, blank=False)
    width_orig = models.IntegerField(null=True, blank=True)
    height_orig = models.IntegerField(null=True, blank=True)
    orientation_orig = models.CharField(max_length=10, null=True, blank=True)
    is_cover = models.BooleanField(null=False, blank=False, default=False)
    is_viewed = models.BooleanField(null=False, blank=False, default=False)
    is_hidden = models.BooleanField(null=False, blank=False, default=False)
    filename = models.TextField(null=False, blank=False)
    page_thumb_lg = ProcessedImageField(upload_to=PAGE_IMG_LG_PATH, null=True, blank=True,
                                        default=DEFAULT_BOOK_IMG_PATH)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    book = models.ForeignKey('Book', related_name='pages', on_delete=models.CASCADE)

    def refresh_page_image(self):
        logging.info('START: refreshing book page image for id: {0}'.format(self.id))

        if self.book.foldername and self.book.extension:
            zip_path = os.path.join(FOLDER_PATH, self.book.foldername + self.book.extension)

            if os.path.isfile(zip_path):
                with ZipFile(zip_path, 'r') as zip:
                    filenames = sorted(zip.namelist())

                    if filenames:
                        for filename in filenames:
                            if filename == self.filename + self.extension:

                                with zip.open(filename, mode='r') as img:
                                    try:
                                        content = ContentFile(img.read())

                                        # todo get height and width

                                        self.page_thumb_lg.save('pge' + '_' + 'lg', content)

                                        logging.info('FOUND: refreshed page image for id: {0}'.format(self.id))

                                    except Exception as e:
                                        logging.critical(e)

                    else:
                        logging.warning('WARN: folder detected in zip: skipping')

            else:
                logging.warning('WARN: zip path is not to a file: skipping')

        else:
            logging.warning('WARN: filename and extension not provided: skipping')

        logging.info('FINISH: refreshing page image for id: {0}'.format(self.id))


# # # SECONDARY MODEL CLASSES
class SecondaryMetadata(models.Model):
    web_id = models.CharField(max_length=100, null=True, blank=True)
    version = models.CharField(max_length=5, null=True, blank=True)
    name_en = models.CharField(max_length=100, null=True, blank=True)
    name_jp = models.CharField(max_length=100, null=True, blank=True)
    name_rj = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        abstract = True

    def update_via_xml(self, xml):
        logging.info('START: updating secondary metadata in db via xml')

        if xml is not None:
            try:
                if self.version is None or self.version < xml.attrib['VER']:
                    msg = 'None' if self.version is None else 'older than xml'
                    logging.info('INFO: db secondary metadata version is {0}: updating'.format(msg))

                    self.web_id = xml.attrib['ID']
                    self.version = xml.attrib['VER']
                    self.name_en = xml.find('NAME_EN').text
                    self.name_jp = xml.find('NAME_JP').text
                    self.name_rj = xml.find('NAME_R').text
                    self.save()

                    logging.info('FOUND: secondary metadata updated from dou.org for web_id: {0}'.format(self.web_id))

            except Exception as e:
                logging.critical(e)

        else:
            logging.warning('INFO: no xml was provided: skipping')

        logging.info('FINISH: updating secondary metadata in db via xml')


class Convention(SecondaryMetadata):
    class Meta:
        constraints = [models.UniqueConstraint(fields=['web_id'], name='convention_unq')]


class Publisher(SecondaryMetadata):
    class Meta:
        constraints = [models.UniqueConstraint(fields=['web_id'], name='publisher_unq')]


class Type(SecondaryMetadata):
    class Meta:
        constraints = [models.UniqueConstraint(fields=['web_id'], name='type_unq')]


class Circle(SecondaryMetadata):
    class Meta:
        constraints = [models.UniqueConstraint(fields=['web_id'], name='circle_unq')]


class Author(SecondaryMetadata):
    url_homepage = models.URLField(max_length=255, null=True, blank=True)
    url_blog = models.URLField(max_length=255, null=True, blank=True)
    url_twitter = models.URLField(max_length=255, null=True, blank=True)
    url_pixiv = models.URLField(max_length=255, null=True, blank=True)
    profile_img = ProcessedImageField(upload_to='profiles/', options={'quality': 100}, format='JPEG',
                                      processors=[Adjust(contrast=1.1, sharpness=1.1), SmartResize(200, 200)],
                                      null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['web_id'], name='author_unq')]

    def refresh_profile_image(self):
        logging.info('START: refreshing author profile image for id: {0}'.format(self.id))

        xp_dict = {'home': '//a[@title="Homepage"]/@href', 'blog': '//a[@title="Blog"]/@href',
                   'twit': '//a[@title="Twitter"]/@href', 'pixv': '//a[@title="Pixiv"]/@href'}

        if self.web_id:
            url = '{0}/{1}/{2}/'.format(META_SCRAPE, 'author', self.web_id[1:])

            try:
                logging.info('INFO: fetching xml from dou.org for web_id: {0}.'.format(self.web_id))
                response = requests.get(url)
                tree = html.fromstring(response.content)

                if html is not None:

                    self.url_homepage = tree.xpath(xp_dict['home'])[0] if tree.xpath(
                        xp_dict['home']) else None  # todo is there something safer than [0]
                    self.url_blog = tree.xpath(xp_dict['blog'])[0] if tree.xpath(xp_dict['blog']) else None
                    self.url_twitter = tree.xpath(xp_dict['twit'])[0] if tree.xpath(xp_dict['twit']) else None
                    self.url_pixiv = tree.xpath(xp_dict['pixv'])[0] if tree.xpath(xp_dict['pixv']) else None
                    self.save()

                    logging.info('FOUND: found xml author websites from dou.org for web_id: {0}'.format(self.web_id))

                else:
                    logging.info('WARN: nothing found on dou.org for web_id: {0}'.format(self.web_id))

            except Exception as e:
                logging.critical(e)

            if self.url_twitter:
                xp_img_url = '//img[contains(@src, "profile_images") and contains(@src, "400x400")]/@src'

                try:
                    logging.info('INFO: fetching profile image from twitter for web_id: {0}.'.format(self.web_id))
                    response = requests.get(self.url_twitter)
                    tree = html.fromstring(response.content)

                    img_url = tree.xpath(xp_img_url)[0] if tree.xpath(
                        xp_img_url) else None  # todo is there something safer than [0], find?

                    if img_url:
                        response = requests.get(img_url)

                        if response.status_code == 200:
                            thumb_name = 'author_{0}_thumb'.format(self.id)
                            content = ContentFile(response.content)

                            self.profile_img.delete()
                            self.profile_img.save(thumb_name, content)


                except Exception as e:
                    logging.critical(e)


class Parody(SecondaryMetadata):
    class Meta:
        constraints = [models.UniqueConstraint(fields=['web_id'], name='parody_unq')]


class Content(SecondaryMetadata):
    class Meta:
        constraints = [models.UniqueConstraint(fields=['web_id'], name='content_unq')]


def clean_cover_images(folder_path):
    logging.info('START: scanning cover image records with local files in folder: {0}'.format(folder_path))

    db_filenames_lg = [os.path.basename(rec) for rec in Book.objects.values_list('cover_thumb_lg', flat=True) if rec]

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file != os.path.basename(DEFAULT_BOOK_IMG_PATH):
                if file not in db_filenames_lg:
                    os.remove(os.path.join(root, file))
                    logging.info('FOUND: deleted cover file with no associated db record: {0}'.format(file))

    logging.info('FINISH: scanning cover image records with local files in folder: {0}'.format(folder_path))

#from dou.models import *
#import os
#refresh_book_and_page_filenames(FOLDER_PATH)
#books = Book.objects.all()
#book = Book.objects.get(id=13185)

#for book in books:
    #book.refresh_meta_via_filename()
    #book.refresh_meta_via_image()
    #book.refresh_cover_image()
    #book.refresh_cover_palette()
    #book.get_page_images()

#book.refresh_page_images()
#clean_filenames(FOLDER_PATH)
#clean_cover_images(SETTINGS_MEDIA_PATH)

