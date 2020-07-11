import requests
import json
import logging


class DBManager:
    """
    The Interface all managers have to comply to.
    """
    def __init__(self):
        self.quota = None

        self.is_online = None

        self.json_decoder = json.JSONDecoder()
        self.session = requests.Session()
        self.csrf_token = None

    def get_quota(self):
        return self.quota if self.quota else 0

    def _make_request(self, url, protocol='http'):
        try:
            return self.session.get('{}://{}'.format(protocol, url), timeout=5, verify=False)
        except requests.Timeout:
            return False
        except requests.ConnectionError as e:
            logging.warning('Connection Error: {}'.format(e))
            return False

    def update_online(self):
        on = self._update_online_api()
        if on is False:
            if self.is_online is True or self.is_online is None:
                logging.info('I am not online anymore! :(')
            self.is_online = False
        elif on is True:
            if self.is_online is False or self.is_online is None:
                logging.info('I am online again! :)')
            self.is_online = True

    def login(self):
        return NotImplementedError

    def _update_online_api(self):
        return NotImplementedError
