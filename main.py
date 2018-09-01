import listparser as lp
from bs4 import BeautifulSoup as bs
import youtube_dl
import os, shutil
import string
import glob
import traceback
import json
from distutils.dir_util import copy_tree
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
START_HOUR = 0
NUM_VIDEOS = 0
DESTINATION_FOLDER = ""
API_KEY = ""
DELAY = 0

configFile = 'data/config'
logFileName = "data/log.txt"


def load_configs(configFile):
	global START_HOUR
	global NUM_VIDEOS
	global DESTINATION_FOLDER
	global API_KEY
	global DELAY

	with open(configFile) as f:
		for line in f:
			line = line.rstrip() # remove newline
			if line.find("START_HOUR") != -1:
				data = line.split("=")
				START_HOUR = int(data[1])
			elif line.find("NUM_VIDEOS") != -1:
				data = line.split("=")
				NUM_VIDEOS = int(data[1])
			elif line.find("DESTINATION_FOLDER") != -1:
				data = line.split("=")
				DESTINATION_FOLDER = str(data[1])
			elif line.find("API_KEY") != -1:
				data = line.split("=")
				API_KEY = str(data[1])
			elif line.find("DELAY") != -1:
				data = line.split("=")
				DELAY = int(data[1])


def get_icons(channel, chid, overwrite=False):
	if len(channel) == 0:
		#Skip check for icon file if we are doing a single channel
		destinationDir = DESTINATION_FOLDER + channel + '/'
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
			with open("poster.jpg", 'wb') as f:
				f.write(request.urlopen(icon_url).read())

			print("Moving Icon...")
			shutil.move('poster.jpg', destinationDir + 'poster.jpg')
		except Exception as e:
			print("An error occured moving Icon")
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
			destinationDir = DESTINATION_FOLDER + channel[j] + ' [Youtube-' + chid[j] + ']/'
			if not os.path.exists(destinationDir + 'poster.jpg') or overwrite:
				if not os.path.exists(destinationDir):
					print("Creating Source Directory")
					os.makedirs(destinationDir)
				try:
					print("Downloading new icon for poster: " + channel[j] + " | " + chid[j])
					url_data = urlopen(
						'https://www.googleapis.com/youtube/v3/channels?part=snippet&id='
						+ chid[j] + '&fields=items%2Fsnippet%2Fthumbnails&key=' + API_KEY)
					data = url_data.read()
					data = json.loads(data.decode('utf-8'))
					icon_url = data['items'][0]['snippet']['thumbnails']['high']['url']
					with open("poster.jpg", 'wb') as f:
						f.write(request.urlopen(icon_url).read())

					print("Moving Icon...")
					#shutil.move('poster.jpg', destinationDir + 'poster.jpg')
					safecopy('poster.jpg', destinationDir + 'poster.jpg')
				except Exception as e:
					print("An error occured moving Icon")
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




def main():
	global START_HOUR
	global NUM_VIDEOS
	global DESTINATION_FOLDER
	global API_KEY
	global DELAY

	while True:
		now = datetime.now()

		if now.hour == START_HOUR or START_HOUR == 0:      # Run once a day at this hour or skip check if we are using delay
			data = lp.parse("data/youtubeData.xml")

			# init for usage outside of this for loop
			xmltitle = [None] * len(data.feeds)
			xmlurl = [None] * len(data.feeds)
			channelIDlist = [None] * len(data.feeds)
			valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

			for i in range(0, len(data.feeds)):
				xmltitle[i] = data.feeds[i].title       #channel Title
				xmlurl[i] = data.feeds[i].url   # formated like 'https://www.youtube.com/feeds/videos.xml?channel_id=CHANNELID'
				indexofid = xmlurl[i].find("id=")
				channelIDlist[i] = xmlurl[i][indexofid+3:]
			get_icons(xmltitle, channelIDlist)

			for i in range(0, len(xmltitle)):  # for every channel
				print(xmltitle[i])

				url_data = urlopen(xmlurl[i], )
				url_data = url_data.read()
				xml = bs(url_data.decode('utf-8'), 'html.parser')

				videoList = xml.find_all('entry')
				#print(xml.find_all('entry'))

				video_download_count = 0
				for v in videoList:     # for every video in channel
					#make sure we only download how many we want
					if video_download_count < NUM_VIDEOS:
						skip_download = False
						video_download_count += 1
						title = v.title.string
						url = v.link.get('href')

						id = v.id.string
						channelID = str(v.find('yt:channelid').contents[0])
						# See if we already downloaded this
						logFile = open(logFileName, 'r')
						logFileContents = logFile.read()
						logFile.close()
						if id in logFileContents:
							print("Video Already downloaded")
						else:
							print("Downloading - " + title + "  |  " + id)
							print("Channel - " + str(xmltitle[i]) + "  |  " + channelID)

							ydl_opts = {
								'outtmpl': 'Download/%(uploader)s - [' + channelID + ']/%(title)s - [%(id)s].%(ext)s',  # need to put channelid in here because what youtube-dl gives may be incorrect
								#'simulate': 'true',
								'writethumbnail': 'true',
								'forcetitle': 'true',
								#'postprocessor_args': [
								#	{'add-metadata': 'true'},
								#],
								'format': '248+251/best'
							}
							#'format:': '140+137',
							#'prefer_ffmpeg': 'true',
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
							#if video_title is not None:  # should be the same but just in case
							#	title = video_title
							#title = ''.join(c for c in title if c in valid_chars)       # make sure all the chars are valid for windows

							#if glob.glob('*' + video_id + '.mp4'):
							#	extension = ".mp4"
							#else:
							#	extension = ".webm"
							#title = glob.glob('*' + video_id + '*')[0]
							#title = title[0:len(title)-5]
							#title = title[0:len(title)-len(video_id)-1]


							#destVideoName = title + " - [" + video_id +"]" + extension
							#destThumbName = title + " - [" + video_id +"].jpg"

							if not skip_download:
								sourceDir = 'Download/' + uploader + ' - [' + channelID + ']/'
								destinationDir = DESTINATION_FOLDER + uploader + ' [Youtube-' + channelID + ']/'

								if not os.path.exists(destinationDir):
									print("Creating Source Directory")
									os.makedirs(destinationDir)
								try:
									print("Moving Folder...")
									#copy_tree(sourceDir, destinationDir)

									#iterate through source and copy each
									for filename in os.listdir(sourceDir):
										safecopy(os.path.join(sourceDir, filename), destinationDir)

									shutil.rmtree(sourceDir, ignore_errors=True)
									#shutil.move(videoName, destination + destVideoName)
									#shutil.move(thumbName, destination + destThumbName)

									#everything was successful so log that we downloaded and moved the video
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
		print("Going to sleep")
		time.sleep(DELAY * 60)


if __name__ == "__main__":
	load_configs(configFile)
	main()
