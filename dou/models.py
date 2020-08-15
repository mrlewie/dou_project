from django.db import models
from dou_project import settings
from django.core.files.base import ContentFile
from lxml import html, etree
from zipfile import ZipFile
from imagekit.models import ProcessedImageField
from imagekit.processors import SmartResize, Adjust, TrimBorderColor
from colorthief import ColorThief
from difflib import SequenceMatcher as seqm
import logging
import json
import os
import re
import requests

# logging settings
logging.basicConfig(format='%(message)s', level=logging.INFO)

# globals
DEFAULT_BOOK_IMG_PATH = r'placeholders/book_default_thumb.jpg'
SETTINGS_MEDIA_PATH = settings.MEDIA_ROOT
PAGE_IMG_LG_PATH = r'pages/'
FOLDER_PATH = r'F:\Doujinshi_working'
META_GENERAL = 'http://doujinshi.mugimugi.org/api'
META_API = '96f9cd021a9125919d78'  # 'be519952736a525a4816' mrlewie / mrlew
META_QUERY_ID = '?S=getID&ID='
META_QUERY_ITEM = '?S=itemSearch&T={0}&sn={1}'
META_QUERY_OBJ = '?S=objectSearch&sn='
META_QUERY_LIST = '&slist='
META_QUERY_IMG = '?S=imageSearch'
META_SCRAPE = 'https://www.doujinshi.org/browse'


class Book(models.Model):
    web_id = models.CharField(max_length=25, null=True, blank=True)
    version = models.CharField(max_length=5, null=True, blank=True)
    name_en = models.CharField(max_length=150, null=True, blank=True)
    name_jp = models.CharField(max_length=150, null=True, blank=True)
    name_rj = models.CharField(max_length=150, null=True, blank=True)
    released = models.CharField(max_length=15, null=True, blank=True)
    num_pages = models.CharField(max_length=5, null=True, blank=True)
    lang_orig = models.CharField(max_length=50, null=True, blank=True)
    lang_trans = models.CharField(max_length=50, null=True, blank=True)
    user_rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    is_adult = models.BooleanField(null=False, blank=False, default=True)
    is_anthology = models.BooleanField(null=False, blank=False, default=False)
    is_decensored = models.BooleanField(null=False, blank=False, default=False)
    is_colored = models.BooleanField(null=False, blank=False, default=False)
    is_digital = models.BooleanField(null=False, blank=False, default=False)
    is_favorite = models.BooleanField(null=False, blank=False, default=False)
    is_viewed = models.BooleanField(null=False, blank=False, default=False)
    is_hidden = models.BooleanField(null=False, blank=False, default=False)
    conventions = models.ManyToManyField('Convention', blank=True)
    publishers = models.ManyToManyField('Publisher', blank=True)
    types = models.ManyToManyField('Type', blank=True)
    circles = models.ManyToManyField('Circle', blank=True)
    authors = models.ManyToManyField('Author', blank=True)
    parodies = models.ManyToManyField('Parody', blank=True)
    contents = models.ManyToManyField('Content', blank=True)
    filename = models.TextField(unique=True, null=False, blank=False)
    extension = models.CharField(max_length=10, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)

    def parse_filename_to_dict(self):

        def init_regex_patterns():

            # metadata regex dict
            s = '\s'
            start = '^'
            con = '\((.*?)\)'
            cir_and_aut = '\[(?P<circle>.*?)\((?P<author>.*?)\)\]'
            cir_or_aut = '\[(?P<author>[^()]+)\]'
            ttl = '(?P<title>[^(\[{]+)'

            meta_patterns_list = [start + con + s + cir_and_aut + s + ttl, start + con + s + cir_or_aut + s + ttl,
                                  start + cir_and_aut + s + ttl, start + cir_or_aut + s + ttl, start + ttl]

            tags_patterns_dict = {'translation': ['english', 'eng', 'en', '英訳'],
                                  'decensored': ['decensored'],
                                  'colored': ['colored', 'coloured', 'color', 'colour'],
                                  'digital': ['digital']}

            return meta_patterns_list, tags_patterns_dict

        logging.info('START: parsing book filename to dict via regex for: {0}'.format(self.filename))

        # generate main and tag regex patterns and metadata dict
        meta_patterns_list, tags_patterns_dict = init_regex_patterns()
        meta_dict = {'circle': None, 'author': None, 'title': None, 'translation': None,
                     'decensored': None, 'colored': None, 'digital': None}

        if self.filename:
            try:
                # fill in main metadata
                for pattern in meta_patterns_list:
                    match = re.match(pattern, self.filename)
                    if match:
                        meta_dict.update((key, val) for key, val in match.groupdict().items())

                        # fill in tag metadata via dict comprehension
                        for tag in re.findall('[\[{]([^()]+?)[}\]]', self.filename):
                            match = {key: vals[0] for key, vals in tags_patterns_dict.items() if tag.lower() in vals}
                            if match:
                                meta_dict.update(match)

                        # final clean white issues
                        meta_dict.update((key, ' '.join(val.split())) for key, val in meta_dict.items() if val)

                        break

            except Exception as e:
                logging.critical(e)

        else:
            logging.info('WARN: no filename to parse: skipping')

        logging.info('FOUND: following meta components: {0}: '.format(meta_dict))
        logging.info('FINISH: parsing book filename to dict via regex: {0}'.format(self.filename))

        return meta_dict

    @staticmethod
    def get_most_similar_book(xml, meta_dict, thresh=0.70):
        logging.info('START: finding most similar dj.org title to parsed title: {0}'.format(meta_dict['title']))

        langs = ('NAME_EN', 'NAME_JP', 'NAME_R')
        title_xp = './{0}|./{1}|./{2}'
        item_xp = './/ITEM[@TYPE="{0}"]/{1}|.//ITEM[@TYPE="{0}"]/{2}|.//ITEM[@TYPE="{0}"]/{3}'

        best_book, best_list = None, []
        meta_count = sum(1 for key, val in meta_dict.items() if key in ['circle', 'author', 'title'] and val)

        if xml is not None:
            try:
                for elem in xml:
                    titles = [t.text if t.text else None for t in elem.xpath(title_xp.format(*langs))]
                    circles = [c.text if c.text else None for c in elem.xpath(item_xp.format('circle', *langs))]
                    authors = [a.text if a.text else None for a in elem.xpath(item_xp.format('author', *langs))]

                    xml_dict = {'title': titles, 'circle': circles, 'author': authors}

                    for key, vals in xml_dict.items():
                        if meta_dict[key]:
                            vals = vals if vals else [None]
                            compare = lambda a, b: seqm(None, a.lower(),
                                                        b.lower()).ratio()  # todo change to def compare(a,b): seqm(etc..
                            xml_dict[key] = max([compare(v, meta_dict[key]) if v else 0.0 for v in vals])
                        else:
                            xml_dict[key] = 0.0

                    avg = sum(xml_dict.values()) / meta_count
                    logging.info('INFO: similarity of {0} calculated'.format(avg))

                    if avg >= thresh:
                        best_list.append((elem, avg))

                if best_list:  # todo clean up code
                    best_list.sort(key=lambda tup: tup[1], reverse=True)
                    best_book = best_list[0][0]
                else:
                    logging.info('WARN: similarity too low for all matches: skipping')

            except Exception as elem:
                logging.critical(elem)

        else:
            logging.info('FINISH: no xml provided provided: skipping')

        logging.info('FINISH: finding most similar dj.org title to parsed title: {0}'.format(meta_dict['title']))

        return best_book

    def update_via_xml(self, xml, extra_tags=None):
        logging.info('START: updating book metadata in db via xml')

        if xml is not None:
            try:
                if self.version is None or self.version < xml.attrib['VER']:
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

        else:
            logging.warning('INFO: no xml provided: skipping')

        logging.info('FINISH: updating book metadata via xml')

    def refresh_meta_via_id(self, override_id=None):
        logging.info('START: refreshing book metadata via web_id: {0}'.format(self.web_id))

        web_id = override_id if override_id else self.web_id

        if web_id:
            url = '{0}/{1}/{2}{3}'.format(META_GENERAL, META_API, META_QUERY_ID, web_id)

            try:
                logging.info('INFO: fetching xml from dou.org for web_id: {0}.'.format(web_id))
                response = requests.get(url)
                tree = etree.fromstring(response.content)
                xml = tree.find('BOOK')

                if xml is not None:
                    logging.info('FOUND: found xml book from dou.org for web_id: {0}'.format(web_id))
                    self.update_via_xml(xml)
                else:
                    logging.info('WARN: nothing found on dou.org for web_id: {0}'.format(web_id))

            except Exception as e:
                logging.critical(e)

        else:
            logging.info('WARN: no web_id exists in db: skipping')

        logging.info('FINISH: refreshing book metadata via web_id: {0}'.format(self.web_id))

    def refresh_meta_via_filename(self, inc_matched=False):
        logging.info('START: refreshing book metadata via filename: {0}'.format(self.filename))

        if inc_matched or (not inc_matched and not self.web_id):
            if self.filename:
                meta_dict = self.parse_filename_to_dict()
                url = '{0}/{1}/{2}{3}{4}C:{5}A:{6}'.format(META_GENERAL, META_API, META_QUERY_OBJ, meta_dict['title'],
                                                           META_QUERY_LIST, meta_dict['circle'], meta_dict['author'])

                try:
                    logging.info('INFO: fetching xml from dou.org for filename: {0}.'.format(self.filename))
                    response = requests.get(url)
                    tree = etree.fromstring(response.content)
                    xml = tree.findall('BOOK')

                    if xml:
                        logging.info('FOUND: found xml books from dou.org for filename: {0}'.format(self.filename))
                        xml = self.get_most_similar_book(xml, meta_dict)
                        self.update_via_xml(xml, meta_dict)

                    else:
                        logging.info('WARN: nothing found on dou.org for filename: {0}'.format(self.filename))

                except Exception as e:
                    logging.critical(e)

            else:
                logging.info('WARN: no filename provided: skipping')

            logging.info('FINISH: refreshing book metadata via filename: {0}'.format(self.filename))

    def refresh_meta_via_image(self, inc_matched=False):
        logging.info('START: refreshing book metadata via cover image: {0}'.format(self.cover_thumb_lg.name))

        if inc_matched or (not inc_matched and not self.web_id):
            if self.cover_thumb_lg.name:
                if os.path.basename(self.cover_thumb_lg.name) != os.path.basename(DEFAULT_BOOK_IMG_PATH):
                    url = '{0}/{1}/{2}'.format(META_GENERAL, META_API, META_QUERY_IMG)

                    # TODO include ability to use webid?
                    if self.filename:
                        logging.info('INFO: using filename based info as similarity comparison to dou.org')
                        meta_dict = self.parse_filename_to_dict()

                        try:
                            logging.info(
                                'INFO: fetching xml from dou.org for image: {0}.'.format(self.cover_thumb_lg.name))
                            response = requests.post(url, files={'img': open(self.cover_thumb_lg.file.name, 'rb')})
                            tree = etree.fromstring(response.content)
                            xml = tree.findall('BOOK')

                            if xml:
                                logging.info(
                                    'FOUND: got xml books from dou.org for image: {0}'.format(self.cover_thumb_lg.name))
                                xml = self.get_most_similar_book(xml, meta_dict)
                                self.update_via_xml(xml, meta_dict)

                            else:
                                logging.info('WARN: nothing on dou.org for image: {0}'.format(self.cover_thumb_lg.name))

                        except Exception as e:
                            logging.critical(e)

                    else:
                        logging.info('WARN: no filename provided: skipping')

                else:
                    logging.info('WARN: cover image is default: skipping')

            else:
                logging.info('WARN: no cover image: skipping')

        logging.info('FINISH: refreshing book metadata via image: {0}'.format(self.cover_thumb_lg.name))

    def refresh_cover_image(self):
        logging.info('START: refreshing book cover image for id: {0}'.format(self.id))

        if self.filename and self.extension:
            zip_path = os.path.join(FOLDER_PATH, self.filename + self.extension)

            if os.path.isfile(zip_path):
                with ZipFile(zip_path, 'r') as zip:
                    filenames = sorted(zip.namelist())
                    filename = filenames[0] if filenames else None

                    if filename and filename[-1] != '/':
                        with zip.open(filename, mode='r') as img:
                            try:
                                content = ContentFile(img.read())
                                self.cover_thumb_lg.save('cov' + '_' + 'lg', content)

                                logging.info('FOUND: refreshed book cover image for id: {0}'.format(self.id))

                            except Exception as e:
                                logging.critical(e)

                    else:
                        logging.warning('WARN: folder detected in zip: skipping')

            else:
                logging.warning('WARN: zip path is not to a file: skipping')

        else:
            logging.warning('WARN: filename and extension not provided: skipping')

        logging.info('FINISH: refreshing book cover image for id: {0}'.format(self.id))

    def refresh_cover_palette(self):
        logging.info('START: getting color palette from cover via image: {0}'.format(self.cover_thumb_lg.name))

        if self.cover_thumb_lg.name:
            try:
                thief = ColorThief(self.cover_thumb_lg)
                colors = thief.get_palette(color_count=2, quality=1)
                colors = json.dumps(colors)

                if colors:
                    logging.info('FOUND: got color palette from cover via image: {0}'.format(self.cover_thumb_lg.name))
                    self.cover_palette = colors
                    self.save()

                else:
                    logging.info('WARN: no color palette: skipping')

            except Exception as e:
                logging.critical(e)

        else:
            logging.info('WARN: no cover image: skipping')

        logging.info('FINISH: getting color palette from cover via image: {0}'.format(self.cover_thumb_lg.name))

    def load_cover_palette_json(self):
        logging.info('START: loading/unpacking color palette from json for web_id: {0}'.format(self.web_id))

        colors = None

        if self.cover_palette:
            try:
                logging.info('FOUND: loaded color palette for web_id: {0}'.format(self.web_id))
                loaded = json.loads(self.cover_palette)
                colors = loaded

            except Exception as e:
                logging.critical(e)

        else:
            logging.info('WARN: no cover palette to load: skipping')

        logging.info('FINISH: loading/unpacking color palette from json for web_id: {0}'.format(self.web_id))

        return colors

    def refresh_page_images(self):
        logging.info('START: refreshing book page images for id: {0}'.format(self.id))

        if self.filename and self.extension:
            zip_path = os.path.join(FOLDER_PATH, self.filename + self.extension)

            if os.path.isfile(zip_path):
                with ZipFile(zip_path, 'r') as zip:
                    filenames = sorted(zip.namelist())

                    if filenames:
                        i = 0
                        for filename in filenames:
                            i += 1
                            file, ext = os.path.splitext(filename)

                            with zip.open(filename, mode='r') as img:
                                try:
                                    page, created = Page.objects.get_or_create(book=self, page_number=str(i),
                                                                               filename=file, extension=ext)
                                    if created:
                                        content = ContentFile(img.read())
                                        page.page_thumb_lg.save('pge' + '_' + 'lg', content)

                                        logging.info('FOUND: refreshed page image for id: {0}'.format(self.id))

                                except Exception as e:
                                    logging.critical(e)

                    else:
                        logging.warning('WARN: folder detected in zip: skipping')

            else:
                logging.warning('WARN: zip path is not to a file: skipping')

        else:
            logging.warning('WARN: filename and extension not provided: skipping')

        logging.info('FINISH: refreshing book cover image for id: {0}'.format(self.id))

    def concat_author_names(self):
        authors_raw = self.authors.all().values_list('name_en', 'name_jp', 'name_rj', flat=False)
        authors_list = []

        for author_tuple in authors_raw:
            name_en = author_tuple[0]
            name_jp = author_tuple[1]
            name_rj = author_tuple[2]

            if name_en:
                if name_jp:
                    author_name = name_en + ' ' + '(' + name_jp + ')'
                elif name_rj:
                    author_name = name_en + ' ' + '(' + name_rj + ')'
                else:
                    author_name = name_en + ' ' + '(' + 'N/A' + ')'
            else:
                author_name = None

            authors_list.append(author_name)

        return authors_list

    def get_language_from_code(self):
        if self.lang_orig == "2":
            return "English"
        elif self.lang_orig == "3":
            return "Japanese"
        elif self.lang_orig == "4":
            return "Chinese"
        elif self.lang_orig == "5":
            return "Korean"
        elif self.lang_orig == "6":
            return "French"
        elif self.lang_orig == "7":
            return "German"
        elif self.lang_orig == "8":
            return "Spanish"
        elif self.lang_orig == "9":
            return "Italian"
        elif self.lang_orig == "10":
            return "Russian"
        else:
            return None


class Page(models.Model):
    page_num = models.IntegerField(null=False, blank=False)
    width_orig = models.IntegerField(null=False, blank=False)
    height_orig = models.IntegerField(null=False, blank=False)
    orientation_orig = models.CharField(max_length=10, null=False, blank=False, default='portrait')
    is_cover = models.BooleanField(null=False, blank=False, default=False)
    is_viewed = models.BooleanField(null=False, blank=False, default=False)
    is_hidden = models.BooleanField(null=False, blank=False, default=False)
    filename = models.TextField(null=False, blank=False)
    extension = models.CharField(max_length=10, null=True, blank=True)
    page_thumb_lg = ProcessedImageField(upload_to=PAGE_IMG_LG_PATH, options={'quality': 95}, format='JPEG',
                                        processors=[Adjust(contrast=1.1, sharpness=1.1), SmartResize(420, 595)],
                                        null=True, blank=True, default=DEFAULT_BOOK_IMG_PATH)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    book = models.ForeignKey('Book', related_name='pages', on_delete=models.CASCADE)

    def refresh_page_image(self):
        logging.info('START: refreshing book page image for id: {0}'.format(self.id))

        if self.book.filename and self.book.extension:
            zip_path = os.path.join(FOLDER_PATH, self.book.filename + self.book.extension)

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



# scans book db and removes any book records that have since been removed
def clean_filenames(folder_path):
    logging.info('START: scanning db records with missing zip files in folder: {0}'.format(folder_path))

    for db_filename in Book.objects.values_list('filename', 'extension'):
        folder_file = os.path.join(FOLDER_PATH, db_filename[0] + db_filename[1])

        if not os.path.isfile(folder_file):
            Book.objects.filter(filename=db_filename[0], extension=db_filename[1]).delete()
            logging.info('FOUND: delete db record with no associated zip file : {0}'.format(db_filename[0]))

    logging.info('FINISH: scanning db record with missing zip files in folder: {0}'.format(folder_path))


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

