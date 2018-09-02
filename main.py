import listparser as lp
from bs4 import BeautifulSoup as bs
import youtube_dl
import os, shutil
import string
import glob
import traceback
import json
#from distutils.dir_util import copy_tree
from datetime import datetime
import time
import sys
from pprint import pprint


# Support for both python 2 and 3
if sys.version_info[0] == 3:
	from urllib.request import urlopen
	from urllib import request
else:
	from urllib import urlopen
	import urllib as request

#GLOBAL VARS
NUM_VIDEOS = 0
DESTINATION_FOLDER = ""
API_KEY = ""
FORMAT = "248+251/best"
FILE_FORMAT = "%NAME - %UPLOAD_DATE - %TITLE"
DESTINATION_FORMAT = "%NAME"
SCHEDULING_MODE = ""
SCHEDULING_MODE_VALUE = ""

configFile = 'data/config'
logFileName = "data/log.txt"
if not os.path.isfile('data/log.txt'):
	open('data/log.txt', 'a').close()
if not os.path.isfile('data/icon_log.txt'):
	open('data/icon_log.txt', 'a').close()
if not os.path.exists('Download/'):
	os.makedirs('Download/')

def load_configs(configFile):
	global NUM_VIDEOS
	global DESTINATION_FOLDER
	global API_KEY
	global FORMAT
	global FILE_FORMAT
	global DESTINATION_FORMAT
	global SCHEDULING_MODE
	global SCHEDULING_MODE_VALUE

	try:
		with open(configFile) as f:
			for line in f:
				line = line.rstrip()  # remove newline
				data = line.split("=")
				print("Checking line %s as %s = %s" % (line, data[0], data[1]))

				if data[0] == "SCHEDULING_MODE":
					SCHEDULING_MODE = data[1]

				elif data[0] == "SCHEDULING_MODE_VALUE":
					if data[1].isdigit():
						SCHEDULING_MODE_VALUE = int(data[1])

				elif data[0] == "NUM_VIDEOS":
					NUM_VIDEOS = int(data[1])

				elif data[0] == "DESTINATION_FOLDER":
					DESTINATION_FOLDER = str(data[1])

				elif data[0] == "API_KEY":
					API_KEY = str(data[1])

				elif data[0] == "FILE_FORMAT":
					FILE_FORMAT = str(data[1])

				elif data[0] == "VIDEO_FORMAT":
					FORMAT = str(data[1])

				elif data[0] == "DESTINATION_FORMAT":
					DESTINATION_FORMAT = str(data[1])

	except Exception as e:
		print("Cannot find config file!!")
		print("Error dump in error.log")
		with open('error.log', 'a+') as f:
			f.write(str(datetime.now()) + '\n')
			f.write(str(e))
			f.write(traceback.format_exc())
			f.write("\n\n----------VAR DUMP--------\n\n")
			pprint(globals(), stream=f)
			pprint(locals(), stream=f)
		exit(0)


def get_icons(channel, chid, overwrite=False):
	icon_log = open('data/icon_log.txt', 'r')
	downloaded = icon_log.readlines()
	icon_log.close()
	downloaded = map(str.strip, downloaded)

	if len(channel) == 0:
		if not (chid[0] in downloaded):
			destinationDir = os.path.join('Download', channel[0])
			if not os.path.exists(destinationDir):
				os.makedirs(destinationDir)
			if not os.path.exists(destinationDir):
				print("Creating Source Directory")
				os.makedirs(destinationDir)
			try:
				print("Downloading new icon for poster")
				url_data = urlopen(
					'https://www.googleapis.com/youtube/v3/channels?part=snippet&id='
					+ chid + '&fields=items%2Fsnippet%2Fthumbnails&key=' + API_KEY)
				data = url_data.read()
				data = json.loads(data.decode('utf-8'))
				icon_url = data['items'][0]['snippet']['thumbnails']['high']['url']
				with open(destinationDir + "/poster.jpg", 'wb') as f:
					f.write(request.urlopen(icon_url).read())
				with open('data/icon_log.txt', 'a') as f:
					f.write(chid[0] + '\n')
				#print("Moving Icon...")
				#destinationDir = parseFormat(DESTINATION_FORMAT)
				#destinationDir = os.path.join(DESTINATION_FOLDER, destinationDir)
				#shutil.move('poster.jpg', DESTINATION_FOLDER + 'poster.jpg')
			except Exception as e:
				print("An error occured")
				print("Error dump in error.log")
				with open('error.log', 'a+') as f:
					f.write(str(datetime.now()) + '\n')
					f.write(str(e))
					f.write(traceback.format_exc())
					f.write("\n\n----------VAR DUMP--------\n\n")
					pprint(globals(), stream=f)
					pprint(locals(), stream=f)
	else:
		for j in range(0, len(channel)):
			if (not chid[j] in downloaded) or overwrite:
				destinationDir = os.path.join('Download', channel[j])
				if not os.path.exists(destinationDir):
					os.makedirs(destinationDir)
				try:
					print("Downloading new icon for poster: " + channel[j] + " | " + chid[j])
					url_data = urlopen(
						'https://www.googleapis.com/youtube/v3/channels?part=snippet&id='
						+ chid[j] + '&fields=items%2Fsnippet%2Fthumbnails&key=' + API_KEY)
					data = url_data.read()
					data = json.loads(data.decode('utf-8'))
					icon_url = data['items'][0]['snippet']['thumbnails']['high']['url']
					with open(destinationDir + "\poster.jpg", 'wb') as f:
						f.write(request.urlopen(icon_url).read())

					with open('data/icon_log.txt', 'a+') as f:
						f.write(chid[j] + '\n')

				except Exception as e:
					print("An error occured")
					print("Error dump in error.log")
					with open('error.log', 'a+') as f:
						f.write(str(datetime.now()) + '\n')
						f.write(str(e))
						f.write(traceback.format_exc())
						f.write("\n\n----------VAR DUMP--------\n\n")
						pprint(globals(), stream=f)
						pprint(locals(), stream=f)
			print()

def safecopy(src, dst):
	if os.path.isdir(dst):
		dst = os.path.join(dst, os.path.basename(src))
	shutil.copyfile(src, dst)

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

def main():
	global NUM_VIDEOS
	global DESTINATION_FOLDER
	global API_KEY
	global FORMAT
	global FILE_FORMAT
	global SCHEDULING_MODE
	global SCHEDULING_MODE_VALUE

	number_of_runs_completed = 0
	did_i_just_complete_run = False
	minutes_to_wait = 0

	while True:
		print("Starting on run number %s" % number_of_runs_completed)
		if SCHEDULING_MODE == "TIME_OF_DAY":
			print("Evaluating time of day run for %s schedule mode" % SCHEDULING_MODE_VALUE)
			if did_i_just_complete_run:
				minutes_to_wait = 24 * 60
				print("  Just completed run, need to wait %s minutes" % minutes_to_wait)
				did_i_just_complete_run = False
			else:
				minutes_to_wait = (SCHEDULING_MODE_VALUE - datetime.now().hour) * 60
				if minutes_to_wait < 0:
					minutes_to_wait += 24 * 60

				minutes_to_wait -= datetime.now().minute
				print("  First scheduled run set for %s minutes from now" % minutes_to_wait)

		elif SCHEDULING_MODE == "RUN_ONCE":
			print("Evaluating run once schedule mode")
			if did_i_just_complete_run:
				print("  Just completed run, ending")
				break
			else:
				print("  Starting run once")

		elif SCHEDULING_MODE == "DELAY":
			print("Evaluating delay schedule mode")
			if did_i_just_complete_run:
				minutes_to_wait = SCHEDULING_MODE_VALUE
				print("  Next run in %s minutes" % minutes_to_wait)
			else:
				print("  First run, doing it now")

		else:
			print("Unknown SCHEDULING_MODE found %s" % SCHEDULING_MODE)
			#todo this should throw an exception
			break

		print("Sleeping for %s minutes..." % minutes_to_wait)
		time.sleep(minutes_to_wait * 60)

		data = lp.parse("data/youtubeData.xml")

		# init for usage outside of this for loop
		xmltitle = [None] * len(data.feeds)
		xmlurl = [None] * len(data.feeds)
		channelIDlist = [None] * len(data.feeds)
		valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

		for i in range(0, len(data.feeds)):
			xmltitle[i] = data.feeds[i].title  # channel Title
			xmlurl[i] = data.feeds[
				i].url  # formatted like 'https://www.youtube.com/feeds/videos.xml?channel_id=CHANNELID'
			indexofid = xmlurl[i].find("id=")
			channelIDlist[i] = xmlurl[i][indexofid + 3:]
		get_icons(xmltitle, channelIDlist)

		for i in range(0, len(xmltitle)):  # for every channel
			uploader = xmltitle[i]
			print(uploader)
			url_data = urlopen(xmlurl[i],)
			url_data = url_data.read()
			xml = bs(url_data.decode('utf-8'), 'html.parser')
			videoList = xml.find_all('entry')
			# print(xml.find_all('entry'))

			video_download_count = 0
			for v in videoList:  # for every video in channel
				# make sure we only download how many we want
				if video_download_count < NUM_VIDEOS:
					skip_download = False
					video_download_count += 1
					title = v.title.string
					url = v.link.get('href')
					upload_date = v.published.string.split('T')[0]
					id = v.id.string
					channelID = str(v.find('yt:channelid').contents[0])
					# See if we already downloaded this
					logFile = open(logFileName, 'r')
					logFileContents = logFile.read()
					logFile.close()
					if id in logFileContents:
						print("Video Already downloaded")
					else:
						filename_format = parseFormat(FILE_FORMAT, uploader, upload_date, title, channelID, id)

						print("Downloading - " + title + "  |  " + id)
						print("Channel - " + str(xmltitle[i]) + "  |  " + channelID)

						if os.name == 'nt':  # if windows use supplied ffmpeg
							ydl_opts = {
								'outtmpl': 'Download/' + uploader + '/' + filename_format + '.%(ext)s',
							# need to put channelid in here because what youtube-dl gives may be incorrect
								# 'simulate': 'true',
								'writethumbnail': 'true',
								'forcetitle': 'true',
								'ffmpeg_location': './ffmpeg/bin/',
								'format': FORMAT
							}
						else:
							# not sure here
							ydl_opts = {
								'outtmpl': 'Download/' + filename_format + '.%(ext)s',
								'writethumbnail': 'true',
								'forcetitle': 'true',
								'format': FORMAT
							}
						try:
							with youtube_dl.YoutubeDL(ydl_opts) as ydl:
								info_dict = ydl.extract_info(url, download=False)
								video_id = info_dict.get("id", None)
								video_title = info_dict.get("title", None)
								video_date = info_dict.get("upload_date", None)
								uploader = info_dict.get("uploader", None)
								is_live = info_dict.get("is_live", None)
								if not is_live:
									ydl.download([url])
								else:
									print("Warning! This video is streaming live, it will be skipped")
									skip_download = True

						except Exception as e:
							print("Failed to Download")
							print("Error dump in error.log")
							skip_download = True
							with open('error.log', 'a+') as f:
								f.write(str(datetime.now()) + '\n')
								f.write(str(e))
								f.write(traceback.format_exc())
								f.write("\n\n----------VAR DUMP--------\n\n")
								pprint(globals(), stream=f)
								pprint(locals(), stream=f)

						if not skip_download:
							sourceDir = 'Download/' + uploader + '/'
							destinationDir = parseFormat(DESTINATION_FORMAT, uploader, upload_date, title, channelID,
														 id)
							destinationDir = os.path.join(DESTINATION_FOLDER, destinationDir)

							if not os.path.exists(destinationDir):
								print("Creating Source Directory")
								os.makedirs(destinationDir)
							try:
								print("Moving Folder...")

								for filename in os.listdir(sourceDir):
									safecopy(os.path.join(sourceDir, filename), destinationDir)

								shutil.rmtree(sourceDir, ignore_errors=True)
								# shutil.move(videoName, destination + destVideoName)
								# shutil.move(thumbName, destination + destThumbName)
								# everything was successful so log that we downloaded and moved the video
								logFile = open(logFileName, 'a')
								logFile.write(id + ' \n')
								logFile.close()
							except Exception as e:
								print("An error occured moving file")
								print("Error dump in error.log")
								with open('error.log', 'a+') as f:
									f.write(str(datetime.now()) + '\n')
									f.write(str(e))
									f.write(traceback.format_exc())
									f.write("\n\n----------VAR DUMP--------\n\n")
									pprint(globals(), stream=f)
									pprint(locals(), stream=f)
							print()
			print()

		number_of_runs_completed += 1
		did_i_just_complete_run = True

if __name__ == "__main__":
	load_configs(configFile)
	main()
