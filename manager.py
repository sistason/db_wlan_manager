#!/usr/bin/env python3

import time
import requests
import logging

from interface import Interface

logging.getLogger("requests").setLevel(logging.WARNING)


class DBManager:
    url = "http://www.wifionice.de/"

    def __init__(self, user_mode):
        self.user_mode = user_mode
        self.is_online = None
        self.interface = None
        if not user_mode:
            self.interface = Interface()

    def run(self):
        while not time.sleep(1):
            self.update_online()
            if self.is_online:
                print('.', end=' ', flush=True)
                continue
            self.login()

    def update_online(self):
        """ Check if we are online. Don't change the state if the check fails itself """
        ret = self._do_request()
        if ret and ret.status_code == 200:
            if ret.text.count('offline') > 5:
                if self.is_online is True or self.is_online is None:
                    logging.info('I am not online anymore! :(')
                self.is_online = False
            if ret.text.count('online') > 5:
                if self.is_online is False or self.is_online is None:
                    logging.info('I am online again! :)')
                self.is_online = True
        else:
            logging.warning('Return object from wifionice broken!: {}'.format(ret))

    def login(self):
        """ Log in to the ICE Portal (wifionice) """
        logging.info('Trying to log in...')
        data = {}
        self._do_request(url_suffix='?login', post=True, data=data)

    def _do_request(self, url_suffix='', post=False, data=None):
        """ Wrapper around the requests.get/post, for timeout/error handling"""
        if data is None:
            data = {}

        retries = 3
        while retries > 0:
            try:
                if post:
                    return requests.post(self.url+url_suffix, data=data, timeout=2)
                else:
                    return requests.get(self.url+url_suffix, data=data, timeout=2)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logging.debug('Caught exception :( "{}"'.format(e))
                time.sleep(1)
            except Exception as e:
                logging.debug('Caught Exception "{}" while making a request'.format(e))
                break
            retries -= 1


if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description="Keeps your Wifi logged into the Wifionice")
    argparser.add_argument('-u', '--user_mode', action='store_true',
                           help='Run as unprivileged user, do everything possible without root')

    args = argparser.parse_args()

    logging.basicConfig(format='%(message)s',
                        level=logging.DEBUG)
    # import pdb
    # pdb.set_trace()

    manager = DBManager(args.user_mode)
    try:
        manager.run()
    except (KeyboardInterrupt, EOFError):
        pass
