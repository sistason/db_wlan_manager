#!/usr/bin/env python3

import requests
import logging
import json
import re

from db_generic_manager import DBManager

logging.getLogger("requests").setLevel(logging.WARNING)


class DBWifiAtDBSuewex(DBManager):
    URL = "wifi-bahn.de"
    login_url = "wifi-bahn.de/connect.php"
    api_host = "www.ombord.info"
#    api_host_limit = ""
    api_site = "api/jsonp/user"

    def login(self):
        """ Log in to the Portal """
        logging.info('Trying to log in...')
        ret = self._make_request(self.login_url)
        return ret and ret.ok

    def _update_online_api(self):
        id_ = self._get_id()
        return True #FIXME: not able to get quota, but any request against the login_url logs in, so...
        print(id_)
        status = self._get_status_from_api(id_)
        if status.get('online') == "1":
            self.update_quota(status)
            return True

    def _get_id(self):
        ret = self._make_request(self.login_url)
        if ret and ret.ok:
            result = re.search(r'https://{}/{}/\?callback=(jQuery.*?)">'.format(self.api_host, self.api_site), ret.text)
            if result:
                return result.group(1).replace('&amp;', '&')


#    def update_quota(self):
# Example API Callback
    """jQuery311013181348935550807_1533860865681({
    "version":"1.9",
    "ip":"172.16.47.224",
    "mac":"18:1D:EA:AB:E9:51",
    "online":"40991",
    "timeleft":"40991",
    "authenticated":"1",
    "userclass":"2",
    "expires":"Thu Dec 26 22:26:52 2019",
    "timeused":"2209",
    "data_download_used":"9987703",
    "data_upload_used":"12925372",
    "data_total_used":"22913075",
    "data_download_limit":"0",
    "data_upload_limit":"0",
    "data_total_limit":"52428800",
    "bandwidth_download_limit":"81250",
    "bandwidth_upload_limit":"81250",
    "cap_level":"0"
});"""
#        ret = self._make_request('{}/{}'.format(self.api_host_limit, 'portal/api/vehicle/gateway/data/limit'))
#       if ret and ret.status_code == 200:
#            try:
#                api_response = ret.json()
#                quota = api_response.get('usedAmount', 0)
#                limit = api_response.get('totalLimit', 1)
#                if type(quota) is int and type(limit) is int:
#                    self.quota = float('{:.2f}'.format(1.0*quota/limit))
#            except Exception as e:
#                logging.exception('Error while updating quote: {}'.format(e))
#                return

    def _get_status_from_api(self, id_):
        ret = self._make_request('{}/{}/?callback={}'.format(self.api_host, self.api_site, id_), protocol="https")
        print(ret.request.url)
        print(ret.text)
        if ret and ret.ok:
            print(ret.text)
            return ret.json()
        return {}
