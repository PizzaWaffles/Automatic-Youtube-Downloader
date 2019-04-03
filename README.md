![Build Status](https://travis-ci.com/Dannyman3819/Automatic-Youtube-Downloader.svg?branch=master)

# YouTube Downloader

This python program periodically checks youtube for new videos in a users subscription feed. It will then move it to a designated folder with a video thumbnail and a channel poster. 

This was designed to work with Plex and this [plugin](https://github.com/ZeroQI/YouTube-Agent.bundle) and this [scanner](https://github.com/ZeroQI/Absolute-Series-Scanner)

This program now works with this [plugin](https://bitbucket.org/mjarends/extendedpersonalmedia-agent.bundle/overview) and this [Scanner](https://bitbucket.org/mjarends/plex-scanners/overview) this plugin and scanner is more stable and seems to work more often. But doesn't have specific youtube data (like descriptions and tags)

Please download and install both if using with Plex.

## Install

To install first download this repo, in the upper right of this repo click 'Download zip

Download python [here](https://www.python.org/ftp/python/3.5.4/python-3.5.4.exe) currently Python 3.5 is supported but should work with newer versions of python (3.5+)

**When installing make sure to click 'Add to PATH'**

After installing python open a command prompt or terminal and copy this

```
python setup.py
```

If its your first time installing select '1', it will walk you through the process

If you have a new subscription you want to add you can select '2' to go through this process again


This program will need you to setup a youtube api key, by following this [guide](https://www.slickremix.com/docs/get-api-key-for-youtube/)

It will then ask whether you want to select which channels you want included or include all the channels. 

If you have a lot of subscriptions (like me) then I recommend chosing to include all of them then opening data/youtubeData.xml when the setup is complete and deleting the whole line for whichever channel(s) you dont want to download.

If you have a fairly smallish amount of subscriptions then you can chose the 'select' opiton and it will ask you for each channel if you want to include it or not

It will then take you through some config options

## Running

Use this command to run:

```
python main.py
```

## Updating

To update download this Repo again, unzip file, then copy over you entire 'data' directory from your old directory to the one you just unzipped.

#### To version 1.0
To update from version 0.1, do the above then edit data/config change the `VIDEO_FORMAT=` line to a quality setting you want currently supported values:

    480p
    720p
    1080p
    1440p
    2160p
    4320p

So if i wanted 4k videos the line would look line 

`VIDEO_FORMAT=2160p`

## Usage

```
python main.py [OPTIONS]
```

### Options
    main.py -c <config file(optional)>
                    -c: config file optional, if not provided will default to data/config
                    Multiple config files supported just separate with a space and surround with quotes ex.
                    main.py -c "config1.txt config2 data/config3"

## Config File

### Options

The config file is created when you run setup.py but here is a reference if you want to configure it yourself

The file must have one option per line(doesn't matter what order), and must not have any spaces around the equals ex: ```FILE_FORMAT=%NAME - %UPLOAD_DATE - %TITLE```

    API_KEY                     Your API key
    SCHEDULING_MODE_VALUE       If set in time mode this is what hour of the day to start, If set in delay mode this is the delay in seconds
    NUM_VIDEOS                  How many videos to download at a time (max 15)
    DESTINATION_FOLDER          The folder to move channels into
    VIDEO_FORMAT                The video quality to download at (default=248+251/best)
    FILE_FORMAT                 Format for files
                                    Supported tags:
                                        %NAME
                                        %UPLOAD_DATE
                                        %TITLE
                                        %CHANNEL_ID
                                        %VIDEO_ID
    DESTINATION_FORMAT          This is the folder the video files will go in, usually the channel name but below are the supported tags
                                    Supported tags:
                                        %NAME
                                        %UPLOAD_DATE
                                        %TITLE
                                        %CHANNEL_ID
                                        %VIDEO_ID
    SCHEDULING_MODE             Mode for when to run things
                                    Options:
                                        TIME_OF_DAY
                                        RUN_ONCE
                                        DELAY

## Filters

With the custom filters you can cherry pick which videos you would like to download automatically, there is 2 modes for the filters to work either "allow-only" or "deny-only" mode

To setup filters navigate to data/filters, then create a file with the name being the channel ID of the channel you want to filter. For example the name of a file would look like "UC4PooiX37Pld1T8J5SYT-SQ"

Each line in that file is a seperate filter for that channel, if there are conflicts it will resort to the top most filter argument. The formatting goes like so
    
    deny-only "*Ear Biscuits*"
    allow-only "*GAME*"

- allow-only: In this mode it will block everything but what is listed
- deny-only: IN this mode it will block anything matching what is given, IMPORTANT:make sure to put before allow-only commands or they might get ignored

The only wildcard supported at the moment is *. The default behavior without wildcards is to exact match, make sure to use * if you want to match a part of a title.


## WIP Features



## Issues

- If you get "Failed to download please update youtube-dl with 

    `pip uninstall youtube-dl` 

    `pip install youtube-dl`

Any other issues please report on Github if you would like them fixed or looked at.

