#!/usr/bin/env python3

import requests
import logging
import re

from db_wifiatdb_suewex import DBWifiAtDBSuewex
from db_wifiatdb_publicwifi import DBWifiAtDBPublicWifi

logging.getLogger("requests").setLevel(logging.WARNING)


class DBWifiAtDBDecider:
    """
    Wifi@DB is used by many different providers, only differing the captive portal.

    Therefore, we check the captive portal here to decide which provider works for
    the specific portal, if we know any.
    """
    SSID = "Wifi@DB"
    PROVIDERS = {
        DBWifiAtDBSuewex.URL: DBWifiAtDBSuewex,
        DBWifiAtDBPublicWifi.URL: DBWifiAtDBPublicWifi,
    }

    def get_specific_provider(self):
        ret = requests.get('detectportal.firefox.com/success.txt')
        if ret.ok:
            if ret.text == 'success':
                logging.warning('Already logged in, cannot determine which Portal we are connected to')
                return None

            base_url = re.search(r'https?://(.+)/', ret.url)
            if not base_url:
                logging.error('Cannot get base_url, portal is: {}'.format(ret.url))
                return None

            base_url = base_url.group(1)
            provider = self.PROVIDERS.get(base_url)
            if provider is None:
                logging.warning("No specific provider implemented yet for this WIFI@DB :(")
            return provider


if __name__ == '__main__':
    w = DBWifiAtDBDecider().get_specific_provider()()
    w.update_online()
    print(w.is_online)
