import base64
import re
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class Browser:
    def __init__(self, username, password, blackboard_url=None):
        logger.info('Initiating')

        self.blackboard_url = blackboard_url or 'https://lms.curtin.edu.au/webapps/login/'
        self.username = username
        self.password = base64.b64encode(password.encode('utf-8'))

        self.b = requests.session()
        self.units = []

    def login(self):
        logger.info('Logging in')
        payload = {
                'login': 'Login',
                'action': 'login',
                'user_id': user,
                'encoded_pw': password,
                }

        r = self.b.post(self.blackboard_url, data=payload)

        soup = BeautifulSoup(r.text, 'html.parser')
        for link in soup.find_all('a'):
            l = link.get('href')
            course = re.search(r'\?type=Course&id=_(.*)_1&url', l)
            if course is None:
                continue
            else:
                print(course.groups())
            # if l.startswith(' /webapps/blackboard/execute/launcher?type=Course'):
            #   l = l.replace(' /webapps/blackboard/execute/launcher?type=Course&id=_'
            #           , '')
            #   l = l.replace('_1&url=', '')



