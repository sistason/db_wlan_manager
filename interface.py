import re
import logging
import subprocess


class Interface:

    def __init__(self):
        self.name = self._get_correct_interface()
        if self.name is None:
            logging.info('Wifi-connection most likely broken')
        self.mac_address = self._get_mac_from_interface(self.name)
        if not self.mac_address:
            logging.warning('Could not get MAC address')

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
