#!/usr/bin/env python3

import time
import logging

from db_lounge import DBLoungeManager
from db_wifionice import DBWifiOnICEManager


class DBManager:
    managers = {
        DBLoungeManager.SSID: DBLoungeManager,
        DBWifiOnICEManager.SSID: DBWifiOnICEManager
    }

    def __init__(self, batch_mode=False):
        self.batch_mode = batch_mode
        logging.basicConfig(level=logging.WARNING if batch_mode else logging.INFO)

        self.is_online = None
        self.new_api = None

    def run(self):
        if self.batch_mode:
            self.manager = self.get_login_manager()
            iteration_ = 5
            while iteration_ > 0:
                self.manager.update_online()
                print('DB: !' if not self.manager.is_online else 'DB: {:.0%}'.format(self.manager.get_quota()))
                if self.manager.is_online:
                    return
                else:
                    self.manager.login()

                iteration_ -= 1
        else:
            while not time.sleep(1):
                self.manager = self.get_login_manager()
                self.manager.update_online()
                if self.manager.is_online:
                    quota = self.manager.get_quota()
                    if quota < 100:
                        print('.{}'.format(quota), end='', flush=True)
                    else:
                        print("Quota surpassed, your traffic is being slowed! MAC-Change suggested")
                elif self.manager.is_online is None:
                    continue
                else:
                    self.manager.login()

    def get_login_manager(self):
        ssid = "WIFIonICE"   # TODO
        manager = self.managers.get(ssid)
        if manager is None:
            return

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

    args = argparser.parse_args()

    manager = DBManager(batch_mode=args.batch)
    try:
        manager.run()
    except (KeyboardInterrupt, EOFError):
        pass
