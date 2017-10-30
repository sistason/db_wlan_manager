#!/usr/bin/env python3

import time
import requests
import logging
import dns.resolver
import json
import re

from interface import Interface

logging.getLogger("requests").setLevel(logging.WARNING)


class DBManager:
    api_host = "www.wifionice.de"
    api_site = "usage_info/"
    api_host_new = "www.ombord.info"
    api_site_new = "api/jsonp/user"

    def __init__(self, user_mode):
        self.user_mode = user_mode
        self.interface = None
        self.quota = None

        self.is_online = None
        self.new_api = None

        self.json_decoder = json.JSONDecoder()
        self.session = requests.Session()
        self.csrf_token = None

        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = ['172.16.0.1']
        self.api_host_ip = self.resolve_url(self.api_host)
        self.api_host_new_ip = self.resolve_url(self.api_host_new)

    def run(self):
        try:
            while not time.sleep(1):
                self.update_online()
                if self.is_online:
                    self.manage_bandwidth()
                    print('.', end='', flush=True)
                elif self.is_online is None:
                    continue
                else:
                    self.login()
        except KeyboardInterrupt:
            pass
        finally:
            if self.interface is not None:
                self.interface.close()

    def manage_bandwidth(self):
        if self.quota is None:
            # Without quota (old website), this does not work
            return

        if self.quota >= 1:
            if self.user_mode:
                logging.info('Your traffic is being shaped, as you surpassed your data limit')
                logging.info('To automatically reset your data limit, run this script as root')
                return

            self.interface.randomize_mac()

    def _make_request(self, url, protocol='https'):
        try:
            return self.session.get('{}://{}'.format(protocol, url), timeout=5, verify=False)
        except requests.Timeout:
            return False
        except requests.ConnectionError as e:
            logging.debug('Connection Error: {}'.format(e))
            return False

    def _check_api(self):
        logging.info('Checking API version...')
        ret = self._make_request(self.api_host_new_ip)
        if ret is not None:
            if ret and ret.status_code != 404 and len(ret.text) > 60:
                self.new_api = True
                logging.info('Using new API.')
            else:
                self.new_api = False
                logging.info('Using old API.')

        return self.new_api

    def update_online(self):
        if self.new_api is None:
            if self._check_api() is None:
                print('api none')
                return

        on = self.update_online_new_api() if self.new_api else self.update_online_old_api()
        if on is False:
            if self.is_online is True or self.is_online is None:
                logging.info('I am not online anymore! :(')
            self.is_online = False
        elif on is True:
            if self.is_online is False or self.is_online is None:
                logging.info('I am online again! :)')
            self.is_online = True

    def update_online_old_api(self):
        """ Check if we are online. Don't change the state if the check fails itself """
        ret = self._make_request('{}/de/'.format(self.api_host_ip), protocol='http')
        if ret and ret.status_code == 200:
            if 'Data meter header' in ret.text:
                self.update_quota(ret.text)

            self.csrf_token = self._get_csrf(ret.text)

            txt = ret.text.lower()
            if txt.count('offline') > 5:
                return False
            if txt.count('online') > 5:
                return True
        else:
            print('?', end=' ', flush=True)
            logging.debug('Return object from wifionice broken!: {}'.format(ret))

    @staticmethod
    def _get_csrf(text):
        search_string = 'name="CSRFToken" value="'
        pos = text.find(search_string)
        return text[pos+len(search_string): pos+len(search_string)+32]

    def update_online_new_api(self):
        """
        "version":"1.9", "ip":"172.16.100.116", "mac":"6C:88:14:84:84:88", "online":"0", "timeleft":"0",
        "authenticated":"1", "userclass":"2", "expires":"Never", "timeused":"1206", "data_download_used":"9256202",
        "data_upload_used":"4302103", "data_total_used":"13558305", "data_download_limit":"209715200",
        "data_upload_limit":"0", "data_total_limit":"0", "bandwidth_download_limit":"81250",
        "bandwidth_upload_limit":"81250", "cap_level":"0"
        """
        status = self._get_status_from_api()
        print(status)
        if self.interface is None and len(status.get('mac', '')) == 17:
            # Interface uninitialized
            self.interface = Interface(status.get('mac'))

        self.update_quota(status)

        return status.get('online') == "1"

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

    def _get_status_from_api(self):
        ret = self._make_request('{}/{}'.format(self.api_host_new_ip, self.api_site_new))
        if ret and ret.status_code == 200:
            return self.json_decoder.decode(re.sub(r'[\n\(\); ]', '', ret.text)[:-2] + '}')
        return {}

    def login(self):
        """ Log in to the ICE Portal (wifionice) """
        logging.info('Trying to log in...')
        ret = self.session.post('http://{}/de/?login'.format(self.api_host_ip),
                                data={'login': True, 'CSRFToken': self.csrf_token})

    def resolve_url(self, url):
        rrset = self.resolver.query(url).rrset
        return rrset.items[0].address if rrset.items else None

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description="Keeps your Wifi logged into the Wifionice")
    argparser.add_argument('-u', '--user_mode', action='store_true',
                           help='Run as unprivileged user, do everything possible without root')

    args = argparser.parse_args()

    logging.basicConfig(format='%(message)s',
                        level=logging.INFO)

    manager = DBManager(args.user_mode)
    try:
        manager.run()
    except (KeyboardInterrupt, EOFError):
        pass
