#YouTube Downloader

This python program periodically checks youtube for new videos in a users subscription feed. It will then move it to a designated folder with a video thumbnail and a channel poster. 

This was designed to work with Plex and this [plugin] (https://github.com/ZeroQI/YouTube-Agent.bundle) and this [scanner] (https://github.com/ZeroQI/Absolute-Series-Scanner)

Please download and install both if using with Plex.

##Install

To install first download this repo, in the upper right of this repo click 'Download zip

Download python [here] (https://www.python.org/ftp/python/3.5.4/python-3.5.4.exe) currently Python 3.5 is supported but should work with other versions of Python (2.* and 3.*)

**When installing make sure to click 'Add to PATH'**

After installing python open a command prompt or terminal and copy this

'''
pip install -r requirements.txt
'''

Make sure there are no errors, then copy and paste this

'''
python setup.py
'''

If its your first time installing select '1'

If you have a new subcription you want to add you can select '2' to go through this process again


This program will need you to setup a youtube api key, by following this guide https://www.slickremix.com/docs/get-api-key-for-youtube/

It will then ask whether you want to select which channels you want included or include all the channels. 

If you have a lot of subscriptions (like me) then I recommend chosing to include all of them then opening data/youtubeData.xml when the setup is complete and deleting the whole line for whichever channel(s) you dont want to download.

If you have a fairly smallish amount of subscriptions then you can chose the 'select' opiton and it will ask you for each channel if you want to include it or not

It will then take you through some config options

##Running

I'm working on a better way to run it right now but for now type this into a terminal or command prompt

'''
python main.py
'''

Remember the first time you run it, it will take a long time to download everything so be patient
