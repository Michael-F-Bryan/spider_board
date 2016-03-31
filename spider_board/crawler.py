import sys
import base64
import re
import requests
from bs4 import BeautifulSoup
import logging
import os

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


class Browser:
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
        url = 'https://lms.curtin.edu.au/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_3_1'

        r = self.b.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        for link in soup.find_all('a'):
            l = link.get('href')
            course = re.search(r'\?type=Course&id=_(.*)_1&url', l)
            if course is None:
                continue
            else:
                code = course.group(1)
                self.units.append(code)
                logger.debug('Unit found, code: {}'.format(code))

    def quit(self):
        sys.exit(1)

