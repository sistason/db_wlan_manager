#!/usr/bin/env python3

import bs4
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
        self.last_portal_soup = None
        
        # No custom DNS here, since DBLounges have non-equal address-spaces

    def get_quota(self):
        return self.quota if self.quota else 0

    def _make_request(self, url, protocol='https'):
        try:
            return self.session.get('{}://{}'.format(protocol, url), timeout=5)
        except requests.Timeout:
            return None
        except requests.ConnectionError as e:
            logging.warning('Connection Error: {}'.format(e))
            return None

    def update_online(self):
        ret = self._make_request("detectportal.firefox.com/success.txt", protocol="http")
        if ret is None:
            return
        if ret.text.strip() == 'success':
            if self.is_online is False or self.is_online is None:
                logging.info('I am online again! :)')
            self.is_online = True
        else:
            if self.is_online is True or self.is_online is None:
                logging.info('I am not online anymore! :(')
            self.is_online = False
            self.last_portal_soup = bs4.BeautifulSoup(ret.text, 'lxml')

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

        data = {item.attrs.get('name'): item.attrs.get('value')
                for item in self.last_portal_soup.find_all('input', attrs={'type': 'hidden'})}

        data['termsOK'] = True
        data["button"] = "kostenlos einloggen"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        print(data)
        print("""
        button	kostenlos+einloggen
challenge	fad088b67b2026c20d3d87d9a64d4afd
custom	1
haveTerms	1
ll	de
myLogin	agb
nasid	db-lounge-bln006
termsOK	on
uamip	192.168.44.1
uamport	80
userurl	http://detectportal.firefox.com/success.txt""")
        try:
            ret = self.session.post('https://{}/{}'.format(self.api_host, self.api_site),
                                    data=data, headers=headers)
            print(ret.text)
        except requests.exceptions.ConnectionError:
            logging.debug('Login Failed, probably bad wifi')
