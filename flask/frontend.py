from flask import Flask, render_template, request
import youtube_dl
import os
import subprocess
from subprocess import *
import sys

# creates a Flask application, named app
from tendo import singleton

app = Flask(__name__)


# a route where we will display a welcome message via an HTML template
@app.route("/")
@app.route("/index.html")
def hello():
    message = "Running"

    print("15894")
    message = sys.stdin.readline()

    #print(message)
    return render_template('index.html', downloader_status=message)


@app.route('/start/')
def downloaderStart():  # TODO Add program start
    print("15853")
    message = sys.stdin.readline()
    print("DAN:" + message)
    return '', 204


@app.route('/stop/')
def downloaderStop():  # TODO Add program stop
    print("15842")
    message = sys.stdin.readline()
    print("DAN:" + message)
    return '', 204


@app.route('/downloaderList')
def downloaderList():
    #data from js function in browser
    text = request.args.get('jsdata')

    f = open('../data/log.txt')
    fileLines = f.readlines()
    fileLines.reverse()
    logList = fileLines[0:20]
    f.close()
    validEntrees = 0

    for i in range(0, len(logList)):
        id = logList[i].split(":")[2].strip()
        [nID, name, title, quality, data, imagePath] = getVideoInfo(id)

        if nID == "Empty":
            logList = logList[0:validEntrees]
            break
        logList[i] = "<tr><td>" + name + "</td><td>" + title + '</td><td>' + id + '</td></tr>'
        validEntrees += 1

    return render_template('downloaderList.html', logList=logList)


# Returns a list in this order: ID, Channel Name, Title, Quality, Date, ImagePath
def getVideoInfo(videoID):
    with open('../data/fullDataLog.txt', 'r') as f:
        lines = f.readlines()
        # ID, Channel Name, Title, Quality, Date, ImagePath
        for line in lines:
            info = line.split('?')
            if info[0] == videoID:
                return info
    return ["Empty", "Empty", "Empty", "Empty", "Empty", "Empty"]


# run the application
if __name__ == "__main__":
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    print("Current Working Directory:" + os.getcwd() + '\n')
    # check if another instance is running
    me = singleton.SingleInstance()  # will sys.exit(-1) if other instance is running
    app.run()
