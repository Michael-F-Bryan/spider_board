import mimetypes
import string
from urllib.parse import urljoin
import sys
import base64
import re
import requests
from bs4 import BeautifulSoup
import logging
import os
from collections import namedtuple
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from .utils import time_job, LOG_FILE, get_logger, humansize



# Create the logging handlers and attach them
logger = get_logger(__name__, LOG_FILE)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)


class Attachment:
    ALLOWED_CHARS = string.ascii_letters + string.digits + '[]()_-.#$%&*+~;:='

    def __init__(self, title, url, section):
        self.title = title
        self.url = url
        self.data = None
        self.section = section

    def sanitise(self, name):
        temp = []
        name = name.replace(' ', '_')

        for c in name:
            if c in Attachment.ALLOWED_CHARS:
                temp.append(c)

        return ''.join(temp)

    @property
    def filename(self):
        """
        Sanitise the title and turn it into a full blown (relative) filename.
        """
        path = []
        
        current_section = self.section
        while True:
            if current_section.parent_section is None:
                path.append(current_section.title)
                path.append(current_section.unit.name)
                break

            path.append(current_section.title)
            current_section = current_section.parent_section

        full_path = self.sanitise(self.title)
        for folder in path:
            full_path = os.path.join(self.sanitise(folder), full_path)

        return str(full_path)

    def __repr__(self):
        return '<Attachment: title="{}">'.format(self.title)


class Section:
    def __init__(self, unit, title, url, parent_section=None):
        self.unit = unit
        self.title = title
        self.url = url
        self.parent_section = parent_section

    def __repr__(self):
        return '<Section: {}>'.format(self.title)

class Unit:
    def __init__(self, name, url, code):
        self.code = code
        self.url = url.strip()
        self.name = name

    def __repr__(self):
        return '<Unit: name="{}">'.format(self.name)
        

class Browser:
    SKIP_FOLDERS = [
            'Discussion Board',
            'Help for students',
            'Contacts',
            'Tools',
            'iPortfolio',
            'Communication',
            'Announcements',
            'My Grades',
            'Help for Students',
            ]

    def __init__(self, username, password, download_dir, blackboard_url=None, 
            threads=8, seq=False, max_size=10, force=False):
        message = '  Initiating Browser   '
        logger.info('='*len(message))
        logger.info(message)
        logger.info('='*len(message))

        self.blackboard_url = blackboard_url or 'https://lms.curtin.edu.au/'
        self.login_url = self.blackboard_url + 'webapps/login/'

        self.username = username
        self.password = base64.b64encode(password.encode('utf-8')) 
        self.download_dir = os.path.abspath(download_dir)
        self.force = force
        self.is_logged_in = False

        if max_size > 0:
            self.max_size = max_size*1024*1024 # Maximum download size in bytes
        else:
            self.max_size = 2*1024**3  # 2GB should be big enough...

        self.session = self.b = requests.session() 
        self.units = []

        # The two "task" queues
        self.sections = Queue()
        self.documents = Queue()

        self.sequential = seq
        self.threads = threads

        self.download_sizes = []

    def login(self):
        logger.info('Logging in')
        payload = {
                'login': 'Login',
                'action': 'login',
                'user_id': self.username,
                'encoded_pw': self.password,
                }

        # Do the login
        r = self.b.post(self.login_url, data=payload)

        if 'You are being redirected to another page' in r.text:
            logger.info('Login was successful')
            self.is_logged_in = True
            self.run_hook('on_login_successful')
        else:
            logger.error('Login failed')
            self.run_hook('on_login_failed')

    def get_units(self):
        url = self.blackboard_url + 'webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_3_1'

        r = self.b.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        course_links = []
        for link in soup.find_all('a'):
            # Because Blackboard is shit, you need to do a hack in order to
            # find all unit names
            href = link.get('href')
            course = re.search(r'\?type=Course&id=_(.*)_1&url', href)

            if course is None:
                continue
            else:
                name = link.text
                code = course.group(1)
                l = urljoin(self.blackboard_url, href.strip()) 

                new_unit = Unit(name=name, url=l, code=code)
                logger.debug('Unit found: {}'.format(new_unit))

                self.units.append(new_unit)

        self.run_hook('on_get_units')

    def _scrape_unit(self, unit):
        logger.info('Scraping all documents for unit: {}'.format(unit))
        
        r = self.b.get(unit.url)
        soup = BeautifulSoup(r.text, 'html.parser')

        sidebar = soup.find(id='courseMenuPalette_contents')
        links = sidebar.find_all('a')

        for link in links:
            title = link.span['title']
            
            if title in Browser.SKIP_FOLDERS:
                continue

            # Skip ilectures
            if 'echo' in title.lower():
                continue

            link = urljoin(self.blackboard_url, link['href'])
            new_section = Section(unit, title, link)
            logger.debug('Adding section: {}'.format(new_section))
            self.sections.put(new_section)

    def _scrape_section(self, section):
        logger.info('Scraping section: {}'.format(section))

        r = self.b.get(section.url)
        soup = BeautifulSoup(r.text, 'html.parser')

        folders = self._folders_in_section(soup, section)
        logger.debug('{} folders found for this section: {}'.format(len(folders),
                                                                  section))
        for folder in folders:
            self.sections.put(folder)

        files = self._files_in_section(soup, section)
        logger.debug('{} files found for this section: {}'.format(len(files), 
                                                                  section))
        for f in files:
            self.documents.put(f)
            
        # Call task_done() to notify the queue that a section has finished
        # Being scraped
        self.sections.task_done()

        return folders

    def _folders_in_section(self, soup, section):
        """
        Find all the nested folders in this section.
        """
        # This is a really dodgy way to do it. Not really any other option
        # Though because Blackboard's html isn't easy to work with
        magic_folder_link_contains = '/webapps/blackboard/content/listContent.jsp?' 
        content = soup.find(id='content')

        if content is None:
            print(section.url)
            import pdb
            pdb.set_trace()

        found_sections = []
        for link in content.find_all('a'):
            if magic_folder_link_contains in link['href']:
                unit = section.unit
                title = link.text.strip()
                url = urljoin(self.blackboard_url, link['href'])

                new_section = Section(unit, title, url, parent_section=section)
                logger.debug('Nested folder discovered: {}'.format(new_section))

                found_sections.append(new_section)

        return found_sections

    def _files_in_section(self, soup, section):
        # Check if there are any documents in this folder
        # (All attached files are in a list with the "attachments" class
        attached_files = soup.find_all(class_='attachments')

        file_list = []
        for attachment_list in attached_files:
            attachments = attachment_list.find_all('a')

            for attachment in attachments:
                url = urljoin(self.blackboard_url, attachment['href'])
                title = attachment.text.strip()
                new_attachment = Attachment(title, url, section)

                logger.debug('File discovered: {}'.format(new_attachment))

                file_list.append(new_attachment)
        return file_list

    def spider_sequential(self):
        self.login()
        self.get_units()

        for unit in self.units:
            if '[' not in unit.name:
                self._scrape_unit(unit)

        while not self.sections.empty():
            next_section = self.sections.get()
            self._scrape_section(next_section)

        logger.info('{} files found'.format(self.documents.qsize()))

    def _download(self, document):
        logger.info('Downloading "{}"'.format(document.title))

        save_location = os.path.join(self.download_dir, document.filename)
        parent_dir = os.path.dirname(save_location)

        if self._already_downloaded(save_location):
            logger.info('Skipping file: {}'.format(save_location))
            return

        content_headers = self.read_headers(document)
        
        # make the document's parent directories
        os.makedirs(parent_dir, exist_ok=True)

        # Start streaming the file and saving chunks to disk
        r = self.b.get(document.url, stream=True)

        if not r.ok:
            logger.error('Request Failed!')
            logger.error('URL: {}'.format(document.url))
            logger.error('Status code: {}'.format(r.status_code))
            logger.error(r.text)
            return

        # Check if there is a file extension, if not infer from request
        # context
        _, ext = os.path.splitext(save_location)
        if not ext:
            content_mimetype = r.headers['Content-Type']
            extension = mimetypes.guess_extension(content_mimetype)

            # In the face of ambiguity, refuse the temptation to guess
            if extension in ['.so', '.dll', '.exe', '.m', '.a']:
                extension = ''

            save_location = save_location + extension
            logger.debug('Guessed file extension "{}" for file: {}'.format(
                extension, save_location))

        if self._already_downloaded(save_location):
            logger.info('Skipping file: {}'.format(save_location))
            return

        file_size = int(r.headers['content-length'])
        if file_size > self.max_size:
            logger.warn('File too big: {}'.format(document))
            logger.warn('Size: {}'.format(humansize(file_size)))
            logger.warn('Proposed save location: {}'.format(save_location))
            return

        with open(save_location, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

        self.download_sizes.append(int(r.headers['content-length']))

    def _already_downloaded(self, save_location):
        # Check if the user wants to overwrite existing documents
        if os.path.exists(save_location):
            if self.force:
                return False
            else:
                return True
        else:
            return False

    def read_headers(self, document):
        r = requests.head(document.url,
                headers={'Accept-Encoding': 'identity'})

        return r.headers

    def download_files_sequential(self):
        logger.info('Now downloading files')
        
        while not self.documents.empty():
            try:
                next_document = self.documents.get()
                self._download(next_document)
            except KeyboardInterrupt:
                logger.info('Execution halted by user')
                logger.info('Last file to be downloaded: {}'.format(next_document))
                logger.info('Save location: {}'.format(next_document.filename))
                break

        logger.info('{} bytes downloaded'.format(sum(self.download_sizes)))

    def spider_concurrent(self):
        self.login()
        self.get_units()

        # Do the initial scrapes for each unit
        for unit in self.units:
            if '[' not in unit.name:
                fut = self.thread_pool.submit(self._scrape_unit, unit)
                self.futures.append(fut)

        # Wait so that we have some sections in the queue initially
        wait(self.futures, return_when=FIRST_COMPLETED)

        while not self.sections.empty():
            section = self.sections.get()

            # Tell the thread pool to scrape that section then add the
            # Future to a list 
            fut = self.thread_pool.submit(self._scrape_section, section)

            callback = lambda future: self._requeue(self._scrape_section, future)
            fut.add_done_callback(callback)

            self.futures.append(fut)

        self.sections.join()
        logger.info('{} files found'.format(self.documents.qsize()))

    def download_concurrent(self):
        logger.info('Now downloading the files')

        while not self.documents.empty():
            new_document = self.documents.get()
            fut = self.thread_pool.submit(self._download, new_document)

            callback = lambda future: self._requeue(self._download, future)
            fut.add_done_callback(callback)

            self.futures.append(fut)

    def _requeue(self, func, fut):
        """
        This function will iterate over the future's return value, submitting
        a new job to the thread pool with the value as it's only argument.
        Then it attaches a callback so that once *that* job is done, it'll do
        the same again until all the tasks are complete.
        
        In order to set it as a callback you need to do a small hack using 
        lambda functions. Initial use when queueing the function you want to
        be repeated::

            fut = self.thread_pool.submit(function_to_call_again, section)

            callback = lambda future: self._requeue(function_to_call_again, future)
            fut.add_done_callback(callback)

            self.futures.append(fut)
        """
        sections = fut.result()

        if not sections:
            return

        for section in sections:
            new_future = self.thread_pool.submit(func, section)

            callback = lambda future: self._requeue(func, future)
            new_future.add_done_callback(callback)

            self.futures.append(new_future)

    @time_job()
    def start_scraping(self):
        if self.sequential:
            self.spider_sequential()
            self.download_files_sequential()
        else:
            self.thread_pool = ThreadPoolExecutor(max_workers=self.threads)
            self.futures = []

            try:
                self.spider_concurrent()
                self.download_concurrent()
                wait(self.futures)
            except KeyboardInterrupt:
                logger.info('Execution halted by user')
                self.thread_pool.shutdown()

        self.run_hook('on_finish_downloads')
        bytes_downloaded = sum(self.download_sizes)
        logger.info('{} bytes downloaded'.format(humansize(bytes_downloaded)))

    def quit(self):
        # Run the "on_quit" function if it is defined
        self.run_hook('on_quit')

        logger.info('Shutting down thread pool and exiting...')
        self.thread_pool.shutdown()
        sys.exit(1)

    def run_hook(self, hook_name):
        """
        Run the function "self.hook_name()" if it exists.
        """
        hook = getattr(self, hook_name, None)
        if hook is not None:
            logger.info('Running hook {}.{}()'.format(self.__class__.__name__,
                                                      hook_name))
            hook(self)


