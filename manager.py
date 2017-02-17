#!/usr/bin/env python3

import re
import time
import logging
import requests
import subprocess


class DBManager:
    url = "http://www.wifionice.de/"

    def __init__(self, user_mode):
        self.user_mode = user_mode
        self.online = None
        if not user_mode:
            self.interface = self._get_correct_interface()
            self._backup_original_mac(self.interface)

    def run(self):
        while not time.sleep(1):
            self._is_online()
            if self.online:
                print('.', end=' ')
                continue
            self._login()

    def _is_online(self):
        """ Check if we are online. Don't change the state if the check fails itself """
        ret = self._do_request()
        if ret and ret.status_code == 200:
            if ret.text.count('offline') > 5:
                if self.online is True or self.online is None:
                    logging.info('I am not online anymore! :(')
                self.online = False
            if ret.text.count('online') > 5:
                if self.online is False or self.online is None:
                    logging.info('I am online again! :)')
                self.online = True
        else:
            logging.warning('Return object from wifionice broken!: {}'.format(ret))

    def _login(self):
        """ Log in to the ICE Portal (wifionice) """
        logging.info('Trying to log in...')
        data = {}
        ret = self._do_request(url_suffix='?login', post=True, data=data)

    def _backup_original_mac(self, interface):
        mac_string = self._get_mac_string_from_interface(interface)
        self.mac_address = self._get_mac_from_device(mac_string)

    def _get_mac_string_from_interface(self, interface):
        """ Wrap ip link and return the output """
        device_call = subprocess.run(['ip', 'link', 'show', interface], stdout=subprocess.PIPE)
        if device_call.returncode == 0:
            return device_call.stdout.decode().strip().split('\n')[-1].strip()

    def _get_mac_from_device(self, mac_string):
        """
        :param mac_string: The last line of ip link show $dev with the MAC in it
        :return: The MAC-address or None, if none is found
        """
        match_ = re.search(r'', mac_string)#TODO
        return match_.group(0) if match_ else None

    def _get_correct_interface(self):
        """ Get the interface on which to connect to wifionice
        Check routing table for
        1. static routes to 172.16.0.1,
        2. default routes via 172.16.0.1
        to get the interface by the lowest metric
        """
        static_routes = self._get_static_routes()
        default_routes = self._get_default_routes()

        if static_routes:
            best_static_route = max(static_routes, key=lambda f: f[0])
            return self._get_interface_from_route(best_static_route[1])

        if default_routes:
            best_default_route = max(default_routes, key=lambda f: f[0])
            return self._get_interface_from_route(best_default_route[1])

        return None

    def _get_static_routes(self):
        """ Get all static routes to 172.16.0.1 """
        return self._filter_all_routes_by_re(re.compile(r'^172.16.0.1(/|\s)'))

    def _get_default_routes(self):
        """ Get all default routes via 172.16.0.1 """
        return self._filter_all_routes_by_re(re.compile(r'default\s+via\s172.16.0.1'))

    def _filter_all_routes_by_re(self, pattern):
        """
        :param pattern: Regular Expression pattern to filter the routes
        :return: A list of routes matching that pattern
        """
        all_routes = self._get_all_routes()
        return [(self._get_metric_from_route(route), route) for route in all_routes
                if pattern.search(route)]

    def _get_all_routes(self):
        """ Wrap call to ip ro and return a list of route-strings """
        all_routes = subprocess.run(['ip', 'ro'], stdout=subprocess.PIPE)
        if all_routes.returncode == 0:
            return all_routes.stdout.decode().split('\n')

    def _get_metric_from_route(self, route):
        """
        :param route: A route string from ip2
        :return: The route metric or 0, if there is none found
        """
        match_ = re.search(r'\smetric\s(\d+)\s', route)
        return int(match_.group(0)) if match_ else 0

    def _get_interface_from_route(self, route):
        """
        :param route: A route string from ip2
        :return: The device name or None, if there is none found
        """
        match_ = re.search(r'\sdev\s(\w)\s', route)
        return match_.group(0) if match_ else None

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
                logging.debug('Caught Exception "{}" while making a get-request to "{}"'.format(e.__class__, url))
                break
            retries -= 1


if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description="Easy Porn storage combining via webinterface")
    argparser.add_argument('-u', '--user_mode', action='store_true',
                           help='Run as unprivileged user, do everything possible without root')

    args = argparser.parse_args()

    logging.basicConfig()
    logging.basicConfig(format='%(funcName)-23s: %(message)s',
                            level=logging.DEBUG)
    import pdb
    pdb.set_trace()

    manager = DBManager(args.user_mode)
    try:
        manager.run()
    except (KeyboardInterrupt, EOFError):
        pass
