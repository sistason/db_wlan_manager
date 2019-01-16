# Deutsche Bahn Wlan Manager

This program will monitor your wireless, 
and keep you logged into the different wlans of the DB 


## What's working?
- Keeps you logged in
- Keeping track of your spent data.


## What's not yet working?
- International/Some ICEs have a json-API for quota. 
I did not ride enough in those... 
- "Free @Bahnhofs Wlan"-Ding?

## How do you use it?
Start with: python3 manager.py
  
Use the flag -b for batch mode, which means it only tries 
to log you in and terminate.

### Network-Manager
To use it with network-manager, go to the network-manager directory and ```sudo ./install.sh```
If you connect with network-manager to a DB wifi, the tool will start in the background automatically and log the output to /var/log/dbwifi.

## Dependencies
- python3-dnspython
- python3-bs4 (beautifulsoup)

### Install Dependencies on Ubuntu
```sudo apt-get install python3 python3-bs4 python3-dnspython```
