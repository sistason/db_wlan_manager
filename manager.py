#!/usr/bin/env python3

import time
import logging
import subprocess

from db_lounge import DBLoungeManager
from db_wifionice import DBWifiOnICEManager


class DBManager:
    managers = {
        DBLoungeManager.SSID: DBLoungeManager,
        DBWifiOnICEManager.SSID: DBWifiOnICEManager
    }
    manager = None

    def __init__(self, batch_mode=False, ssid=""):
        self.batch_mode = batch_mode
        if ssid:
            manager = self.managers.get(ssid)
            if manager:
                self.manager = manager()

        logging.basicConfig(level=logging.WARNING if batch_mode else logging.INFO)

        self.is_online = None
        self.new_api = None

    def run(self):
        if self.batch_mode:
            self.manager = self.get_login_manager()
            if not self.manager:
                return

            iteration_ = 5
            while iteration_ > 0:
                self.manager.update_online()
                print('DB: !' if not self.manager.is_online else 'DB: {:.0%}'.format(self.manager.get_quota()))
                if self.manager.is_online:
                    return
                else:
                    self.manager.login()

                time.sleep(1)

                iteration_ -= 1
        else:
            while not time.sleep(1):
                self.manager = self.get_login_manager()
                if not self.manager:
                    continue

                self.manager.update_online()
                if self.manager.is_online:
                    quota = self.manager.get_quota()
                    if quota < 1:
                        print('.{}'.format(quota), end='', flush=True)
                    else:
                        print("Quota surpassed, your traffic is being slowed! MAC-Change suggested")
                elif self.manager.is_online is None:
                    continue
                else:
                    self.manager.login()

    def get_login_manager(self):
        if self.manager is not None:
            return self.manager

        interface_ssids = []
        res = subprocess.run(['/bin/ip', 'a'], stdout=subprocess.PIPE)
        up_interfaces = [l.split(b':')[1].strip() for l in res.stdout.split(b'\n') if b"state UP" in l]
        for interface in up_interfaces:
            res = subprocess.run(['/sbin/iw', 'dev', interface, 'link'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            iw_result = res.stdout.decode('utf-8')
            for line in iw_result.split('\n'):
                if line.startswith('command failed'):
                    break
                if 'ssid' in line.lower():
                    interface_ssids.append(line.strip().split()[-1])
                    break

        for ssid in interface_ssids:
            manager = self.managers.get(ssid)
            if manager is None:
                continue

            if type(manager) is type:
                # If not yet in instanciated, do
                manager = manager()
                self.managers[ssid] = manager
            return manager


if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description="Keeps your Wifi logged into the various DB Wifis")
    argparser.add_argument('-b', '--batch', action='store_true',
                           help='Just check status and login, if not yet.')
    argparser.add_argument('ssid', nargs="?", type=str, help="If you already know the SSID and it's not gonna change")

    args = argparser.parse_args()

    db_manager = DBManager(batch_mode=args.batch, ssid=args.ssid)
    try:
        db_manager.run()
    except (KeyboardInterrupt, EOFError):
        pass
