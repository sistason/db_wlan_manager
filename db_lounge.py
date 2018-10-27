#!/usr/bin/env python3

import re
import requests
import logging

logging.getLogger("requests").setLevel(logging.WARNING)


class DBLoungeManager:
    SSID = "DBLounge"
    api_host = "www.hotsplots.de"
    api_site = "/auth/login.php"


    def __init__(self):
        self.quota = None

        self.is_online = None

        self.session = requests.Session()
        self.challenge = None
        
        # No custom DNS here, since DBLounges have non-equal address-spaces

    def get_quota(self):
        return int(self.quota*100) if self.quota else 0

    def _make_request(self, url, protocol='https'):
        try:
            return self.session.get('{}://{}'.format(protocol, url), timeout=5)
        except requests.Timeout:
            return False
        except requests.ConnectionError as e:
            logging.warning('Connection Error: {}'.format(e))
            return False

    def update_online(self):
        #TODO: call mozilla-success? and let ourself be redirected to hotspot with all data
        ret = self._make_request(self.api_host + self.api_site)
        on = False
        if ret and ret.status_code == 200:
            on = "kostenlos einloggen" in ret.text.lower()
            self.challenge = self._get_challenge(ret.text)

        if on is False:
            if self.is_online is True or self.is_online is None:
                logging.info('I am not online anymore! :(')
            self.is_online = False
        elif on is True:
            if self.is_online is False or self.is_online is None:
                logging.info('I am online again! :)')
            self.is_online = True

    def _get_challenge(self, text):
        print(text)
        search = re.search('name="challenge" value="([0-9a-f]+)"', text)
        if search:
            pos = search.group(0)
            print(pos)
            return pos

    def update_quota(self, user):
        if type(user) is dict:
            quota = user.get('data_download_used', '')
            limit = user.get('data_download_limit', '')
            if quota.isdigit() and limit.isdigit():
                self.quota = 1.0*quota/limit
        else:
            ret = self._make_request('{}/{}'.format(self.api_host, self.api_site), protocol='http')
            if ret:
                try:
                    self.quota = float(ret.text)
                except ValueError:
                    pass

    def login(self):
        """ Log in to the Lounge Portal """
        logging.info('Trying to log in...')
        data = {
            "haveTerms": 1,
            "termsOK": True,
            "button": "kostenlos einloggen",
            "custom": 1,
            "ll": "de",
            "myLogin": "agb",
            "nasid":	"db-lounge-ffm025", #FIXME
            "uamip":    "192.168.64.1",
            "uamport":  80,
            "userurl":  "http://localhost.localdomain",
            "challenge": self.challenge
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        try:
            ret = self.session.post('https://{}/{}'.format(self.api_host, self.api_site),
                                    data=data, headers=headers)
            print(ret.text)
        except requests.exceptions.ConnectionError:
            logging.debug('Login Failed, probably bad wifi')

    def resolve_url(self, url):
        rrset = self.resolver.query(url).rrset
        return rrset.items[0].address if rrset.items else None
