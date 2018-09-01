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


# support for python 3 and 2
if sys.version_info[0] == 3:
	from urllib.request import urlopen
	from urllib import request
else:
	from urllib import urlopen
	import urllib as request

DEBUGLOGGING = True
configFile = "data/config"

def logPrint(string):
	if DEBUGLOGGING:
		print("DEBUGMSG:" + str(string))


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
			print("Checking " + package)
			if pipmain(['install', package]):
				raise Exception
			#print(subprocess.check_call([sys.executable, '-m', 'pip', 'install', package]))
		#if platform == 'windows':
		#	install(windows)
		if platform.startswith('linux'):
			for package in linux:
				print("Checking " + package)
				if pipmain(['install', package]):
					raise Exception
				#print(subprocess.check_call([sys.executable, '-m', 'pip', 'install', package]))
		#if platform == 'darwin':  # MacOS
		#	install(darwin)
	except Exception as e:
		logPrint("ERROR:\n" + str(e))
		logPrint(traceback.format_exc())
		print("One or more dependencies not met!! Please run 'pip install -r requirements.txt'")
		exit()
	print("Complete.")


def setup_youtube():
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
			setup_not_complete = False
		else:
			print("File Not Found!! Please make sure you have it in th correct directory and its named correctly")
			logPrint("data folder contents:\n" + str(glob.glob("data/*")))

	setup_not_complete = True
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
			setup_not_complete = False
			return api_key
		except Exception as e:
			logPrint("\n\nERROR\n" + str(e))
			logPrint(traceback.format_exc())
			print("Sorry that key did not work!!! Make sure you copied the key correctly")

	return api_key  # shouldn't reach this but just in case


def channel_selection():
	import listparser as lp
	# This function parses OPML data and allows the user to select which channels to be included
	print("\n\n\nParsing Youtube data.....")
	all_channels = False
	loop = True
	while loop:
		selection = get_input(
			"Would you like to select which channels you want to include, or do you want to include all of them?\n"
			"If you include all channels you can remove them manually by editing data/youtubeData.xml and deleting the"
			" entire line of the channel you do not want (Choose this option if you have a lot of subscriptions)\n"
			"Enter 'all' to keep all subscriptions or 'select' to select which channels (or 'a' or 's'):").lower()
		if selection == 'all' or selection == 'a':
			all_channels = True
			loop = False
			print("Including all channels")
		elif selection == 'select' or selection == 's':
			all_channels = False
			loop = False
			print(
				"You will now be asked to select which channels you would like to include in your download library. \nAny"
				" channels you do not include will be ignored. \nWarning: if you add a new subscription you must go through this"
				" process again (until I add a feature to import a channel)\n")
		else:
			print("Invalid Selection!!! Try again.")

	file = open("data/youtubeData.xml", 'w')
	d = lp.parse('data/subscription_manager.xml')
	l = d.feeds
	file.write('<opml version="1.1">\n<body>\n')
	num_channels = len(l)
	human_count = 1

	for channel in l:
		title = bytes(channel.title, 'utf-8').decode('utf-8','ignore')
		url = bytes(channel.url, 'utf-8').decode('utf-8','ignore').encode("utf-8")
		print("\nVideo " + str(human_count) + "/" + str(num_channels))
		# logPrint(title)
		logPrint(url)

		print(title)
		if not all_channels:
			loop = True
			while loop:
				selection = get_input(
					"Select if you want to include the channel above, select 'yes' or 'no' (or 'y' or 'n'):").lower()
				if selection == 'y' or selection == 'yes':
					file.write('<outline title="' + title + '" xmlUrl="' + url + '"/>\n')
					print(title + " will be included!!")
					loop = False
				elif selection == 'n' or selection == 'no':
					loop = False
					print(title + " will NOT be included!!")
				else:
					print("Invalid response. Tray again.")
		else:
			file.write('<outline title="' + title + '" xmlUrl="' + url + '"/>\n')
		human_count += 1

	file.write('</body>\n</opml>')
	file.close()
	print("\nComplete.")


def setup_config(api_key):
	print("\n\n\nSetting up Config file")
	with open(configFile, 'w') as f:
		f.write("API_KEY=" + api_key + "\n")

		loop = True
		while loop:
			selection = get_input("""
	\nHow would you like the program to run? (x being any number you want)
		1. Every x minutes
		2. Every day at x time\n""")
			if selection == '1':
				delay_time = get_input("Please enter a number in minutes:")
				if delay_time.isdigit():
					print("\nSuccess! It will run every " + delay_time + " minutes")
					f.write("START_TIME=\n")
					f.write("DELAY=" + delay_time + '\n')
					loop = False
				else:
					print("\nInvalid response!!! Try again.")
			elif selection == '2':
				start_time = get_input("Please enter a number in hours:")
				if start_time.isdigit():
					print("\nSuccess! It will run at " + start_time + " everyday!")
					f.write("START_TIME=" + start_time + '\n')
					f.write("DELAY=0\n")
					loop = False
				else:
					print("\nInvalid response!!! Try again.")
			else:
				print("\nInvalid!!! Please try again.")

		loop = True
		while(loop):
			response = get_input("\nHow many videos for each channel do you want to download? (max 15)")
			if response.isdigit():
				f.write("NUM_VIDEOS=" + response + '\n')
				loop = False
			else:
				print("\nInvalid!!! Please try again.")

		loop = True
		while (loop):
			response = get_input("\nWhere would you like your videos moved? (Usually a Plex library)\n"
			                     "Make sure you enter the entire address (ex. 'G:\\Plex\\Youtube\\\n')")

			try:
				if not os.path.isdir(response): # either not a valid directory or not created
					# try making a directory and see if it throws an exception
					print("Creating Source Directory")
					response = os.path.join(response, '')      # add a trailing backslash if not already there
					os.makedirs(response)
					f.write("DESTINATION_FOLDER=" + response + '\n')   # if it gets this far we are good
					print('\nSuccess!')
					loop = False
				else:
					print("Found Source Directory")
					response = os.path.join(response, '')
					f.write("DESTINATION_FOLDER=" + response + '\n')
					print('\nSuccess!')
					loop = False
			except Exception as e:
				logPrint(str(e))
				print("\nInvalid!!! Please try again.")


def main():
	if not os.path.exists('data/'):
		os.makedirs('data/')
	if not os.path.exists('Download/'):
		os.makedirs('Download/')
	if not os.path.isfile('data/log.txt'):
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
			exit()
		else:
			print("\n Not Valid Choice Try again")


if __name__ == "__main__":
	main()
	# print(setup_youtube())
	#channel_selection()
	#setup_config("123")
