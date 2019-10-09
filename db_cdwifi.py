#!/usr/bin/env python3

import requests
import logging
import json
import re

logging.getLogger("requests").setLevel(logging.WARNING)


class DBCDWiFiManager:
    SSID = "CDWiFi"
    api_host = "www.info.cdwifi.cz"
    api_host_limit = "cdwifi.cz"
    api_site = "api/jsonp/connectivity"

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
        on = self.update_online_api()
        if on is False:
            if self.is_online is True or self.is_online is None:
                logging.info('I am not online anymore! :(')
            self.is_online = False
        elif on is True:
            if self.is_online is False or self.is_online is None:
                logging.info('I am online again! :)')
            self.is_online = True

    @staticmethod
    def _get_csrf(text):
        search_string = 'name="CSRFToken" value="'
        pos = text.find(search_string)
        return text[pos+len(search_string): pos+len(search_string)+32]

    def update_online_api(self):
        status = self._get_status_from_api()
        if status.get('online') == "1":
            self.update_quota()
            return True

    def update_quota(self):
        ret = self._make_request('{}/{}'.format(self.api_host_limit, 'portal/api/vehicle/gateway/data/limit'))
        if ret and ret.status_code == 200:
            try:
                api_response = ret.json()
                quota = api_response.get('usedAmount', 0)
                limit = api_response.get('totalLimit', 1)
                if type(quota) is int and type(limit) is int:
                    self.quota = float('{:.2f}'.format(1.0*quota/limit))
            except Exception as e:
                logging.exception('Error while updating quote: {}'.format(e))
                return

    def _get_status_from_api(self):
        ret = self._make_request('{}/{}'.format(self.api_host, self.api_site))
        if ret and ret.status_code == 200:
            return self.json_decoder.decode(re.sub(r'[\n\(\); ]', '', ret.text[1:-2]))
        return {}

    def login(self):
        """ Log in to the ICE Portal (wifionice) """
        logging.info('Trying to log in...')
        try:
            ret = self.session.post('http://{}/{}'.format(self.api_host, 'portal/api/vehicle/gateway/user/authenticate'))
            if ret.status_code in [200, 500]:   # yes, apparently 500 is okay, too ;)
                return True
        except requests.exceptions.ConnectionError:
            logging.debug('Login Failed, probably bad wifi')


if __name__ == '__main__':
    w = DBCDWiFiManager()
    w.update_online()
    print(w.is_online)