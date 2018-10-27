# Deutsche Bahn Wlan Manager

This program will monitor your wireless, 
and keep you logged into the different wlans of the DB 


## What's working?
- Keeps you logged in
- Keeping track of your spent data.


## What's not yet working?
- DB Lounge Autologin. Not enough waiting time in there.
- International/Some ICEs have a json-API for quota. 
I did not ride enough in those... 


## How do you use it?
Start with: python3 manager.py
  
Use the flag -b for batch mode, which means it only tries 
to log you in and terminate.

## Dependencies
- python3-dnspython