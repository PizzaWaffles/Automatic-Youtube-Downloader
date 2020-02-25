import listparser as lp
from bs4 import BeautifulSoup as bs
import youtube_dl
import os, shutil
import string
import glob
import traceback
import json
# from distutils.dir_util import copy_tree
from datetime import datetime
import time
import sys, getopt
from pprint import pprint
import logging
import re
import fnmatch
import subprocess
from colorama import init
from colorama import Fore, Back, Style
from tendo import singleton
from sys import platform

# Support for both python 2 and 3
if sys.version_info[0] == 3:
    from urllib.request import urlopen
    from urllib import request
else:
    print("\nError, please install python3.\n")
    exit(1)

# Start Colorizer
init()

# GLOBAL VARS
NUM_VIDEOS = 0
DESTINATION_FOLDER = ""
API_KEY = ""
FORMAT = "1080p"  # default if not specified in config
FILE_FORMAT = "%NAME - %UPLOAD_DATE - %TITLE"
DESTINATION_FORMAT = "%NAME"
SCHEDULING_MODE = ""
SCHEDULING_MODE_VALUE = ""
YOUTUBE_XML_FILE = "data/youtubeData.xml"

# Constant
FILTER_FOLDER = "data/filters/"

# Colorizer constants
RED = Fore.RED
GREEN = Fore.GREEN
BLUE = Fore.CYAN
MAGENTA = Fore.MAGENTA
LIGHT_BLUE = Fore.LIGHTCYAN_EX

# No longer using codes in config file, use human readable tags ex '1080p'
VIDEO_QUALITY_LIST = [
    ['480p', '720p', '1080p HD', '1440p QHD', '2160p 4k', '4320p 8k'],
    ['244+251/best', '247+251/best', '248+251/299+140/137+140/best', '271+251/best', '313+251/best', '272+251/best']
]


def write(s, color=None):
    if color is None:
        print(s)
    else:
        print(color + s + Style.RESET_ALL)


def load_configs(configFile):
    global NUM_VIDEOS
    global DESTINATION_FOLDER
    global API_KEY
    global FORMAT
    global FILE_FORMAT
    global DESTINATION_FORMAT
    global SCHEDULING_MODE
    global SCHEDULING_MODE_VALUE
    global YOUTUBE_XML_FILE

    logging.info("Loading config file from %s" % configFile)

    try:
        with open(configFile) as f:
            for line in f:
                line = line.rstrip()  # remove newline
                data = line.split("=")
                logging.debug("Checking line %s as %s = %s" % (line, data[0], data[1]))

                if data[0] == "SCHEDULING_MODE":
                    SCHEDULING_MODE = data[1]
                    logging.info("Setting %s to %s" % (data[0], data[1]))

                elif data[0] == "SCHEDULING_MODE_VALUE":
                    if data[1].isdigit():
                        SCHEDULING_MODE_VALUE = int(data[1])
                        logging.info("Setting %s to %s" % (data[0], data[1]))

                elif data[0] == "NUM_VIDEOS":
                    NUM_VIDEOS = int(data[1])
                    logging.info("Setting %s to %s" % (data[0], data[1]))

                elif data[0] == "DESTINATION_FOLDER":
                    DESTINATION_FOLDER = str(data[1])
                    logging.info("Setting %s to %s" % (data[0], data[1]))

                elif data[0] == "API_KEY":
                    API_KEY = str(data[1])
                    logging.info("Setting %s to %s" % (data[0], data[1]))

                elif data[0] == "FILE_FORMAT":
                    FILE_FORMAT = str(data[1])
                    logging.info("Setting %s to %s" % (data[0], data[1]))

                elif data[0] == "VIDEO_FORMAT":
                    FORMAT = str(data[1])
                    logging.info("Setting %s to %s" % (data[0], data[1]))

                elif data[0] == "DESTINATION_FORMAT":
                    DESTINATION_FORMAT = str(data[1])
                    logging.info("Setting %s to %s" % (data[0], data[1]))

                elif data[0] == "YOUTUBE_XML_FILE":
                    YOUTUBE_XML_FILE = str(data[1])
                    logging.info("Setting %s to %s" % (data[0], data[1]))
        return NUM_VIDEOS, DESTINATION_FOLDER, API_KEY, FORMAT, FILE_FORMAT, DESTINATION_FORMAT, SCHEDULING_MODE, SCHEDULING_MODE_VALUE, YOUTUBE_XML_FILE

    except Exception as e:
        logging.error("Cannot find config file!!")
        write("Cannot find config file!!", RED)
        logging.error(str(e))
        logging.error(traceback.format_exc())
        logVariables()
        exit(0)


def check_channelID(channelID):
    tempData = ""
    if ("UC" in channelID) and (len(channelID) is 24):
        try:
            url_data = urlopen('https://www.youtube.com/feeds/videos.xml?channel_id=' + channelID, )
            url_data = url_data.read()
            xml = bs(url_data.decode('utf-8'), 'html.parser')
            tempData = xml.find('name').get_text(strip=True)
            print()
        except Exception as e:
            write("Failed to Download Channel list due to html error, check logs", RED)
            videoList = ""
            return 0
    else:
        return 0
    return tempData


def check_dependencies():
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


def logVariables():
    dicGlobal = globals()
    logging.error("-------Global Vars------")
    for key in dicGlobal.keys():
        logging.error(str(key) + ' = ' + str(dicGlobal[key]).replace('\r', ' ').replace('\n', ' '))

    '''dicLocal = locals()
    logging.error("-------Local Vars------")
    for key in dicLocal.keys():
        logging.error(str(key) + ' = ' + str(dicLocal[key]).replace('\r', ' ').replace('\n', ' '))'''


def get_icons(channel, chid, overwrite=False):
    logging.info("get_icons called")
    icon_log = open('data/icon_log.txt', 'r')
    temp = icon_log.readlines()
    icon_log.close()
    downloaded = [None] * len(temp)
    for d in range(0, len(temp)):
        downloaded[d] = temp[d].strip()

    write("Downloading Icons....", BLUE)
    if len(channel) == 0:
        write("Error youtubeData.xml file empty please run setup.py to fix", RED)

    else:
        for j in range(0, len(channel)):
            if (not chid[j] in downloaded) or overwrite:
                destinationDir = os.path.join('Download', channel[j])
                if not os.path.exists(destinationDir):
                    logging.info("destination directory was not found for %s" % destinationDir)
                    os.makedirs(destinationDir)
                try:
                    logging.info("Downloading new icon for poster: %s | %s" % (channel[j], chid[j]))
                    url_data = urlopen(
                        'https://www.googleapis.com/youtube/v3/channels?part=snippet&id='
                        + chid[j] + '&fields=items%2Fsnippet%2Fthumbnails&key=' + API_KEY)

                    logging.info("icon url is [not recorded due to API key being included]")

                    data = url_data.read()
                    data = json.loads(data.decode('utf-8'))
                    icon_url = data['items'][0]['snippet']['thumbnails']['high']['url']
                    with open(os.path.join(destinationDir, "poster.jpg"), 'wb') as f:
                        f.write(request.urlopen(icon_url).read())

                    if not os.path.isdir(os.path.join(DESTINATION_FOLDER, channel[j])):
                        os.mkdir(os.path.join(DESTINATION_FOLDER, channel[j]))

                    # Move file
                    safecopy(os.path.join(destinationDir, "poster.jpg"),
                             os.path.join(DESTINATION_FOLDER, channel[j], 'poster.jpg'))
                    shutil.rmtree(os.path.dirname(destinationDir))

                    with open('data/icon_log.txt', 'a+') as f:
                        f.write(chid[j] + '\n')
                except Exception as e:
                    print(str(e))
                    print(Fore.RED + "An error occurred downloading icons, Please check logs" + Style.RESET_ALL)
                    logging.error(str(e))
                    logging.error(traceback.format_exc())
                    logVariables()
    write("Complete.", GREEN)


# src is directory plus filename
# dst is directory with or without filename
def safecopy(src, dst):
    src = os.path.join(os.getcwd(), src)
    logging.debug("safecopy requested from %s to %s" % (src, dst))
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    shutil.copy(src, dst)


def parseFormat(formating, name="", date="", title="", chID="", id=""):
    '''
        Supported tags:
    %NAME
    %UPLOAD_DATE
    %TITLE
    %CHANNEL_ID
    %VIDEO_ID
    '''

    formating = formating.split('%')
    result = ""
    for f in formating:
        if f.find('NAME') is not -1:
            result += f.replace("NAME", name)
        elif f.find("UPLOAD_DATE") is not -1:
            result += f.replace("UPLOAD_DATE", date)
        elif f.find("TITLE") is not -1:
            result += f.replace("TITLE", title)
        elif f.find("CHANNEL_ID") is not -1:
            result += f.replace("CHANNEL_ID", chID)
        elif f.find("VIDEO_ID") is not -1:
            result += f.replace("VIDEO_ID", id)
        else:
            result += f
    return result


class filters:
    filtersListType = []
    filtersListArg = []
    channelID = []

    def __init__(self):
        if not os.path.exists(FILTER_FOLDER):
            os.makedirs(FILTER_FOLDER)
        files = os.listdir(FILTER_FOLDER)
        for i in range(0, len(files)):
            handler = open(FILTER_FOLDER + files[i])
            filters = handler.readlines()

            for j in range(0, len(filters)):  # filters per file/channel
                temp = filters[j].strip().split('"')
                self.filtersListType.append(temp[0].replace(" ", ""))
                self.filtersListArg.append(temp[1].lower())
                self.channelID.append(files[i])

                # print(self.channelID)

    def download_check(self, title, chID):
        title = title.lower()

        # Returns true if filters don't match title
        for idx, channel in enumerate(self.channelID):
            if chID == channel:
                arg = self.filtersListArg[idx].replace('*', '.*')
                if re.search(arg, title):
                    if self.filtersListType[idx] == "deny-only":
                        return False
                    elif self.filtersListType[idx] == "allow-only":
                        return True

        # Nothing matches if we find a allow-only tag we need to deny everything else
        for idx in range(0, len(self.channelID)):
            if chID == self.channelID[idx]:
                if "allow-only" == self.filtersListType[idx]:
                    return False
        return True


class scheduling:
    global NUM_VIDEOS
    global DESTINATION_FOLDER
    global API_KEY
    global FORMAT
    global FILE_FORMAT
    global SCHEDULING_MODE
    global SCHEDULING_MODE_VALUE
    global YOUTUBE_XML_FILE

    def __init__(self):
        self.number_of_runs_completed = 0
        self.did_i_just_complete_run = False
        self.minutes_to_wait = 0

    def increase_run(self):
        self.number_of_runs_completed += 1
        self.did_i_just_complete_run = True

    def getNumRuns(self):
        return self.number_of_runs_completed

    def run(self):

        print("Starting on run number %s" % self.number_of_runs_completed)
        logging.info("Starting on run number %s" % self.number_of_runs_completed)
        if SCHEDULING_MODE == "TIME_OF_DAY":
            logging.info("Evaluating time of day run for %s schedule mode" % SCHEDULING_MODE_VALUE)
            if self.did_i_just_complete_run:
                self.minutes_to_wait = 24 * 60
                logging.debug("  Just completed run, need to wait %s minutes" % self.minutes_to_wait)
                self.did_i_just_complete_run = False
            else:
                self.minutes_to_wait = (SCHEDULING_MODE_VALUE - datetime.now().hour) * 60
                if self.minutes_to_wait < 0:
                    self.minutes_to_wait += 24 * 60

                    self.minutes_to_wait -= datetime.now().minute
                print("  First scheduled run set for %s minutes from now" % self.minutes_to_wait)

        elif SCHEDULING_MODE == "RUN_ONCE":
            logging.info("Evaluating run once schedule mode")
            if self.did_i_just_complete_run:
                logging.info("  Just completed run, ending")
                sys.exit(0)
                # break
            else:
                logging.info("  Starting run once")

        elif SCHEDULING_MODE == "DELAY":
            logging.info("Evaluating delay schedule mode")
            if self.did_i_just_complete_run:
                self.minutes_to_wait = SCHEDULING_MODE_VALUE
                logging.info("  Next run in %s minutes" % self.minutes_to_wait)
            else:
                logging.info("  First run, doing it now")

        else:
            logging.info("Unknown SCHEDULING_MODE found %s" % SCHEDULING_MODE)
            raise Exception("Unknown SCHEDULING_MODE found %s" % SCHEDULING_MODE)
            exit(2)
            # break

        logging.info("Sleeping for %s minutes..." % self.minutes_to_wait)
        time.sleep(self.minutes_to_wait * 60)

        self.number_of_runs_completed += 1
        self.did_i_just_complete_run = True
        # Now run main


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'(?u)[^-\w .]', '', value).strip()
    value = value.replace(":", "")
    return value


def main(my_sch):
    global NUM_VIDEOS
    global DESTINATION_FOLDER
    global API_KEY
    global FORMAT
    global FILE_FORMAT
    global SCHEDULING_MODE
    global SCHEDULING_MODE_VALUE
    global YOUTUBE_XML_FILE

    data = lp.parse(YOUTUBE_XML_FILE)
    logFileName = "data/log.txt"

    my_filters = filters()

    # init for usage outside of this for loop
    xmltitle = [None] * len(data.feeds)
    xmlurl = [None] * len(data.feeds)
    channelIDlist = [None] * len(data.feeds)
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

    for i in range(0, len(data.feeds)):
        xmltitle[i] = slugify(data.feeds[i].title)  # channel Title
        xmlurl[i] = data.feeds[
            i].url  # formatted like 'https://www.youtube.com/feeds/videos.xml?channel_id=CHANNELID'
        indexofid = xmlurl[i].find("id=")
        channelIDlist[i] = xmlurl[i][indexofid + 3:]

    if my_sch.getNumRuns() == 1:
        get_icons(xmltitle, channelIDlist)

    for i in range(0, len(xmltitle)):  # for every channel
        skip_download = False
        uploader = xmltitle[i]
        # print(uploader)
        try:
            url_data = urlopen(xmlurl[i], )
            url_data = url_data.read()
            xml = bs(url_data.decode('utf-8'), 'html.parser')
            videoList = xml.find_all('entry')
        except Exception as e:
            print(Fore.RED + "Failed to Download Channel list due to html error, check logs" + Style.RESET_ALL)
            videoList = ""
            skip_download = True
            logging.error(str(e))
            logging.error(traceback.format_exc())
            logVariables()

        video_download_count = 0
        for v in videoList:  # for every video in channel
            # make sure we only download how many we want
            if (video_download_count < NUM_VIDEOS) and not skip_download:
                skip_download = False
                skip_move = False
                video_download_count += 1

                title = str(v.title.string)
                # title = title.decode("utf-8")
                # temp = title.encode("ascii", errors="ignore").decode('utf-8', 'ignore')
                title = title.encode("utf-8", errors="ignore").decode('utf-8', 'ignore')
                escapes = '|'.join([chr(char) for char in range(1, 32)])
                title = re.sub(escapes, "", title)  # removes all escape characters
                title = title.replace("-", " ").replace("\\", "").replace("/", "").replace("%", "")
                title = slugify(title)

                upload_time = v.published.string.split('T')[1].split('+')[0].replace(':', '')[:-2]
                upload_date = v.published.string.split('T')[0]
                upload_date = upload_date + "_" + upload_time
                url = v.link.get('href')
                id = v.id.string
                channelID = str(v.find('yt:channelid').contents[0])
                # See if we already downloaded this
                logFile = open(logFileName, 'r')
                logFileContents = logFile.read()
                logFile.close()
                if id in logFileContents:
                    logging.info("Video Already downloaded for id %s" % id)
                    # print("Video Already downloaded: " + id)
                else:
                    if not my_filters.download_check(title, channelID):
                        # print("Video Filtered: " + title)
                        logging.info("Video Filtered: Title:" + title + "ChannelID:" + channelID)
                        skip_download = True
                        skip_move = True

                    filename_format = parseFormat(FILE_FORMAT, uploader, upload_date, title, channelID,
                        id.replace("yt:video:", ""))
                    logging.debug("filename_formatted parsed to %s" % filename_format)

                    if not skip_download:
                        logging.info("Downloading - " + title + "  |  " + id)
                        logging.info("Channel - " + str(xmltitle[i]) + "  |  " + channelID)

                        # Get format codes to use
                        usable_extension = 'webm'
                       # usable_format_code_video = 'bestvideo[ext=webm]'
                       # usable_format_code_audio = 'bestaudio'
                        containsWebmContent = False

                        usable_format_code_audio = '(bestaudio[ext=m4a]/bestaudio)'
                        usable_format_code_video = '(bestvideo[vcodec^=av01][height>=2160][fps>30]/' \
                                              'bestvideo[vcodec=vp9.2][height>=2160][fps>30]/' \
                                              'bestvideo[vcodec=vp9][height>=2160][fps>30]/' \
                                              'bestvideo[vcodec^=av01][height>=2160]/' \
                                              'bestvideo[vcodec=vp9.2][height>=2160]/' \
                                              'bestvideo[vcodec=vp9][height>=2160]/' \
                                              'bestvideo[height>=2160]/' \
                                              'bestvideo[vcodec^=av01][height>=1440][fps>30]/' \
                                              'bestvideo[vcodec=vp9.2][height>=1440][fps>30]/' \
                                              'bestvideo[vcodec=vp9][height>=1440][fps>30]/' \
                                              'bestvideo[vcodec^=av01][height>=1440]/' \
                                              'bestvideo[vcodec=vp9.2][height>=1440]/' \
                                              'bestvideo[vcodec=vp9][height>=1440]/' \
                                              'bestvideo[height>=1440]/' \
                                              'bestvideo[vcodec^=av01][height>=1080][fps>30]/' \
                                              'bestvideo[vcodec=vp9.2][height>=1080][fps>30]/' \
                                              'bestvideo[vcodec=vp9][height>=1080][fps>30]/' \
                                              'bestvideo[vcodec^=av01][height>=1080]/' \
                                              'bestvideo[vcodec=vp9.2][height>=1080]/' \
                                              'bestvideo[vcodec=vp9][height>=1080]/' \
                                              'bestvideo[height>=1080]/' \
                                              'bestvideo[vcodec^=av01][height>=720][fps>30]/' \
                                              'bestvideo[vcodec=vp9.2][height>=720][fps>30]/' \
                                              'bestvideo[vcodec=vp9][height>=720][fps>30]/' \
                                              'bestvideo[vcodec^=av01][height>=720]/' \
                                              'bestvideo[vcodec=vp9.2][height>=720]/' \
                                              'bestvideo[vcodec=vp9][height>=720]/' \
                                              'bestvideo[height>=720]/' \
                                              'bestvideo)'

                        try:
                            if FORMAT.split(" ")[0] == 'best':
                                logging.info("Skipping getting format codes using granulated option")
                            else:
                                with youtube_dl.YoutubeDL() as ydl:
                                    info_dict = ydl.extract_info(url, download=False)
                                    formats = info_dict.get("formats", None)
                                    for f in formats:
                                        note = f.get('format_note')
                                        fID = f.get('format_id')
                                        extension = f.get('ext')

                                        if FORMAT.split(" ")[0] == note:
                                            usable_format_code_video = fID
                                            usable_extension = extension
                                            containsWebmContent = True
                                            break

                                    for f in formats:
                                        note = f.get('format_note')
                                        fID = f.get('format_id')
                                        extension = f.get('ext')

                                        if usable_extension == extension and note == 'audio only':
                                            usable_format_code_audio = fID

                                if not containsWebmContent:
                                    usable_format_code_video = 'bestvideo'
                                    usable_format_code_audio = 'bestaudio'

                        except Exception as e:
                            logging.error(str(e))
                            if str(e) == "ERROR: This video is unavailable.":
                                logging.error("This video is not available for download, "
                                              "maybe streaming or just an announcement post.")
                                write("This video is not available for download, "
                                      "maybe streaming or just an announcement post.", RED)
                                skip_download = True
                                skip_move = True
                            else:
                                logging.error("An error occurred trying to find user requested format,"
                                              " reverting to best")
                                usable_format_code_video = 'bestvideo'
                                usable_format_code_audio = 'bestaudio'
                                write("Couldn't find request format for this video, defaulting to best", RED)

                    if not skip_download:
                        if os.name == 'nt':  # if windows use supplied ffmpeg
                            ydl_opts = {
                                'outtmpl': os.path.join('Download', uploader, filename_format + '.%(ext)s'),
                                # need to put channelid in here because what youtube-dl gives may be incorrect
                                # 'simulate': 'true',
                                'writethumbnail': 'true',
                                'forcetitle': 'true',
                                'ffmpeg_location': './ffmpeg/bin/',
                                'ignoreerrors': 'true',
                                'format': usable_format_code_video + "+" + usable_format_code_audio + '/best'
                            }
                        else:
                            # Linux/Unix
                            ydl_opts = {
                                'outtmpl': os.path.join('Download', uploader, filename_format + '.%(ext)s'),
                                'writethumbnail': 'true',
                                'forcetitle': 'true',
                                'format': usable_format_code_video + "+" + usable_format_code_audio + '/best'
                            }
                        try:
                            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                                info_dict = ydl.extract_info(url, download=False)
                                quality = info_dict.get("format", None)
                                write("Video Quality: " + quality, BLUE)
                                video_id = info_dict.get("id", None)
                                video_title = info_dict.get("title", None)
                                video_date = info_dict.get("upload_date", None)
                                is_live = info_dict.get("is_live", None)
                                if 'entries' in info_dict:
                                    is_live = info_dict['entries'][0]["is_live"]
                                if not is_live:
                                    ydl.download([url])
                                else:
                                    write("Warning! This video is streaming live, it will be skipped", RED)
                                    logging.info("Warning! This video is streaming live, it will be skipped")
                                    skip_move = True

                            if os.path.exists('Download/' + uploader + '/'):
                                for file in os.listdir('Download/' + uploader + '/'):
                                    if fnmatch.fnmatch(file, "*" + video_title + "*.part"):
                                        skip_move = True
                                        write("Failed to Download. Will Retry on next Run.", RED)
                                        logging.error("Found .part file. Failed to Download. Will Retry next Run.")

                        except Exception as e:
                            skip_move = True
                            logging.error(str(e))

                            if str(e) == "ERROR: This video is unavailable.":
                                logging.error("This video is not available for download, "
                                              "maybe streaming or just an announcement post.")
                                write("This video is not available for download, "
                                      "maybe streaming or just an announcement post.", RED)
                            else:
                                logging.error("Failed to download video")
                                write("Failed to Download", RED)
                                logging.error(traceback.format_exc())
                                logVariables()

                    if not skip_move:
                        destinationDir = parseFormat(DESTINATION_FORMAT, uploader, upload_date, title, channelID, id)
                        destinationDir = os.path.join(DESTINATION_FOLDER, destinationDir)

                        subscription_source_dir = 'Download/' + uploader + '/'
                        logging.debug("subscription_source_dir is %s" % subscription_source_dir)
                        logging.debug("subscription_destination_dir is %s" % destinationDir)

                        if not os.path.exists(destinationDir):
                            logging.info(
                                "Creating uploader destination directory for %s" % destinationDir)
                            os.makedirs(destinationDir)
                        try:
                            logging.info("Now moving content from %s to %s" % (
                            subscription_source_dir, destinationDir))

                            for filename in os.listdir(subscription_source_dir):
                                logging.info("Checking file %s" % filename)
                                source_to_get = os.path.join(subscription_source_dir, filename)
                                logging.info("Moving file %s to %s" % (source_to_get, destinationDir))
                                safecopy(source_to_get, destinationDir)
                                # shutil.move(os.path.join(subscription_source_dir, filename), subscription_destination_dir)

                            shutil.rmtree(subscription_source_dir, ignore_errors=True)
                            # shutil.move(videoName, destination + destVideoName)
                            # shutil.move(thumbName, destination + destThumbName)
                            # everything was successful so log that we downloaded and moved the video
                            logFile = open(logFileName, 'a')
                            logFile.write(id + ' \n')
                            logFile.close()
                            logging.info("Successfully downloaded and moved file")
                            write("Success!", GREEN)
                        except Exception as e:
                            print(str(e))
                            write("An error occured moving file", RED)
                            logging.error(str(e))
                            logging.error(traceback.format_exc())
                            logVariables()

            skip_download = False
            skip_move = False

    logging.info("Program main.py ended")
    logging.info("============================================================")
    return ""


def start():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    print("Current Working Directory:" + os.getcwd() + '\n')

    configFileInput = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvc:", ["config="])
    except getopt.GetoptError:
        print('main.py -c <config file(optional)>\n'
              '   -c: config file optional, if not provided will default to data/config\n'
              '       Multiple config files supported just separate with a space and surround with quotes ex.\n'
              '       main.py -c "config1.txt config2 data/config3"\n')
        exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('main.py -c <config file(optional)>\n'
                  '   -c: config file optional, if not provided will default to data/config\n'
                  '       Multiple config files supported just separate with a space and surround with quotes ex.\n'
                  '       main.py -c "config1.txt config2 data/config3"\n'
                  '   -v: version number')
            exit()
        elif opt in ("-c", "--config"):
            configFileInput = arg
        elif opt == '-v':
            if os.path.isfile('pyproject.toml'):
                with open("pyproject.toml") as f:
                    lines = f.readlines()
                    version = lines[2].split("=")[1].strip()
                    write("Version:" + version)
            else:
                write("Version: 0.1-Pre")
            exit()

    # check if another instance is running
    me = singleton.SingleInstance()  # will sys.exit(-1) if other instance is running

    try:
        check_dependencies()
    except Exception as e:
        print(str(e))
        write("Error, checking dependencies please run setup.py and install dependencies", RED)

    if not os.path.isfile('main.log'):
        open('logs/main.log', 'a').close()
    loggingFile = open('main.log', 'a', encoding='utf-8')
    logging.basicConfig(stream=loggingFile, level=logging.DEBUG, format='%(asctime)s %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info("Program main.py started")

    if not os.path.isfile('data/log.txt'):
        logging.warning("data/log.txt not found... creating")
        open('data/log.txt', 'a').close()
    if not os.path.isfile('data/icon_log.txt'):
        open('data/icon_log.txt', 'a').close()
        logging.warning("data/icon_log.txt not found... creating")
    if not os.path.exists('Download/'):
        os.makedirs('Download/')

    # configFile = [None] * len(opts)
    if configFileInput == '':
        configFile = 'data/config'
        print('--Using data/config')
        if not os.path.isfile('data/config'):
            print('Error config file not found at: data/config')
            exit(2)
    else:
        configFile = configFileInput.split(' ')
        for f in configFile:
            if not os.path.isfile(f):
                print('Error config file not found at: ' + os.path.join(os.getcwd(), f))
                exit(2)

    sch = scheduling()  # init class
    sch.increase_run()
    while True:
        if type(configFile) is list:
            for l in configFile:  # for every config file run main
                # print("Running config:'" + l + "'")
                load_configs(l)
                main(sch)
        else:
            # print("Running config:'" + configFile + "'")
            load_configs(configFile)
            main(sch)
        sch.run()

if __name__ == "__main__":
    start()
