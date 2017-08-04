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
    url = "www.wifionice.de"
    api_url = "https://www.ombord.info/api/jsonp/user/"
    url_cached_ip = None
    new_api = None

    def __init__(self, user_mode):
        self.user_mode = user_mode
        self.is_online = None
        self.interface = None
        self.json_decoder = json.JSONDecoder()
        self.quota = (0, 0)

        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = ['172.16.0.1']
        self.url_cached_ip = self.resolve_url()

    def run(self):
        try:
            while not time.sleep(1):
                self.update_online()
                if self.is_online:
                    self.manage_bandwidth()
                    print('.', end='', flush=True)
                    continue
                self.login()
        except KeyboardInterrupt:
            pass
        finally:
            if self.interface is not None:
                self.interface.close()

    def manage_bandwidth(self):
        if self.quota == (0, 0):
            # Without quota (old website), this does not work
            return

        if self.quota[0] >= self.quota[1]:
            if self.user_mode:
                logging.info('Your traffic is being shaped, as you surpassed your data limit')
                logging.info('To automatically reset your data limit, run this script as root')
                return

            self.interface.randomize_mac()

    def _check_api(self):
        try:
            ret = requests.get(self.api_url, timeout=5)
            if ret.status_code == 404:
                self.new_api = False
                logging.debug('Using old API...')
            else:
                self.new_api = True
                logging.debug('Using new API...')
        except requests.ConnectionError as e:
            logging.debug('Connection Error: {}'.format(e))

    def update_online(self):
        if self.new_api is None:
            if self._check_api() is None:
                return

        on = self.update_online_with_api() if self.new_api else self.update_online_without_api()
        if on is False:
            if self.is_online is True or self.is_online is None:
                logging.info('I am not online anymore! :(')
            self.is_online = False
        elif on is True:
            if self.is_online is False or self.is_online is None:
                logging.info('I am online again! :)')
            self.is_online = True

    def update_online_without_api(self):
        """ Check if we are online. Don't change the state if the check fails itself """
        ret = requests.get('http://' + self.url_cached_ip + '/de/')
        if ret and ret.status_code == 200:
            txt = ret.text.lower()
            if txt.count('offline') > 5:
                return False
            if txt.count('online') > 5:
                return True
        else:
            print('?', end=' ', flush=True)
            logging.debug('Return object from wifionice broken!: {}'.format(ret))

    def update_online_with_api(self):
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
        quota = user.get('data_download_used', '')
        limit = user.get('data_download_limit', '')

        if quota.isdigit() and limit.isdigit():
            self.quota = (quota, limit)

    def _get_status_from_api(self):
        try:
            ret = requests.get(self.api_url, timeout=5)
            return self.json_decoder.decode(re.sub(r'[\n\(\); ]', '', ret.text)[:-2] + '}')
        except requests.ConnectTimeout:
            return {}
        except Exception as e:
            logging.error('Error getting API response, was {}'.format(ret.text))
            return {}

    def login(self):
        """ Log in to the ICE Portal (wifionice) """
        logging.info('Trying to log in...')
        data = {}
        suffix = '/de/?login'
        self._do_request(url_suffix=suffix, post=True, data=data)

    def _do_request(self, url_suffix='', post=False, data=None):
        """ Wrapper around the requests.get/post, for timeout/error handling"""
        if data is None:
            data = {}

        address = self.url_cached_ip if self.url_cached_ip else self.url

        retries = 3
        while retries > 0:
            try:
                if post:
                    return requests.post('http://'+address+url_suffix, data=data, timeout=2)
                else:
                    return requests.get('http://'+address+url_suffix, data=data, timeout=2)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logging.debug('Caught exception :( "{}"'.format(e))
                time.sleep(1)
            except Exception as e:
                logging.debug('Caught Exception "{}" while making a request'.format(e))
                break
            retries -= 1

    def resolve_url(self):
        rrset = self.resolver.query(self.url).rrset
        return rrset.items[0].address if rrset.items else None

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description="Keeps your Wifi logged into the Wifionice")
    argparser.add_argument('-u', '--user_mode', action='store_true',
                           help='Run as unprivileged user, do everything possible without root')

    args = argparser.parse_args()

    logging.basicConfig(format='%(message)s',
                        level=logging.DEBUG)

    manager = DBManager(args.user_mode)
    try:
        manager.run()
    except (KeyboardInterrupt, EOFError):
        pass
