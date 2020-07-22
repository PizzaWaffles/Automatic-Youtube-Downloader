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
from colorama import init
from colorama import Fore, Back, Style

# support for python 3 and 2
if sys.version_info[0] == 3:
    from urllib.request import urlopen
    from urllib import request
else:
    print("\nError, please install python3.\n")
    exit(1)

DEBUGLOGGING = False
TESTING = False

# Deprecated no longer using codes
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

CONFIGURATIONS_HUMAN_READABLE = {
    'API_KEY': "Google's API key",
    'SCHEDULING_MODE': 'Program scheduler(Delay, Once, Time)',
    'SCHEDULING_MODE_VALUE': 'Program scheduler value(delay time, time to run)',
    'NUM_VIDEOS': 'Number of videos to download initially',
    'DESTINATION_FOLDER': 'The folder to move videos to',
    'DESTINATION_FORMAT': 'The naming convention to use for folders(see GitHub for more info)',
    'FILE_FORMAT': 'The naming convention to use for files(see GitHub for more info)',
    'VIDEO_FORMAT': 'Quality setting'
}

init()  # start colorizer
RED = Fore.RED
GREEN = Fore.GREEN
BLUE = Fore.BLUE
MAGENTA = Fore.MAGENTA
LIGHT_BLUE = Fore.LIGHTCYAN_EX


def write(s, color=None):
    if color is None:
        print(s)
    else:
        print(color + s + Style.RESET_ALL)


# this should be deprecated in favor of logging.* calls
def logPrint(string):
    if DEBUGLOGGING:
        logging.warning("logPrint is deprecated, please use logging.* calls")
        logging.debug("DEBUGMSG: %s" % str(string))


def get_input(msg, color=LIGHT_BLUE):
    write(msg, color)
    d = input("")
    return d


def install_dependencies():
    logging.debug("install_dependencies function called")
    try:
        write("Checking Dependencies....", BLUE)
        homeDirectory = os.getcwd()
        pythonPath = sys.executable
        write("Python Path: " + pythonPath)
        getPoetryCmd = [pythonPath, os.path.join(homeDirectory, "poetry", "get_poetry.py"), "--version", "0.12.11"]
        runPoetryCmd = [os.path.join(homeDirectory, "poetry", "bin", "poetry"), "update"]
        if sys.platform.startswith("win"):
            write('Using Windows System Settings')
            subprocess.run(getPoetryCmd, shell=True)
            subprocess.run(runPoetryCmd, shell=True)
        else:
            sys.stdout.flush()
            proc = subprocess.call(getPoetryCmd)
            if proc > 0:
                write("An error occurred with downloading poetry", RED)
                exit(1)

            sys.stdout.flush()
            proc = subprocess.call(runPoetryCmd)
            if proc > 0:
                write("An error occurred with running poetry", RED)
                exit(1)

    except Exception as e:
        logging.error("Exception occurred %s" % str(e))
        logging.error(traceback.format_exc())
        write(str(e))
        write("An error occured please check logs and try again", RED)
        exit()
    write("Complete.\n", GREEN)


def format_youtube_data():
    logging.debug("format_youtube_data function called")
    api_key = ""
    setup_not_complete = True
    subFile = "subscription_manager.xml"
    while setup_not_complete:
        write("\n\nSetting up Youtube configs")
        write("Please goto https://www.youtube.com/subscription_manager")
        write("On the bottom of the page click 'Export Subscriptions'")
        write("Put that file in the data directory so it looks like data/" + subFile)
        if not TESTING:
            get_input("Click enter to continue.....")

        if os.path.exists(os.path.join("data", subFile)):
            write("\nFile Found\n\n")
            logging.info(subFile + " was found")
            setup_not_complete = False
        else:
            write("File Not Found!! Please make sure you have it in the correct directory and its named correctly", RED)
            logging.warning(subFile + " was NOT found")
            logging.debug("data folder contents:\n" + str(glob.glob("data/*")))


def get_API_key_config(cFile):
    logging.debug("get_API_key_config function called")
    if os.path.isfile(cFile):
        f = open(cFile)
        l = f.readlines()
        for line in l:
            if line.split("=")[0] == "API_KEY":
                return line.split("=")[1]

    write("Config file does not exist please run setup from the start", RED)
    return None


def get_API_key():
    logging.debug("get_API_key function called")

    setup_not_complete = True

    logging.debug("Gathering API key info")
    while setup_not_complete:
        write("\n\nPlease goto https://www.slickremix.com/docs/get-api-key-for-youtube/")
        write("Follow this guide to setup an API key you can name the project whatever you want")
        if TESTING:
            print("Using Test key from travis-ci")
            api_key = str(os.environ.get('APIKEY'))
        else:
            api_key = get_input("Please enter your API key now:")

        write("Testing key.....", BLUE)
        try:
            url_data = urlopen(
                'https://www.googleapis.com/youtube/v3/search?part=snippet&q=YouTube+Data+API&type=video&key=' + api_key)
            code = url_data.getcode()
            if code != 200:
                raise Exception('Did not receive webpage')

            write("\nSuccess!", GREEN)
            logging.info("Google API Key returned 200 (success)")
            setup_not_complete = False
            return api_key
        except Exception as e:
            logging.error("ERROR" + str(e))
            logging.error(traceback.format_exc())
            write("Sorry that key did not work!!! Make sure you copied the key correctly", RED)


def channel_selection(dataFile, inputFile="data/subscription_manager.xml", titleList=None, idList=None):
    logging.debug("channel_selection function called")
    if titleList is not None:
        inputFile = None
    else:
        titleList = []
        idList = []


    import listparser as lp
    logging.debug("Channel_selection started")
    # This function parses OPML data and allows the user to select which channels to be included
    write("Parsing Youtube data...\n", BLUE)
    all_channels = False
    loop = True
    while loop:
        write("Would you like to select which channels you want to include, or do you want to include all of them?\n"
              "If you include all channels you can remove them manually by editing " + dataFile + " and deleting the"
                                                                                                  " entire line of the channel you do not want (Choose this option if you have a lot of subscriptions)")
        selection = get_input(
            "Enter 'all' to keep all subscriptions or 'select' to select which channels (or 'a' or 's'):").lower()

        logging.debug("User selected %s for all or single channel selection" % selection)
        if selection == 'all' or selection == 'a':
            all_channels = True
            loop = False
            write("Including all channels\n")
        elif selection == 'select' or selection == 's':
            all_channels = False
            loop = False
            write(
                "You will now be asked to select which channels you would like to include in your download library. \n"
                "Any channels you do not include will be ignored.\n")
        else:
            write("Invalid Selection!!! Try again.")
            logging.warning("User selected invalid entry")

    logging.debug("Opening " + dataFile + " for writing")
    file = open(dataFile, 'w')
    # logging.debug("Parsing " + inputFile)
    file.write('<opml version="1.1">\n<body>\n')

    if inputFile is not None:
        d = lp.parse(inputFile)
        l = d.feeds

        for count, channel in enumerate(l):
            #titleList[count] = channel.title
            #idList[count] = channel.url
            titleList.append(channel.title)
            idList.append(channel.url)
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
            write("(%i/%i) Including subscription: %s\n" % (human_count, num_channels, title))
            logging.info("Automatically including channel: %s" % title)

        if not all_channels:
            loop = True
            while loop:
                selection = get_input(
                    "(%i/%i) Include %s, yes or no (y/n)?" % (human_count, num_channels, title)).lower()
                if selection == 'y' or selection == 'yes':
                    include_this_subscription = True
                    write("   Including %s\n" % title)
                    logging.info("User opted to include channel: %s" % title)
                    loop = False
                elif selection == 'n' or selection == 'no':
                    include_this_subscription = False
                    logging.info("User opted to not include channel: %s" % title)
                    loop = False
                else:
                    write("   Invalid response. Try again.", RED)

        human_count += 1

        if include_this_subscription:
            file.write('<outline title="' + xml.sax.saxutils.escape(title) + '" xmlUrl="' + xml.sax.saxutils.escape(
                url) + '"/>\n')
        else:
            write("   Not including %s\n" % title)

    file.write('</body>\n</opml>')
    file.close()
    logging.debug("Channels saved to" + dataFile)
    write("\nComplete.")


def edit_config(configPath):
    logging.debug("edit_config function called")
    if not os.path.isfile(configPath):
        logging.info(configPath + " not found!!")
        write(configPath + " not found!!", RED)
        return 0

    # TODO add error processing for empty config file
    with open(configPath, 'r+') as f:
        cLines = f.readlines()
        for i in range(0, len(cLines)):
            cLines[i] = cLines[i].strip().split('=')
        loop = True
        while (loop):
            write("Please choose a setting to edit:\n", LIGHT_BLUE)
            for i, line in enumerate(cLines):
                write('{}.   {}'.format(i + 1, cLines[i][0] + ' = ' + cLines[i][1]))

            menuSelection = get_input("")
            if menuSelection == "1":
                write('\n\nChanging ' + cLines)

            elif menuSelection == "2":
                channel_selection(dataFile)
            elif menuSelection == "3":
                install_dependencies()
            elif menuSelection == "4":
                add_channel(dataFile)
            elif menuSelection == "5":
                edit_config()
            elif menuSelection == "6":
                write("\n Goodbye")
                logging.info("User exited program")

                exit()
            else:
                write("\n Not Valid Choice Try again")


def setup_config(api_key, configFile):
    logging.info("setup_config function called")
    write("\n\n\nSetting up Config file...", BLUE)

    # TODO Add config edit functionality
    '''if os.path.isfile(configFile):
        loop = True
        while loop:
            response = get_input("Previous config file found would you like to overwrite it or edit it (o or e):")
            if response is 'o' or response is 'O':
                loop = False
            elif response is 'e' or response is 'E':
                loop = False
            else:
                write("Please enter o for overwrite or e for edit.", RED)'''

    with open(configFile, 'w') as f:
        f.write("API_KEY=" + api_key + "\n")
        logging.debug("API Key recorded to file")
        loop = True
        while loop:
            write("\nHow would you like the program to run? (x being any number you want)", LIGHT_BLUE)
            selection = get_input("""
        1. Once at startup and then every X minutes
        2. Every day at a specific time
        3. Once and then exit (for Cron, etc)""", None)

            logging.info("User selected schedule option %s" % selection)
            if selection == '1':
                delay_time = get_input("Please enter the delay time between checks (in minutes):")
                if delay_time.isdigit():
                    logging.info("User set delay time between checks to %s" % delay_time)
                    write("\nSuccess! It will run once and then every " + delay_time + " minutes", GREEN)
                    f.write("SCHEDULING_MODE=DELAY\n")
                    f.write("SCHEDULING_MODE_VALUE=" + delay_time + '\n')
                    loop = False
                else:
                    write("\nInvalid entry! Value must be a whole number (e.g.: 1, 10, 6000)", RED)
            elif selection == '2':
                start_time = get_input("Please enter the hour of the day to run at (0-23):")
                if start_time.isdigit() and (-1 < int(start_time) < 24):
                    logging.info("User set run time of day to %s" % start_time)
                    write("\nSuccess! It will run at " + start_time + " everyday!", GREEN)
                    f.write("SCHEDULING_MODE=TIME_OF_DAY\n")
                    f.write("SCHEDULING_MODE_VALUE=" + start_time + '\n')
                    loop = False
                else:
                    write("\nInvalid entry! Value must be 0-23 (e.g.: 6, 14, 23)")
            elif selection == '3':
                start_time = get_input("The program will only run once and then end, please confirm with Y")
                if start_time.isalpha() and (start_time.lower() == "y"):
                    logging.info("User set to run only once and exit")
                    write("\nSuccess! It will run once and exit!", GREEN)
                    f.write("SCHEDULING_MODE=RUN_ONCE\n")
                    f.write("SCHEDULING_MODE_VALUE="'\n')
                    loop = False
                else:
                    write("\nReturning to the parent selection")
                    loop = True
            else:
                write("\nInvalid!!! Please choose from 1-3.", RED)
                logging.warning("User entered bad selection for how to run %s" % selection)

        loop = True
        while (loop):
            write("\nHow many videos for each channel do you want to download initially? (max 15)\n"
                  "Note that is a automatic video downloader meaning it will download new videos "
                  "once they are posted. \nThis is not meant to download am entire channel (at least I "
                  "have not implemented this function if you would like it please request it on GitHub)\n")
            response = get_input("Please enter a number between 1-15")
            if response.isdigit():
                logging.info("User selected %s videos to be downloaded per channel" % response)
                f.write("NUM_VIDEOS=" + response + '\n')
                loop = False
            else:
                write("\nInvalid!!! Please try again.", RED)

        loop = True
        while (loop):
            response = get_input("\nWhere would you like your videos moved? (Usually a Plex library)\n"
                                 "Make sure you enter the entire address (ex. 'G:\\Plex\\Youtube\\')\n")

            logging.info("User selected path to place videos as %s" % response)

            try:
                if not os.path.isdir(response):  # either not a valid directory or not created
                    # try making a directory and see if it throws an exception
                    write("Creating Source Directory")
                    response = os.path.join(response, '')  # add a trailing backslash if not already there
                    os.makedirs(response)
                    logging.info("Path to video library was not found, created")
                    f.write("DESTINATION_FOLDER=" + response + '\n')  # if it gets this far we are good
                    write('\nSuccess!', GREEN)
                    loop = False
                else:
                    write("Found Source Directory")
                    logging.info("Video library path found")
                    response = os.path.join(response, '')
                    f.write("DESTINATION_FOLDER=" + response + '\n')
                    write('\nSuccess!', GREEN)
                    loop = False
            except Exception as e:
                logging.error(str(e))
                write("\nInvalid!!! Please try again.", RED)

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
                # "3. Custom"
            )

            logging.info("User selected %s for destination format" % response)

            DESTINATION_FORMAT = ""
            if response is "1":
                DESTINATION_FORMAT = "%NAME [Youtube-$CHANNEL_ID]"
                loop = False
            elif response is "2":
                DESTINATION_FORMAT = "%NAME"
                loop = False
            # elif response is "3":
            #    write("HODLLLLLLLLLLLLLL")
            #    loop = False
            else:
                write("Invalid Entry", RED)

            if loop is False:
                f.write('DESTINATION_FORMAT=' + DESTINATION_FORMAT + '\n')

        loop = True
        while (loop):
            response = get_input("Please Choose a file format:\n"
                                 "1. ASS Scanner Default (%Video_Tile - [%Video_ID])\n"
                                 "2. Extended Personal Scanner Default (%Channel_Name - %Upload_Date - %Video_Title)\n"
                # "3. Custom"
            )

            logging.info("User selected %s for destination format" % response)
            FILE_FORMAT = ""
            if response is "1":
                FILE_FORMAT = "%TITLE - [%VIDEO_ID]"
                loop = False
            elif response is "2":
                FILE_FORMAT = "%NAME - %UPLOAD_DATE - %TITLE"
                loop = False
            # elif response is "3":
            #    write("HODDLLLL")
            #    loop = False
            else:
                write("Invalid Entry", RED)
            if loop is False:
                f.write('FILE_FORMAT=' + FILE_FORMAT + '\n')

        loop = True
        while (loop):  # TODO Test to make sure correct quality is saved
            write("Please choose a quality setting:\n", BLUE)
            for i, line in enumerate(VIDEO_QUALITY_LIST[0]):
                write('{}. {}'.format(i + 1, line.strip()))
            response = int(get_input(""))
            # try:
            if 0 < int(response) < len(VIDEO_QUALITY_LIST[0]):
                temp = VIDEO_QUALITY_LIST[0][int(response - 1)].split(" ")[0]
                f.write("VIDEO_FORMAT=" + temp + "\n")
                loop = False
            else:
                write("Please choose a number between 1-" + str(len(VIDEO_QUALITY_LIST[0])) + "\n", BLUE)

            # except:
            #    write("Please choose a number between 1-" + str(len(VIDEO_QUALITY_LIST[0])) + "\n", BLUE)


def add_channel(dataFile):
    logging.debug("add_channel function called")
    chName = get_input("\n\nPlease enter the channel Name:")
    chID = get_input("Please enter the channel ID:")
    get_input("\nYou entered\nName:" + chName + "\nChannel ID:" + chID + "\nIf this is correct press enter...")

    if ("UC" in chID) or (len(chID) is 24):

        write("Writing to file...", BLUE)

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
            write("Complete.", GREEN)
        else:
            file = open(dataFile, 'w')
            file.write('<opml version="1.1">\n<body>\n')
            file.write('<outline title="' + xml.sax.saxutils.escape(chName) +
                       '" xmlUrl="https://www.youtube.com/feeds/videos.xml?channel_id=' +
                       xml.sax.saxutils.escape(chID) + '"/>\n')
            file.write('</body>\n</opml>')
            file.close()
    else:
        write("Invalid ID! Try again please", RED)


def get_sub_list(api_key, configFile=None):
    logging.debug("get_sub_list function called")
    my_chid = ""
    if configFile is not None:
        if os.path.isfile(configFile):
            f = open(configFile)
            l = f.readlines()
            for line in l:
                if line.split("=")[0] == "MY_CHANNEL_ID":
                    write("Using My Channel ID from config file")
                    my_chid = line.split("=")[1]
            f.close()

    if TESTING:
        print("Using Travis channel ID")
        my_chid = str(os.environ.get('MYCHID'))
    else:
        while True:
            if my_chid is "":
                write("Please login to your youtube account in a browser, click on your account and click 'My Channel'\n"
                      "Look at the address bar, copy everything after channel/, it should start with UC\n"
                      "This is the youtube account that will be scraped for channel subscriptions\n"
                      "(Warning this account must be the same Google account used to sign up for the API key.)\n"
                      "Or leave blank if you want to manually grab the subscription file.")
                my_chid = get_input(
                    "Please paste that in here: ")
            else:
                break

    try:
        if my_chid.strip() is "":
            return [None, None]

        my_chid = my_chid.split("?")[0]
        url_data = urlopen(
            'https://www.googleapis.com/youtube/v3/subscriptions?channelId='
            + my_chid + '&part=snippet%2CcontentDetails&maxResults=50&key=' + api_key +
            '')

        if configFile is not None:
            file = open(configFile, 'a')
            file.write("\nMY_CHANNEL_ID="+my_chid + '\n')
            file.close()

        data = url_data.read()
        data = json.loads(data.decode('utf-8'))

        titleList = []
        idList = []

        for item in data['items']:
            titleList.append(item['snippet']['title'])
            idList.append(item['snippet']['resourceId']['channelId'])

        # results_per_page = data['pageInfo']['resultsPerPage']
        # total_results = data['pageInfo']['totalResults']
        while True:
            if "nextPageToken" in data:
                # There is more pages we need to get
                next_page_token = data['nextPageToken']

                url_data = urlopen(
                    'https://www.googleapis.com/youtube/v3/subscriptions?&pageToken=' + next_page_token +
                    '&channelId=' + my_chid + '&part=snippet%2CcontentDetails&maxResults=50&key=' + api_key)

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
        write("There was something wrong with your key, please check the setup.log", RED)
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
        write("""
        1. First Time Install
        2. Channel Selection
        3. Install Dependencies
        4. Add Single Channel Manually
        5. Edit Configurations
        6. Exit/Quit
        """)

        menuSelection = get_input("What would you like to do? ")

        if menuSelection == "1":
            logging.info("At main menu, user selected option %s" % menuSelection)
            if not skipDep:
                install_dependencies()
            api_key = get_API_key()
            titleList, idList = get_sub_list(api_key)
            if titleList is None:
                format_youtube_data()
                channel_selection(dataFile, "data/subscription_manager.xml")
            else:
                channel_selection(dataFile, "", titleList, idList)
            setup_config(api_key, configFile)
            write('\n\n\n----------This completes the setup you may now exit-----------\n', GREEN)
            if TESTING:
                exit(0)
        elif menuSelection == "2":
            api_key = get_API_key_config(configFile)
            titleList, idList = get_sub_list(api_key, configFile)
            if titleList is None:
                format_youtube_data()
                channel_selection(dataFile, "data/subscription_manager.xml")
            else:
                channel_selection(dataFile, "", titleList, idList)
        elif menuSelection == "3":
            install_dependencies()
        elif menuSelection == "4":
            add_channel(dataFile)
        elif menuSelection == "5":
            edit_config(configFile)
        elif menuSelection == "6":
            write("\n Goodbye")
            logging.info("User exited program")

            exit()
        else:
            write("\n Not Valid Choice Try again")
            logging.info("Main menu selection of %s rejected, looping" % menuSelection)


if __name__ == "__main__":
    if not os.path.exists('logs/'):
        logging.info("logs directory not found, creating...")
        os.makedirs('logs/')
    if not os.path.isfile('logs/setup.log'):
        logging.info("logs/setup.log not found, creating...")
        open('logs/setup.log', 'a').close()
    logging.basicConfig(filename='logs/setup.log', level=logging.DEBUG, format='%(asctime)s %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')

    logging.info("Program setup.py started")

    configFileInput = ''
    dataFileInput = ''
    skipDep = False
    if len(sys.argv) > 0:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hc:d:s", ["config=", "data=", "skip"])
        except getopt.GetoptError:
            write('\n\nmain.py -c <config file> -d <youtube data file> -s\n\n'
                  '   -c,--config: config file optional, if not provided will default to data/config\n'
                  '       Multiple config files supported just separate with a space and surround with quotes ex.\n'
                  '       main.py -c "config1.txt config2 data/config3"\n'
                  '   -d,--data: data file optional, if not provided will default to data/youtubeData.xml\n'
                  '       This is the file output of channel names and urls.\n'
                  '   -s,--skip: flag to skip dependency check\n\n')
            exit(2)
        for opt, arg in opts:
            if opt == '-h':
                write('\n\nmain.py -c <config file> -d <youtube data file> -s\n\n'
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
                write("--Skipping Dependency check")

        if configFileInput == '':
            configFile = 'data/config'
            # write('--Using data/config')
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
        # write('--Using data/youtubeData.xml')
    else:
        dataFile = dataFileInput

    try:
        name = os.environ.get('TRAVIS')
        if name:
            TESTING = True
            print("Using Travis test settings")
    except:
        print("")

    write("--Outputting data to:" + dataFile)
    write("--Config file:" + configFile)
    main(configFile, dataFile, skipDep)
    logging.info("Program setup.py ended")
    logging.info("====================================================================")
