# get primary colors from an image
"""
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
"""


# load cover palette json for using in palette generation
"""
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
"""


# concat author names
"""
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
"""


# old regex meanings
"""
s = '\s'
start = '^'
con = '\((.*?)\)'
cir_and_aut = '\[(?P<circle>.*?)\((?P<author>.*?)\)\]'
cir_or_aut = '\[(?P<author>[^()]+)\]'
ttl = '(?P<title>[^(\[{]+)'

meta_patterns_list = [start + con + s + cir_and_aut + s + ttl, 
                      start + con + s + cir_or_aut + s + ttl,
                      start + cir_and_aut + s + ttl, 
                      start + cir_or_aut + s + ttl, start + ttl]
"""


# refresh page images for a particular book
"""
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
"""


# read zips and extract
"""
import os
from zipfile import ZipFile

dir = r'D:\Projects\Dou\Doujinshi_working'
for filename in os.listdir(dir):
    if filename.endswith('.zip'):
        filepath = os.path.join(dir, filename)

        with ZipFile(filepath, 'r') as zip:
            folder_name = os.path.splitext(filename)[0]
            zip.extractall(os.path.join(dir, folder_name))
            print('Extracted: ' + folder_name)
"""