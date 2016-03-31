from urllib.parse import urljoin
import sys
import base64
import re
import requests
from bs4 import BeautifulSoup
import logging
import os
from collections import namedtuple

LOG_FILE = os.path.abspath('scraper_log.log')

# Create the logging handlers and attach them
logger = logging.getLogger(__name__)

stream_handler = logging.StreamHandler()

file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s: %(message)s",
        datefmt='%Y/%m/%d %I:%M:%S %p')

file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

logger.setLevel(logging.DEBUG)


Section = namedtuple('Section', ['unit_code', 'title', 'url'])

class Section:
    def __init__(self, unit_code, title, url):
        self.unit_code = unit_code
        self.title = title
        self.url = url
        self.scraped = False

    def __repr__(self):
        return '<Section: {}>'.format(self.title)

class Unit:
    def __init__(self, name, url, code):
        self.code = code
        self.url = url.strip()
        self.name = name
        self.folders = []
        self.documents = []

    def __repr__(self):
        return '<Unit: name="{}">'.format(self.name)
        

class Browser:
    SKIP_FOLDERS = [
            'Discussion Board',
            'Contacts',
            'Tools',
            'iPortfolio',
            'Communication',
            'Announcements',
            'My Grades',
            'Help for Students',
            ]

    def __init__(self, username, password, blackboard_url=None):
        logger.info('Initiating')

        self.blackboard_url = blackboard_url or 'https://lms.curtin.edu.au/'
        self.login_url = self.blackboard_url + 'webapps/login/'

        self.username = username
        self.password = base64.b64encode(password.encode('utf-8')) 
        self.b = requests.session() 
        self.units = []

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
        else:
            logger.error('Login failed')
            self.quit()

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

            new_section = Section(unit.code, title, link['href'])
            logger.debug('Adding section: {}'.format(new_section))
            unit.folders.append(new_section)

    def quit(self):
        sys.exit(1)

