#!/usr/bin/env python3

import requests
import logging
import json
import re

logging.getLogger("requests").setLevel(logging.WARNING)



class DBWifiAtDBManager:
    SSID = "Wifi@DB"
    login_url = "wifi-bahn.de/connect.php"
    api_host = "www.ombord.info"
#    api_host_limit = ""
    api_site = "api/jsonp/user"

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

    def get_id(self):
        ret = self._make_request(self.login_url)
        if ret and ret.ok:
            result = re.search(r'https://{}/{}/\?callback=(jQuery.*?)">'.format(self.api_host, self.api_site), ret.text)
            if result:
                return result.group(1).replace('&amp;', '&')

    def update_online_api(self):
        id_ = self.get_id()
        return True #FIXME: not able to get quota, but any request against the login_url logs in, so...
        print(id_)
        status = self._get_status_from_api(id_)
        if status.get('online') == "1":
            self.update_quota(status)
            return True

#    def update_quota(self):
#        ret = self._make_request('{}/{}'.format(self.api_host_limit, 'portal/api/vehicle/gateway/data/limit'))
#       if ret and ret.status_code == 200:
#            try:
#                api_response = ret.json()
#                quota = api_response.get('usedAmount', 0)
#                limit = api_response.get('totalLimit', 1)
#                if type(quota) is int and type(limit) is int:
#                    self.quota = float('{:.2f}'.format(1.0*quota/limit))
#            except Exception as e:
#                logging.exception('Error while updating quote: {}'.format(e))
#                return

    def _get_status_from_api(self, id_):
        ret = self._make_request('{}/{}/?callback={}'.format(self.api_host, self.api_site, id_), protocol="https")
        print(ret.request.url)
        print(ret.text)
        if ret and ret.ok:
            print(ret.text)
            return ret.json()
        return {}

    def login(self):
        """ Log in to the Portal """
        logging.info('Trying to log in...')
        ret = self._make_request(self.login_url)
        return ret and ret.ok


if __name__ == '__main__':
    w = DBWifiAtDBManager()
    w.update_online()
    print(w.is_online)
