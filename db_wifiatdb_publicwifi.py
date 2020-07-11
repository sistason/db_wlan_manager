#!/usr/bin/env python3

import requests
import logging
import json
import re

logging.getLogger("requests").setLevel(logging.WARNING)


class DBWifiAtDBPublicWifi:
    URL = "public-wifi.deutschebahn.com"
    login_url = ""
#    api_host = "www.ombord.info"
#    api_host_limit = ""
#    api_site = "api/jsonp/user"

    def login(self):
        """ Log in to the Portal """
        logging.info('Trying to log in...')
        """First Call: (idk if necessary?)
        action	subscribe
type	one
connect_policy_accept	true
user_login	
user_password	
user_password_confirm	
email_address	
prefix	
phone	
policy_accept	false
gender	
interests	
"""
        """Second Call:
        action	authenticate
login	arw005o
password	5QMu7v6o
policy_accept	true
from_ajax	true
wispr_mode	false
        """
        #ret = self._make_request(self.login_url)
        #return ret and ret.ok

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



if __name__ == '__main__':
    w = DBWifiAtDBManager()
    w.update_online()
    print(w.is_online)
