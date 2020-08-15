# module imports
import logging


# handle messages for scripts > scan_local_content function
class ScanLocalContent:

    # start process
    @staticmethod
    def start(info):
        logging.info('START: scanning for new book zip files and pages in folder: {0}.'.format(info))

    # found - new book zip file found and added
    @staticmethod
    def book_added(info):
        logging.info('SUCCESS: new book zip file detected and added to db: {0}.'.format(info))

    # success - new page files added
    @staticmethod
    def pages_added(info):
        logging.info('SUCCESS: new page files detected and added to db: {0}.\n'.format(info))

    # warning - book already exists
    @staticmethod
    def warn_book_exists(info):
        logging.info('WARN: book zip already exists in db: {0}. Skipping book zip.\n'.format(info))

    # warning - no files in zip, or a folder detected
    @staticmethod
    def warn_folder_detected(info):
        logging.warning('WARN: no files and/or a folder detected in zip: {0}. Skipping zip.\n'.format(info))

    # warning - zip file not detected
    @staticmethod
    def warn_not_zip_file(info):
        logging.warning('WARN: file ({0}) is not of type .zip. Skipping zip.\n'.format(info))

    # end process
    @staticmethod
    def end(info):
        logging.info('FINISH: scanned new book zip files and pages in folder: {0}.\n'.format(info))


# handle messages for scripts > scan_local_content function
class ScanCheckListOfPageFiletypes:

    # warning - zip file not detected
    @staticmethod
    def warn_not_all_files_images():
        logging.warning('WARN: not all files in zip were image types. Excluded these from processing.')
