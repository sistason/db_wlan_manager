# Deutsche Bahn Wlan Manager

This program will monitor your wireless, 
keep you logged into the Wlan of the train 
and will change your MAC when your data is drained.


## What's working?
- Keeps you logged in
- Getting the interface with which you're logged into 
ICE-Wlan and saving it's MAC address, to change it back 
later if it needed to be changed.

## What's not working?
- Changing the MAC address of the interface
- Reloading your Wifi (for new IP, req. plugins for NM/wpa_supp/...?)
- DNS. Getting the wifionice.de address by asking 172.16.0.1, not you primary DNS

## How do you use it?
Start with: python3 manager.py
  
Use the flag -u if the manager should run as the 
current user and won't do stuff requiring root 
privileges (like changing MAC address [not yet working!])