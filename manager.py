#!/usr/bin/env python3

import re
import time
import requests
import logging
import subprocess

logging.getLogger("requests").setLevel(logging.WARNING)


class DBManager:
    url = "http://www.wifionice.de/"

    def __init__(self, user_mode):
        self.user_mode = user_mode
        self.is_online = None
        if not user_mode:
            self.interface = self._get_correct_interface()
            self.mac_address = self._get_mac_from_interface(self.interface)
            if not self.mac_address:
                logging.warning('Could not get MAC address, Problem during interface recognition!')

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

    def _get_mac_from_interface(self, interface):
        """ Get MAC-address by calling ip link show and parsing that output """
        if interface:
            mac_string = self._get_mac_string_from_interface(interface)
            return self._get_mac_from_device(mac_string)

    @staticmethod
    def _get_mac_string_from_interface(interface):
        """ Wrap ip link and return the output """
        device_call = subprocess.run(['ip', 'link', 'show', interface], stdout=subprocess.PIPE)
        if device_call.returncode == 0:
            return device_call.stdout.decode().strip().split('\n')[-1].strip()

    @staticmethod
    def _get_mac_from_device(mac_string):
        """
        :param mac_string: The last line of ip link show $dev with the MAC in it
        :return: The MAC-address or None, if none is found
        """
        match_ = re.search(r'\s([0-9a-f]{2}:){5}([0-9a-f]{2})\s', mac_string)
        return match_.group(0).strip() if match_ else None

    def _get_correct_interface(self):
        """ Get the interface on which to connect to wifionice
        Check routing table for
        1. static routes to 172.16.0.1,
        2. default routes via 172.16.0.1
        to get the interface by the lowest metric
        """
        static_routes = self._get_static_routes()
        default_routes = self._get_default_routes()
        route_by_subnet = self._get_route_by_subnet()

        if static_routes:
            best_static_route = min(static_routes, key=lambda f: f[0])
            return self._get_interface_from_route(best_static_route[1])

        if default_routes:
            best_default_route = min(default_routes, key=lambda f: f[0])
            return self._get_interface_from_route(best_default_route[1])

        if route_by_subnet:
            best_route_by_subnet = min(route_by_subnet, key=lambda f: f[0])
            return self._get_interface_from_route(best_route_by_subnet[1])

        return None

    def _get_static_routes(self):
        """ Get all static routes to 172.16.0.1 """
        return self._filter_all_routes_by_re(re.compile(r'^172.16.0.1(/|\s)'))

    def _get_default_routes(self):
        """ Get all default routes via 172.16.0.1 """
        return self._filter_all_routes_by_re(re.compile(r'default\s+via\s172.16.0.1'))

    def _get_route_by_subnet(self):
        """ Get the specific interface route by the 172.16.0.0/16 subnet,
            At this point, there is no way to check if we're online, since we have no connection to wifionice
        """
        return self._filter_all_routes_by_re(re.compile(r'^172.16.0.0/16\s'))

    def _filter_all_routes_by_re(self, pattern):
        """
        :param pattern: Regular Expression pattern to filter the routes
        :return: A list of routes matching that pattern
        """
        all_routes = self._get_all_routes()
        return [(self._get_metric_from_route(route), route) for route in all_routes
                if pattern.search(route)]

    @staticmethod
    def _get_all_routes():
        """ Wrap call to ip ro and return a list of route-strings """
        all_routes = subprocess.run(['ip', 'ro'], stdout=subprocess.PIPE)
        if all_routes.returncode == 0:
            return all_routes.stdout.decode().split('\n')

    @staticmethod
    def _get_metric_from_route(route):
        """
        :param route: A route string from ip2
        :return: The route metric or 0, if there is none found
        """
        match_ = re.search(r'\smetric\s(\d+)\s', route)
        return int(match_.group(1)) if match_ else 0

    @staticmethod
    def _get_interface_from_route(route):
        """
        :param route: A route string from ip2
        :return: The device name or None, if there is none found
        """
        match_ = re.search(r'\sdev\s(\w+)\s', route)
        return match_.group(1) if match_ else None

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
    argparser = argparse.ArgumentParser(description="Easy Porn storage combining via webinterface")
    argparser.add_argument('-u', '--user_mode', action='store_true',
                           help='Run as unprivileged user, do everything possible without root')

    args = argparser.parse_args()

    logging.basicConfig(format='%(message)s',
                        level=logging.DEBUG)
    import pdb
    #pdb.set_trace()

    manager = DBManager(args.user_mode)
    try:
        manager.run()
    except (KeyboardInterrupt, EOFError):
        pass
