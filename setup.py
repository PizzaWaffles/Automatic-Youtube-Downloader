import sys
import json
import os
import glob
import pip
import traceback
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict
from sys import platform
import subprocess
import xml.sax.saxutils
import logging

# support for python 3 and 2
if sys.version_info[0] == 3:
    from urllib.request import urlopen
    from urllib import request
else:
    from urllib import urlopen
    import urllib as request

DEBUGLOGGING = False
configFile = "data/config"


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
        from pip import main as pipmain
    except:
        from pip._internal import main as pipmain

    print("Checking Dependencies....")
    _all_ = [
        "beautifulsoup4",
        "listparser",
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
    except Exception as e:
        logging.error("Exception occurred %s" % str(e))
        logPrint("ERROR:\n" + str(e))
        logging.error(traceback.format_exc())
        print("One or more dependencies not met!! Please run 'pip install -r requirements.txt'")
        exit()
    print("Complete.")


def setup_youtube():
    logging.debug("setup_youtube function called")
    api_key = ""
    setup_not_complete = True
    while setup_not_complete:
        print("\n\nSetting up Youtube configs")
        print("Please goto https://www.youtube.com/subscription_manager")
        print("On the bottom of the page click 'Export Subscriptions'")
        print("Put that file in the data directory so it looks like data/subscription_manager.xml")
        get_input("Click enter to continue.....")

        if os.path.exists('data/subscription_manager.xml'):
            print("\nFile Found\n\n")
            logging.info("subscription_manager.xml was found")
            setup_not_complete = False
        else:
            print("File Not Found!! Please make sure you have it in th correct directory and its named correctly")
            logging.warning("subscription_manager.xml was NOT found")
            logging.debug("data folder contents:\n" + str(glob.glob("data/*")))

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


def channel_selection():
    import listparser as lp
    logging.debug("Channel_selection started")
    # This function parses OPML data and allows the user to select which channels to be included
    print("Parsing Youtube data\n")
    all_channels = False
    loop = True
    while loop:
        selection = get_input(
            "Would you like to select which channels you want to include, or do you want to include all of them?\n"
            "If you include all channels you can remove them manually by editing data/youtubeData.xml and deleting the"
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

    logging.debug("Opening data/youtubeData.xml for writing")
    file = open("data/youtubeData.xml", 'w')
    logging.debug("Parsing data/subscription_manager.xml")
    d = lp.parse('data/subscription_manager.xml')
    l = d.feeds
    file.write('<opml version="1.1">\n<body>\n')
    num_channels = len(l)
    human_count = 1

    logging.debug("Processing channels")
    for channel in l:
        include_this_subscription = True
        title = channel.title.replace('&', 'and')
        title = channel.title.encode("ascii", errors="ignore").decode('utf-8', 'ignore')
        url = bytes(channel.url, 'utf-8').decode('utf-8', 'ignore')

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
    logging.debug("Channels saved to youtubeData.xml")
    print("\nComplete.")


def setup_config(api_key):
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
                                 "Make sure you enter the entire address (ex. 'G:\\Plex\\Youtube\\\n')")

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


def main():
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
        4. Exit/Quit
        """)

        menuSelection = get_input("What would you like to do? ")

        if menuSelection == "1":
            logging.info("At main menu, user selected option %s" % menuSelection)
            install_dependencies()
            api_key = setup_youtube()
            channel_selection()
            setup_config(api_key, )
            print('\n\n\n----------This completes the setup you may now exit-----------\n')
        elif menuSelection == "2":
            channel_selection()
        elif menuSelection == "3":
            install_dependencies()
        elif menuSelection == "4":
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
    main()
    logging.info("Program setup.py ended")
    logging.info("====================================================================")
