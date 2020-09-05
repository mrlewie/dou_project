# module imports
import requests
from lxml import html, etree, objectify
from difflib import SequenceMatcher as seqm

# script imports
from dou.scripts import log_messages as log
from dou.scripts import local_data as local

# globals
META_GENERAL = 'http://doujinshi.mugimugi.org/api'
META_API = '96f9cd021a9125919d78'  # 'be519952736a525a4816' mrlewie / mrlew
META_QUERY_ID = '?S=getID&ID='
META_QUERY_IMG = '?S=imageSearch'
META_QUERY_OBJ = '?S=objectSearch&sn='
META_QUERY_LIST = '&slist='


# # # PRIMARY FUNCTIONS
# fetches book metadata xml for a single doujinshi.org web id
def fetch_meta_xml_via_web_id(web_id):
    """
    :param web_id: a doujinshi.org web id value used to search the doujinshi.org api.
    :return: a single matching xml object, or none.
    """

    log.FetchMetadataXmlViaWebId.start(info=web_id)  # log
    xml = None

    if web_id:
        try:
            log.FetchMetadataXmlViaWebId.fetch_xml(info=web_id)  # log

            url = '{0}/{1}/{2}{3}'.format(META_GENERAL, META_API, META_QUERY_ID, web_id)
            response = requests.get(url)
            tree = etree.fromstring(response.content)
            xml = tree.find('BOOK')

            if xml is not None:
                log.FetchMetadataXmlViaWebId.found_xml(info=web_id)  # log
            else:
                log.FetchMetadataXmlViaWebId.warn_no_meta_for_web_id_found(info=web_id)  # log

        except Exception as e:
            log.FetchMetadataXmlViaWebId.exception_during_meta_fetch(info=e)  # log
    else:
        log.FetchMetadataXmlViaWebId.warn_no_web_id_provided()  # log

    log.FetchMetadataXmlViaWebId.end(info=web_id)  # log
    return xml


# fetches book metadata xml from doujinshi.org for a single filename
def fetch_meta_xml_via_filename(filename):
    log.FetchMetadataXmlViaFilename.fetch_xml(info=filename)
    xmls = None

    if filename:
        meta_dict = local.convert_filename_to_meta_dict(filename=filename)

        if meta_dict:
            try:
                log.FetchMetadataXmlViaFilename.fetch_xml(info=filename)

                url = '{0}/{1}/{2}{3}{4}C:{5}A:{6}'.format(META_GENERAL, META_API, META_QUERY_OBJ,
                                                           meta_dict['title'], META_QUERY_LIST,
                                                           meta_dict['circle'], meta_dict['author'])
                response = requests.get(url)
                tree = etree.fromstring(response.content)
                xmls = tree.findall('BOOK')

                if xmls is not None:
                    log.FetchMetadataXmlViaFilename.found_xml(info=filename)
                else:
                    log.FetchMetadataXmlViaFilename.warn_no_meta_for_filename_found(info=filename)

            except Exception as e:
                log.FetchMetadataXmlViaFilename.exception_during_meta_fetch(info=e)
        else:
            log.FetchMetadataXmlViaFilename.warn_no_metadata_dict_provided()
    else:
        log.FetchMetadataXmlViaFilename.warn_no_filename_provided()

    log.FetchMetadataXmlViaFilename.end(info=filename)
    return xmls


# fetches book metadata xmls by matching a cover image to doujinshi.org archive
def fetch_meta_xml_via_cover_image(cover_img_path):
    """
    :param cover_img_path: a django static path and filename to cover image for doujinshi.org api.
    :return: a list of xml objects fetched via the doujinshi.org api, or none.
    """

    log.FetchMetadataXmlViaCoverImage.start(info=cover_img_path)
    xmls = None

    if cover_img_path and 'default' not in cover_img_path:
        try:
            log.FetchMetadataXmlViaCoverImage.fetch_xml(info=cover_img_path)

            url = '{0}/{1}/{2}'.format(META_GENERAL, META_API, META_QUERY_IMG)
            response = requests.post(url, files={'img': open(cover_img_path, 'rb')})
            tree = etree.fromstring(response.content)
            xmls = tree.findall('BOOK')

            if xmls is not None:
                log.FetchMetadataXmlViaCoverImage.found_xml(info=cover_img_path)
            else:
                log.FetchMetadataXmlViaCoverImage.warn_no_meta_for_cover_image_found(info=cover_img_path)

        except Exception as e:
            log.FetchMetadataXmlViaCoverImage.exception_during_meta_fetch(info=e)
    else:
        log.FetchMetadataXmlViaCoverImage.warn_no_cover_image_provided()

    log.FetchMetadataXmlViaCoverImage.end(info=cover_img_path)
    return xmls


# # # SECONDARY FUNCTIONS
# take an xml of potential books, find most similar, return as single xml book
def select_most_similar_xml_book(xmls, known_title, min_accuracy=0.7):
    """
    :param xmls: a list of xml objects fetched from doujinshi.org api.
    :param known_title: a book title filename. used to match against titles in list of xmls.
    :param min_accuracy: the minimum accuracy allowed when matching a book.
    :return: a single matching xml object, or none.
    """

    log.SelectMostSimilarXmlBook.start(info=known_title)
    xml, web_id = None, None
    max_ratio = 0.0

    if known_title:
        if xmls is not None:
            log.SelectMostSimilarXmlBook.find_highest_match(info=known_title)

            for elem in xmls:
                try:
                    title_list = [
                        elem.findtext('NAME_EN'),
                        elem.findtext('NAME_JP'),
                        elem.findtext('NAME_R')
                    ]

                    for title in title_list:
                        if title:
                            match = seqm(isjunk=None, a=title.lower(), b=known_title.lower())
                            ratio = round(match.ratio(), 2)

                            if ratio > max_ratio:
                                web_id = elem.attrib['ID']
                                max_ratio = round(ratio, 2)

                except Exception as e:
                    log.SelectMostSimilarXmlBook.exception_during_accuracy_calc(info=e)

            if web_id and max_ratio >= min_accuracy:
                for elem in xmls:
                    if elem.attrib['ID'] == web_id:
                        log.SelectMostSimilarXmlBook.found_match(info=max_ratio)
                        xml = elem
            else:
                log.SelectMostSimilarXmlBook.warn_no_match_found(info=known_title)
        else:
            log.SelectMostSimilarXmlBook.warn_no_xmls_provided()
    else:
        log.SelectMostSimilarXmlBook.warn_no_title_provided()

    log.SelectMostSimilarXmlBook.end(info=known_title)
    return xml


# convert a metadata singular xml object from doujinshi.org into a clean dict
def convert_meta_xml_to_dict(xml):
    """
    :param xml: a single matching xml object.
    :return: a single dictionary of metadata converted from a xml obtained from doujinshi.org api.
    """

    log.ConvertMetaXmlToDict.start()
    meta_dict = {}

    if xml is not None:
        try:
            meta_obj = objectify.fromstring(etree.tostring(xml))
            meta_dict = {
                'web_id':           meta_obj.attrib['ID'],
                'version':          int(meta_obj.attrib['VER']),
                'name_en':          meta_obj['NAME_EN'].text,
                'name_jp':          meta_obj['NAME_JP'].text,
                'name_rj':          meta_obj['NAME_R'].text,
                'released':         meta_obj['DATE_RELEASED'].text,
                'num_pages_orig':   int(meta_obj['DATA_PAGES'].text),
                'num_pages_user':   None,
                'lang_orig':        int(meta_obj['DATA_LANGUAGE'].text),
                'lang_user':        0,
                'is_adult':         int(meta_obj['DATA_AGE'].text),
                'is_anthology':     int(meta_obj['DATA_ANTHOLOGY'].text),
                'is_decensored':    0,
                'is_colored':       0,
                'is_digital':       0,
                'convention':       [],
                'type':             [],
                'circle':           [],
                'publisher':        [],
                'author':           [],
                'parody':           [],
                'contents':         []
            }

            item_types = ['convention', 'type', 'circle', 'publisher',
                          'author', 'parody', 'contents']

            for item_type in item_types:
                for elem in meta_obj['LINKS'].iterchildren():
                    if elem.attrib['TYPE'] == item_type:
                        temp_dict = {
                            'web_id':   elem.attrib['ID'],
                            'version':  int(elem.attrib['VER']),
                            'type':     elem.attrib['TYPE'],
                            'name_en':  elem['NAME_EN'].text,
                            'name_jp':  elem['NAME_JP'].text,
                            'name_r':   elem['NAME_R'].text
                        }
                        meta_dict[item_type].append(temp_dict)

            log.ConvertMetaXmlToDict.parsed_meta_to_dict(info=meta_dict['web_id'])

        except Exception as e:
            log.ConvertMetaXmlToDict.exception_during_meta_unpack(e)
    else:
        log.ConvertMetaXmlToDict.warn_no_xml_provided()

    log.ConvertMetaXmlToDict.end()
    return meta_dict

