import sys
import json
import os
import glob
import traceback
from sys import platform
import subprocess
import xml.sax.saxutils
import logging
import getopt

# support for python 3 and 2
if sys.version_info[0] == 3:
    from urllib.request import urlopen
    from urllib import request
else:
    from urllib import urlopen
    import urllib as request

DEBUGLOGGING = False

VIDEO_QUALITY_DICT = {
    '480p': '244+251/best',
    '720p': '247+251/best',
    '1080p HD': '248+251/299+140/137+140/best',
    '1440p QHD': '271+251/best',
    '2160p 4k': '313+251/best',
    '4320p 8k': '272+251/best'
}
VIDEO_QUALITY_LIST = [
    ['480p', '720p', '1080p HD', '1440p QHD', '2160p 4k', '4320p 8k'],
    ['244+251/best', '247+251/best', '248+251/299+140/137+140/best', '271+251/best', '313+251/best', '272+251/best']
]


# this should be deprecated in favor of logging.* calls
def logPrint(string):
    if DEBUGLOGGING:
        logging.warning("logPrint is deprecated, please use logging.* calls")
        logging.debug("DEBUGMSG: %s" % str(string))


def get_input(msg):  # support for python 2 and 3
    if sys.version_info[0] == 3:
        d = input(msg)
    else:
        d = raw_input(msg)
    return d


def install_dependencies():
    try:
        print("Checking Dependencies....")
        homeDirectory = os.getcwd()
        if platform == 'windows':
            #print('Windows System')
            subprocess.run(["python", os.path.join("poetry", "get_poetry.py")], shell=True)
            subprocess.run([os.path.join("poetry", "bin", "poetry"), "update"], shell=True)
        else:
            #print('Not Windows Sys')
            sys.stdout.flush()
            os.system('python ' + os.path.join(homeDirectory, "poetry", 'get_poetry.py'))
            sys.stdout.flush()
            os.system(os.path.join(homeDirectory, "poetry", "bin", "poetry") + ' update')

    except Exception as e:
        logging.error("Exception occurred %s" % str(e))
        logPrint("ERROR:\n" + str(e))
        logging.error(traceback.format_exc())
        print(str(e))
        print("An error occured please check logs and try again")
        exit()
    print("Complete.\n")
    '''try:
        from pip import main as pipmain
    except:
        from pip._internal import main as pipmain'''
'''
    _all_ = [
        "beautifulsoup4",
        "listparser",
        "colorama",
        "youtube-dl"
    ]
    linux = [
        "ffmpeg"
    ]
    try:
        if pipmain(['install', "--upgrade", "pip"]):
            raise Exception
        for package in _all_:
            logging.debug("Looking for package %s" % package)
            if pipmain(['install', package]):
                raise Exception
                # print(subprocess.check_call([sys.executable, '-m', 'pip', 'install', package]))
        # if platform == 'windows':
        #	install(windows)
        if platform.startswith('linux'):
            for package in linux:
                logging.debug("Looking for linux package %s" % package)
                if pipmain(['install', package]):
                    raise Exception
                    # print(subprocess.check_call([sys.executable, '-m', 'pip', 'install', package]))
                    # if platform == 'darwin':  # MacOS
                    #	install(darwin)
'''


def format_youtube_data():
    api_key = ""
    setup_not_complete = True
    subFile = "subscription_manager.xml"
    while setup_not_complete:
        print("\n\nSetting up Youtube configs")
        print("Please goto https://www.youtube.com/subscription_manager")
        print("On the bottom of the page click 'Export Subscriptions'")
        print("Put that file in the data directory so it looks like " + subFile)
        get_input("Click enter to continue.....")

        if os.path.exists(os.path.join("data" + subFile)):
            print("\nFile Found\n\n")
            logging.info(subFile + " was found")
            setup_not_complete = False
        else:
            print("File Not Found!! Please make sure you have it in th correct directory and its named correctly")
            logging.warning(subFile + " was NOT found")
            logging.debug("data folder contents:\n" + str(glob.glob("data/*")))


def get_API_key():
    logging.debug("get_API_key function called")

    setup_not_complete = True

    logging.debug("Gathering API key info")
    while setup_not_complete:
        print("\n\nPlease goto https://www.slickremix.com/docs/get-api-key-for-youtube/")
        print("Follow this guide to setup an API key you can name the project whatever you want")
        api_key = get_input("Please enter your API key now:")

        print("Testing key.....")
        try:
            url_data = urlopen(
                'https://www.googleapis.com/youtube/v3/search?part=snippet&q=YouTube+Data+API&type=video&key=' + api_key)
            code = url_data.getcode()
            if code != 200:
                raise Exception('Did not receive webpage')

            print("\nSuccess!")
            logging.info("Google API Key returned 200 (success)")
            setup_not_complete = False
            return api_key
        except Exception as e:
            logging.error("ERROR" + str(e))
            logging.error(traceback.format_exc())
            print("Sorry that key did not work!!! Make sure you copied the key correctly")

    return api_key  # shouldn't reach this but just in case


def channel_selection(dataFile, inputFile="data/subscription_manager.xml", titleList=None, idList=None):
    if titleList is not None:
        inputFile = None

    import listparser as lp
    logging.debug("Channel_selection started")
    # This function parses OPML data and allows the user to select which channels to be included
    print("Parsing Youtube data\n")
    all_channels = False
    loop = True
    while loop:
        selection = get_input(
            "Would you like to select which channels you want to include, or do you want to include all of them?\n"
            "If you include all channels you can remove them manually by editing " + dataFile + " and deleting the"
            " entire line of the channel you do not want (Choose this option if you have a lot of subscriptions)\n"
            "Enter 'all' to keep all subscriptions or 'select' to select which channels (or 'a' or 's'):").lower()

        logging.debug("User selected %s for all or single channel selection" % selection)
        if selection == 'all' or selection == 'a':
            all_channels = True
            loop = False
            print("Including all channels\n")
        elif selection == 'select' or selection == 's':
            all_channels = False
            loop = False
            print(
                "You will now be asked to select which channels you would like to include in your download library. \nAny"
                " channels you do not include will be ignored. \nWarning: if you add a new subscription you must go through this"
                " process again (until I add a feature to import a channel)\n")
        else:
            print("Invalid Selection!!! Try again.")
            logging.warning("User selected invalid entry")

    logging.debug("Opening " + dataFile + " for writing")
    file = open(dataFile, 'w')
    #logging.debug("Parsing " + inputFile)
    file.write('<opml version="1.1">\n<body>\n')

    if titleList is None:
        d = lp.parse(inputFile)
        l = d.feeds

        for count, channel in enumerate(l):
            titleList[count] = channel.title
            idList[count] = channel.url
    else:
        for count, channel in enumerate(idList):
            idList[count] = "https://www.youtube.com/feeds/videos.xml?channel_id=" + idList[count]
    num_channels = len(titleList)

    human_count = 1
    logging.debug("Processing channels")
    for count in range(0, num_channels):
        include_this_subscription = True
        title = titleList[count].replace('&', 'and')
        title = title.encode("ascii", errors="ignore").decode('utf-8', 'ignore')
        url = bytes(idList[count], 'utf-8').decode('utf-8', 'ignore')

        logging.debug("Processing channel: %s" % title)
        logging.debug("Channel has url %s" % url)

        if all_channels:
            print("(%i/%i) Including subscription: %s\n" % (human_count, num_channels, title))
            logging.info("Automatically including channel: %s" % title)

        if not all_channels:
            loop = True
            while loop:
                selection = get_input(
                    "(%i/%i) Include %s, yes or no (y/n)?" % (human_count, num_channels, title)).lower()
                if selection == 'y' or selection == 'yes':
                    include_this_subscription = True
                    print("   Including %s\n" % title)
                    logging.info("User opted to include channel: %s" % title)
                    loop = False
                elif selection == 'n' or selection == 'no':
                    include_this_subscription = False
                    logging.info("User opted to not include channel: %s" % title)
                    loop = False
                else:
                    print("   Invalid response. Try again.")

        human_count += 1

        if include_this_subscription:
            file.write('<outline title="' + xml.sax.saxutils.escape(title) + '" xmlUrl="' + xml.sax.saxutils.escape(
                url) + '"/>\n')
        else:
            print("   Not including %s\n" % title)

    file.write('</body>\n</opml>')
    file.close()
    logging.debug("Channels saved to" + dataFile)
    print("\nComplete.")


def setup_config(api_key, configFile):
    logging.info("setup_config function called")
    print("\n\n\nSetting up Config file")
    with open(configFile, 'w') as f:
        f.write("API_KEY=" + api_key + "\n")
        logging.debug("API Key recorded to file")
        loop = True
        while loop:
            selection = get_input("""
    \nHow would you like the program to run? (x being any number you want)
        1. Once at startup and then every X minutes
        2. Every day at a specific time
        3. Once and then exit (for Cron, etc)""")

            logging.info("User selected schedule option %s" % selection)
            if selection == '1':
                delay_time = get_input("Please enter the delay time between checks (in minutes):")
                if delay_time.isdigit():
                    logging.info("User set delay time between checks to %s" % delay_time)
                    print("\nSuccess! It will run once and then every " + delay_time + " minutes")
                    f.write("SCHEDULING_MODE=DELAY\n")
                    f.write("SCHEDULING_MODE_VALUE=" + delay_time + '\n')
                    loop = False
                else:
                    print("\nInvalid entry! Value must be a whole number (e.g.: 1, 10, 6000)")
            elif selection == '2':
                start_time = get_input("Please enter the hour of the day to run at (0-23):")
                if start_time.isdigit() and (-1 < int(start_time) < 24):
                    logging.info("User set run time of day to %s" % start_time)
                    print("\nSuccess! It will run at " + start_time + " everyday!")
                    f.write("SCHEDULING_MODE=TIME_OF_DAY\n")
                    f.write("SCHEDULING_MODE_VALUE=" + start_time + '\n')
                    loop = False
                else:
                    print("\nInvalid entry! Value must be 0-23 (e.g.: 6, 14, 23)")
            elif selection == '3':
                start_time = get_input("The program will only run once and then end, please confirm with Y")
                if start_time.isalpha() and (start_time.lower() == "y"):
                    logging.info("User set to run only once and exit")
                    print("\nSuccess! It will run once and exit!")
                    f.write("SCHEDULING_MODE=RUN_ONCE\n")
                    f.write("SCHEDULING_MODE_VALUE="'\n')
                    loop = False
                else:
                    print("\nReturning to the parent selection")
                    loop = True
            else:
                print("\nInvalid!!! Please choose from 1-3.")
                logging.warning("User entered bad selection for how to run %s" % selection)

        loop = True
        while (loop):
            response = get_input("\nHow many videos for each channel do you want to download? (max 15)")
            if response.isdigit():
                logging.info("User selected %s videos to be downloaded per channel" % response)
                f.write("NUM_VIDEOS=" + response + '\n')
                loop = False
            else:
                print("\nInvalid!!! Please try again.")

        loop = True
        while (loop):
            response = get_input("\nWhere would you like your videos moved? (Usually a Plex library)\n"
                                 "Make sure you enter the entire address (ex. 'G:\\Plex\\Youtube\\')\n")

            logging.info("User selected path to place videos as %s" % response)

            try:
                if not os.path.isdir(response):  # either not a valid directory or not created
                    # try making a directory and see if it throws an exception
                    print("Creating Source Directory")
                    response = os.path.join(response, '')  # add a trailing backslash if not already there
                    os.makedirs(response)
                    logging.info("Path to video library was not found, created")
                    f.write("DESTINATION_FOLDER=" + response + '\n')  # if it gets this far we are good
                    print('\nSuccess!')
                    loop = False
                else:
                    print("Found Source Directory")
                    logging.info("Video library path found")
                    response = os.path.join(response, '')
                    f.write("DESTINATION_FOLDER=" + response + '\n')
                    print('\nSuccess!')
                    loop = False
            except Exception as e:
                logging.error(str(e))
                print("\nInvalid!!! Please try again.")



        '''
        Format for files and destination folders available options:
            %NAME
            %UPLOAD_DATE
            %TITLE
            %CHANNEL_ID
            %VIDEO_ID
        '''
        loop = True
        while (loop):
            response = get_input("Please Choose a destination format:\n"
                                 "1. ASS Scanner Default (%Channel_Name [Youtube-$Channel_ID])\n"
                                 "2. Extended Personal Scanner Default (%Channel_Name)\n"
                                 #"3. Custom"
            )

            logging.info("User selected %s for destination format" % response)

            DESTINATION_FORMAT = ""
            if response is "1":
                print()
                DESTINATION_FORMAT = "%NAME [Youtube-$CHANNEL_ID]"
                loop = False
            elif response is "2":
                print()
                DESTINATION_FORMAT = "%NAME"
                loop = False
            #elif response is "3":
            #    print("HODLLLLLLLLLLLLLL")
            #    loop = False
            else:
                print("Invalid Entry")

            if loop is False:
                f.write('DESTINATION_FORMAT=' + DESTINATION_FORMAT + '\n')

        loop = True
        while (loop):
            response = get_input("Please Choose a file format:\n"
                                 "1. ASS Scanner Default (%Video_Tile - [%Video_ID])\n"
                                 "2. Extended Personal Scanner Default (%Channel_Name - %Upload_Date - %Video_Title)\n"
                                 #"3. Custom"
            )

            logging.info("User selected %s for destination format" % response)
            FILE_FORMAT = ""
            if response is "1":
                print()
                FILE_FORMAT = "%TITLE - [%VIDEO_ID]"
                loop = False
            elif response is "2":
                print()
                FILE_FORMAT = "%NAME - %UPLOAD_DATE - %TITLE"
                loop = False
            #elif response is "3":
            #    print("HODDLLLL")
            #    loop = False
            else:
                print("Invalid Entry")
            if loop is False:
                f.write('FILE_FORMAT=' + FILE_FORMAT + '\n')

        loop = True
        while (loop):
            print("Please choose a quality setting:\n")
            for i, line in enumerate(VIDEO_QUALITY_LIST[0]):
                print('{}. {}'.format(i + 1, line.strip()))
            response = get_input("")
            try:
                if 0 < int(response) < len(VIDEO_QUALITY_LIST[0]):
                    f.write("VIDEO_FORMAT=" + VIDEO_QUALITY_LIST[1][int(response)] + "\n")
                loop = False
            except:
                print("Please choose a number between 1-" + str(len(VIDEO_QUALITY_LIST[0])) + "\n")


def add_channel(dataFile):
    chName = get_input("\n\nPlease enter the channel Name:")
    chID = get_input("Please enter the channel ID:")
    get_input("\nYou entered\nName:" + chName + "\nChannel ID:" + chID + "\nIf this is correct press enter...")

    if ("UC" in chID) or (len(chID) is 24):

        print("Writing to file...")

        if os.path.isfile(dataFile):
            file = open(dataFile, 'r')
            lines = file.readlines()
            file.close()

            file = open(dataFile, 'w')
            lines.insert(2, '<outline title="' + xml.sax.saxutils.escape(chName) +
                            '" xmlUrl="https://www.youtube.com/feeds/videos.xml?channel_id=' +
                            xml.sax.saxutils.escape(chID) + '"/>\n')
            file.writelines(lines)
            file.close()
            print("Complete.")
        else:
            file = open(dataFile, 'w')
            file.write('<opml version="1.1">\n<body>\n')
            file.write('<outline title="' + xml.sax.saxutils.escape(chName) +
                       '" xmlUrl="https://www.youtube.com/feeds/videos.xml?channel_id=' +
                        xml.sax.saxutils.escape(chID) + '"/>\n')
            file.write('</body>\n</opml>')
            file.close()
    else:
        print("Invalid ID! Try again please")


def get_sub_list(api_key):
    my_chid = get_input("Please login to your youtube account in a browser, click on your account and click 'My Channel'\n"
                      "Look at the address bar, copy everything after channel/, it should start with UC\n"
                      "Please paste that in here(If you do not have a Youtube account just click enter): ")

    try:
        if my_chid.strip() is "":
            print("Please put ")
        my_chid = my_chid.split("?")[0]
        url_data = urlopen(
            'https://www.googleapis.com/youtube/v3/subscriptions?channelId='
            + my_chid + '&part=snippet%2CcontentDetails&maxResults=50&key=' + api_key +
            '')

        data = url_data.read()
        data = json.loads(data.decode('utf-8'))

        titleList = []
        idList = []

        for item in data['items']:
            titleList.append(item['snippet']['title'])
            idList.append(item['snippet']['resourceId']['channelId'])

        #results_per_page = data['pageInfo']['resultsPerPage']
        #total_results = data['pageInfo']['totalResults']
        while True:
            if "nextPageToken" in data:
                # There is more pages we need to get
                next_page_token = data['nextPageToken']

                url_data = urlopen(
                    'https://www.googleapis.com/youtube/v3/subscriptions?channelId=' + my_chid +
                    '&part=snippet%2CcontentDetails&maxResults=50&pageToken=' + next_page_token + '&key=' + api_key +
                    '&order=alphabetical')

                data = url_data.read()
                data = json.loads(data.decode('utf-8'))

                for item in data['items']:
                    titleList.append(item['snippet']['title'])
                    idList.append(item['snippet']['resourceId']['channelId'])

            else:
                return [titleList, idList]

    except Exception as e:
        logging.error("ERROR: My Channel Key incorrect")
        logging.error("ERROR" + str(e))
        logging.error(traceback.format_exc())
        print("There was something wrong with your key, please check the setup.log")
        exit(0)


def main(configFile, dataFile, skipDep):
    if not os.path.exists('data/'):
        logging.info("Data directory not found, creating...")
        os.makedirs('data/')
    if not os.path.exists('Download/'):
        logging.info("Download directory not found, creating...")
        os.makedirs('Download/')
    if not os.path.isfile('data/log.txt'):
        logging.info("log.txt not found, creating...")
        open('data/log.txt', 'a').close()

    loop = True
    while loop:
        print("""
        1. First Time Install
        2. Channel Selection
        3. Install Dependencies
        4. Add Single Channel Manually
        5. Exit/Quit
        """)

        menuSelection = get_input("What would you like to do? ")

        if menuSelection == "1":
            logging.info("At main menu, user selected option %s" % menuSelection)
            if not skipDep:
                install_dependencies()
            api_key = get_API_key()
            titleList, idList = get_sub_list(api_key)
            channel_selection(dataFile, "", titleList, idList)
            setup_config(api_key, configFile)
            print('\n\n\n----------This completes the setup you may now exit-----------\n')
        elif menuSelection == "2":
            channel_selection(dataFile)
        elif menuSelection == "3":
            install_dependencies()
        elif menuSelection == "4":
            add_channel(dataFile)
        elif menuSelection == "5":
            print("\n Goodbye")
            logging.info("User exited program")

            exit()
        else:
            print("\n Not Valid Choice Try again")
            logging.info("Main menu selection of %s rejected, looping" % menuSelection)


if __name__ == "__main__":
    logging.basicConfig(filename='setup.log', level=logging.DEBUG, format='%(asctime)s %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')

    logging.info("Program setup.py started")

    configFileInput = ''
    dataFileInput = ''
    skipDep = False
    if len(sys.argv) > 0:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hc:d:s", ["config=", "data=", "skip"])
        except getopt.GetoptError:
            print('\n\nmain.py -c <config file> -d <youtube data file> -s\n\n'
                  '   -c,--config: config file optional, if not provided will default to data/config\n'
                  '       Multiple config files supported just separate with a space and surround with quotes ex.\n'
                  '       main.py -c "config1.txt config2 data/config3"\n'
                  '   -d,--data: data file optional, if not provided will default to data/youtubeData.xml\n'
                  '       This is the file output of channel names and urls.\n'
                  '   -s,--skip: flag to skip dependency check\n\n')
            exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print('\n\nmain.py -c <config file> -d <youtube data file> -s\n\n'
                      '   -c,--config: config file optional, if not provided will default to data/config\n'
                      '       Multiple config files supported just separate with a space and surround with quotes ex.\n'
                      '       main.py -c "config1.txt config2 data/config3"\n'
                      '   -d,--data: data file optional, if not provided will default to data/youtubeData.xml\n'
                      '       This is the file output of channel names and urls.\n'
                      '   -s,--skip: flag to skip dependency check\n\n')
                exit(2)
            elif opt in ("-c", "--config"):
                configFileInput = arg
            elif opt in ("-d", "--data"):
                dataFileInput = arg
            elif opt in ("-s", "--skip"):
                skipDep = True
                print("--Skipping Dependency check")

        if configFileInput == '':
            configFile = 'data/config'
            #print('--Using data/config')
        else:
            configFile = configFileInput

        if dataFileInput == '':
            dataFile = 'data/youtubeData.xml'
        else:
            dataFile = dataFileInput
    else:
        # No arguments
        configFile = 'data/config'
        dataFile = 'data/youtubeData.xml'

    if dataFileInput == '':
        dataFileInput = 'data/youtubeData.xml'
        #print('--Using data/youtubeData.xml')
    else:
        dataFile = dataFileInput

    print("--Outputting data to:" + dataFile)
    print("--Config file:" + configFile)
    main(configFile, dataFile, skipDep)
    logging.info("Program setup.py ended")
    logging.info("====================================================================")
