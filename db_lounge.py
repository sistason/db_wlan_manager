#!/usr/bin/env python3

import requests
import logging
import dns.resolver

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

        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = ['192.168.96.1']
        self.api_host_ip = self.resolve_url(self.api_host)

    def get_quota(self):
        return int(self.quota*100) if self.quota else 0

    def _make_request(self, url, protocol='https'):
        try:
            return self.session.get('{}://{}'.format(protocol, url), timeout=5, verify=False)
        except requests.Timeout:
            return False
        except requests.ConnectionError as e:
            logging.warning('Connection Error: {}'.format(e))
            return False

    def update_online(self):
        ret = self._make_request(self.api_host_ip + self.api_site)
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
        search_string = 'name="challenge" value="'
        pos = text.find(search_string)
        return text[pos+len(search_string): pos+len(search_string)+32]

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
        }
        try:
            ret = self.session.post('https://{}/{}'.format(self.api_host_ip, self.api_site),
                                    data=data)
        except requests.exceptions.ConnectionError:
            logging.debug('Login Failed, probably bad wifi')

    def resolve_url(self, url):
        rrset = self.resolver.query(url).rrset
        return rrset.items[0].address if rrset.items else None
