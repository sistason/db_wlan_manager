import re
import time
import logging
import subprocess
import random


class Interface:
    TRANSITION_TIME = 60 # it is never to late to transition ;)

    def __init__(self, mac=None, ip=None):
        self.last_randomize = 0
        if mac:
            self.original_mac_address = mac
            self.interface_name = self._get_correct_interface(mac)
        elif ip:
            self.original_mac_address, self.interface_name = self._get_original_mac(ip)
        else:
            self.original_mac_address, self.interface_name = None, None

        if self.interface_name is None:
            logging.info('Wifi-connection most likely broken')

    def close(self):
        """ Leave the interface with the MAC it had when this script started """
        if self._get_mac() != self.original_mac_address:
            self._set_mac(self.original_mac_address)

    def randomize_mac(self):
        """ Randomize a MAC-address and set it """
        if time.time() < self.last_randomize + self.TRANSITION_TIME:
            return
        self.last_randomize = time.time()
        new_mac = ':'.join(["{:2}".format(str(hex(random.randrange(16*16)))[2:]) for _ in range(6)])
        return self._set_mac(new_mac)

    def _set_mac(self, mac):
        """ Set the supplied MAC-address to our interface """
        if not mac:
            return
        int_down_call = subprocess.run(['ip', 'link', 'set', self.interface_name, 'down'], stderr=subprocess.PIPE)
        if int_down_call.returncode:
            logging.error('Could not get the interface down: {}'.format(int_down_call.stderr))
            return
        mac_call = subprocess.run(['ip', 'link', 'set', self.interface_name, 'address', mac], stderr=subprocess.PIPE)
        int_up_call = subprocess.run(['ip', 'link', 'set', self.interface_name, 'up'], stderr=subprocess.PIPE)
        if mac_call.returncode:
            logging.error('Could not change MAC-address {}: {}'.format(mac, mac_call.stderr))
        elif int_up_call.returncode:
            logging.error('Could not get the interface back up: {}'.format(int_up_call.stderr))
        else:
            return True

    def _get_original_mac(self, ip):
        """ Get the original MAC-address by calling ip ro get on the IP of the API"""
        device_call = subprocess.run(['ip', 'ro', 'get', ip], stdout=subprocess.PIPE)
        if device_call.returncode == 0:
            output = device_call.stdout.decode().strip()
            interface = output[output.find('dev')+3:output.find('src')].strip()
            return self._get_mac_from_device(self._get_mac_string_from_interface(interface)), interface

    def _get_mac(self):
        """ Get MAC-address by calling ip link show and parsing that output """
        if self.interface_name:
            mac_string = self._get_mac_string_from_interface(self.interface_name)
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
        if not mac_string:
            return 
        match_ = re.search(r'\s([0-9a-f]{2}:){5}([0-9a-f]{2})\s', mac_string)
        return match_.group(0).strip() if match_ else None

    def _get_correct_interface(self, mac):
        """ Get the interface on which to connect to wifionice """
        interfaces = self._get_all_interfaces()
        for interface in interfaces:
            match = re.search(r'(?s)^(?P<interface>[^:]+):.*link/ether (?P<mac>[\dabcdef:]+) ', interface)
            if match:
                iface_, mac_ = match.group('iface'), match.group('mac')
                if mac_ == mac:
                    return iface_

    @staticmethod
    def _get_all_interfaces():
        """ Wrap call to ip link and return a list of interface-strings """
        all_interfaces = subprocess.run(['ip', 'link', 'show'], stdout=subprocess.PIPE)
        if all_interfaces.returncode == 0:
            return re.split(r'(?m)[\n]\d+: ', '\n'+all_interfaces.stdout.decode())[1:]
