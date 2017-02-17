#!/usr/bin/env python3

import time
import logging
import requests


class DBManager:
    url = "http://www.wifionice.de/"

    def __init__(self, user_mode):
        self.user_mode = user_mode

    def run(self):

        while not time.sleep(1):
            if self._is_online():
                print('I am online! :)')
                continue
            print('I am not online! :(')

            pass

    def _is_online(self):
        """ Check if we are online """
        ret = self._do_request()
        if not ret or ret.status_code != 200 or ret.text.count('offline') > 4:
            return False
        return True

    def _login(self):
        """ Log in to the ICE Portal (wifionice) """
        data = {}
        ret = self._do_request(post=True, data=data)

    def _do_request(self, post=False, data=None):
        """ Wrapper around the requests.get/post, for timeout/error handling"""
        if data is None:
            data = {}

        retries = 3
        while retries > 0:
            try:
                if post:
                    return requests.post(self.url, data=data, timeout=2)
                else:
                    return requests.get(self.url, data=data, timeout=2)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                time.sleep(1)
            except Exception as e:
                logging.debug('Caught Exception "{}" while making a get-request to "{}"'.format(e.__class__, url))
                break
            retries -= 1


if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description="Easy Porn storage combining via webinterface")
    argparser.add_argument('-u', '--user_mode',
                           help='Run as unprivileged user, do everything possible without root')

    args = argparser.parse_args()

    manager = DBManager(args.user_mode)
    manager.run()