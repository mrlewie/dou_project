# module imports
import logging

# logging settings
logging.basicConfig(format='%(message)s', level=logging.INFO)


# handle messages for scripts > local_data
class ScanLocalContent:

    @staticmethod
    def start(info):
        logging.info('START: scanning for new book zip files and pages in folder: {0}.'.format(info))

    @staticmethod
    def book_added(info):
        logging.info('SUCCESS: new book zip file detected and added to db: {0}.'.format(info))

    @staticmethod
    def pages_added(info):
        logging.info('SUCCESS: new page files detected and added to db: {0}.\n'.format(info))

    @staticmethod
    def warn_book_exists(info):
        logging.info('WARN: book zip already exists in db: {0}. Skipping book zip.\n'.format(info))

    @staticmethod
    def warn_folder_detected(info):
        logging.warning('WARN: no files and/or a folder detected in zip: {0}. Skipping zip.\n'.format(info))

    @staticmethod
    def warn_not_zip_file(info):
        logging.warning('WARN: file ({0}) is not of type .zip. Skipping zip.\n'.format(info))

    @staticmethod
    def exception_during_page_creation(info):
        logging.warning(info)

    @staticmethod
    def end(info):
        logging.info('FINISH: scanned new book zip files and pages in folder: {0}.\n'.format(info))


# handle messages for scripts > local_data
class CheckListOfPageFiletypes:

    @staticmethod
    def warn_not_all_files_images():
        logging.warning('WARN: not all files in zip were image types. Excluded these from processing.')


# handle messages for scripts > local_data
class ConvertFilenameToMetaDict:

    @staticmethod
    def start():
        logging.info('START: converting filename tags to dict.')

    @staticmethod
    def found_meta(info):
        logging.info('SUCCESS: meta {0} detected and converted to dict.'.format(info))

    @staticmethod
    def found_tags(info):
        logging.info('SUCCESS: tags {0} detected and converted to dict.'.format(info))

    @staticmethod
    def warn_no_meta_detected():
        logging.info('WARN: no meta detected on filename. Skipping.'.format())

    @staticmethod
    def warn_no_tags_detected():
        logging.info('WARN: no tags detected on filename. Skipping.'.format())

    @staticmethod
    def warn_no_filename_provided():
        logging.warning('WARN: no filename provided. Skipping.')

    @staticmethod
    def exception_during_meta_unpack(info):
        logging.warning(info)

    @staticmethod
    def end():
        logging.info('FINISH: converted filename tags to dict.\n')


# handle messages for scripts > local_data
class CountBookPagesInZip:

    @staticmethod
    def start(info):
        logging.info('START: counting number of book pages in zip: {0}.'.format(info))

    @staticmethod
    def counted_pages(info):
        logging.info('SUCCESS: counted {0} pages in book.'.format(info))

    @staticmethod
    def warn_folder_detected(info):
        logging.warning('WARN: no files and/or a folder detected in zip: {0}. Skipping zip.\n'.format(info))

    @staticmethod
    def warn_not_zip_file(info):
        logging.warning('WARN: file ({0}) is not of type .zip. Skipping zip.\n'.format(info))

    @staticmethod
    def no_folder_or_filename(info):
        logging.warning('WARN: no folder or filename provided. Skipping.\n'.format(info))

    @staticmethod
    def end(info):
        logging.info('FINISH: counted number of book pages in zip: {0}.\n'.format(info))


# handle messages for scripts > web_data
class FetchMetadataXmlViaWebId:

    @staticmethod
    def start(info):
        logging.info('START: fetching doujinshi.org book xml metadata using web_id: {0}.'.format(info))

    @staticmethod
    def fetch_xml(info):
        logging.info('WORKING: beginning fetch request for web_id: {0}.'.format(info))

    @staticmethod
    def found_xml(info):
        logging.info('SUCCESS: found xml from doujinshi.org for web_id: {0}.'.format(info))

    @staticmethod
    def warn_no_meta_for_web_id_found(info):
        logging.warning('WARN: nothing found on doujinshi.org for web_id: {0}.'.format(info))

    @staticmethod
    def warn_no_web_id_provided():
        logging.warning('WARN: no web_id provided. Skipping.')

    @staticmethod
    def exception_during_meta_fetch(info):
        logging.warning(info)

    @staticmethod
    def end(info):
        logging.info('FINISH: obtained doujinshi.org book xml metadata using web_id: {0}.\n'.format(info))


# handle messages for scripts > web_data
class FetchMetadataXmlViaFilename:

    @staticmethod
    def start(info):
        logging.info('START: fetching doujinshi.org book xml metadata using filename: {0}.'.format(info))

    @staticmethod
    def fetch_xml(info):
        logging.info('WORKING: beginning fetch request for filename: {0}.'.format(info))

    @staticmethod
    def found_xml(info):
        logging.info('SUCCESS: found xml from doujinshi.org for filename: {0}.'.format(info))

    @staticmethod
    def warn_no_meta_for_filename_found(info):
        logging.warning('WARN: nothing found on doujinshi.org for filename: {0}.'.format(info))

    @staticmethod
    def warn_no_metadata_dict_provided():
        logging.warning('WARN: no metadata dictionary provided. Skipping.')

    @staticmethod
    def warn_no_filename_provided():
        logging.warning('WARN: no filename provided. Skipping.')

    @staticmethod
    def exception_during_meta_fetch(info):
        logging.warning(info)

    @staticmethod
    def end(info):
        logging.info('FINISH: obtained doujinshi.org book xml metadata using filename: {0}.\n'.format(info))



# handle messages for scripts > web_data
class FetchMetadataXmlViaCoverImage:

    @staticmethod
    def start(info):
        logging.info('START: fetching doujinshi.org book xml metadata using cover image: {0}.'.format(info))

    @staticmethod
    def fetch_xml(info):
        logging.info('WORKING: beginning xml fetch request for cover image: {0}.'.format(info))

    @staticmethod
    def found_xml(info):
        logging.info('SUCCESS: found xml from doujinshi.org for cover image: {0}.'.format(info))

    @staticmethod
    def warn_no_meta_for_cover_image_found(info):
        logging.warning('WARN: nothing found on doujinshi.org for cover image: {0}.'.format(info))

    @staticmethod
    def warn_no_cover_image_provided():
        logging.warning('WARN: no cover image or default cover image provided. Skipping.')

    @staticmethod
    def exception_during_meta_fetch(info):
        logging.warning(info)

    @staticmethod
    def end(info):
        logging.info('FINISH: obtained doujinshi.org book xml metadata using cover image: {0}.\n'.format(info))


# handle messages for scripts > web_data
class SelectMostSimilarXmlBook:

    @staticmethod
    def start(info):
        logging.info('START: selecting most similar xml in xmls from doujinshi.org for filename" {0}.'.format(info))

    @staticmethod
    def find_highest_match(info):
        logging.info('WORKING: looking through xmls for best match for filename : {0}.'.format(info))

    @staticmethod
    def found_match(info):
        logging.info('SUCCESS: found best match in xmls with {0}% accuracy.'.format(info))

    @staticmethod
    def warn_no_match_found(info):
        logging.warning('WARN: no match was found on doujinshi.org for filename: {0}.'.format(info))

    @staticmethod
    def warn_no_xmls_provided():
        logging.warning('WARN: no xml or xml list provided. Skipping.')

    @staticmethod
    def warn_no_title_provided():
        logging.warning('WARN: no known title provided. Skipping.')

    @staticmethod
    def exception_during_accuracy_calc(info):
        logging.warning(info)

    @staticmethod
    def end(info):
        logging.info('FINISH: obtained doujinshi.org book xml for filename: {0}.\n'.format(info))


# handle messages for scripts > web_data
class ConvertMetaXmlToDict:

    @staticmethod
    def start():
        logging.info('START: converting metadata xml to dict.')

    @staticmethod
    def parsed_meta_to_dict(info):
        logging.info('SUCCESS: xml metadata converted to dict for web_id: {0}.'.format(info))

    @staticmethod
    def warn_no_xml_provided():
        logging.warning('WARN: no metadata xml provided: skipping.')

    @staticmethod
    def exception_during_meta_unpack(info):
        logging.warning(info)

    @staticmethod
    def end():
        logging.info('FINISH: converted metadata xml to dict.\n')


