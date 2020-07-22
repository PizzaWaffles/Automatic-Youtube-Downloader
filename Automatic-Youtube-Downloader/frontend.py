from flask import Flask, render_template, request, redirect
import os
import time
from multiprocessing import Process, Pipe
import listparser
#import flask_login
#import flask_loginmanager
#from flask_loginmanager import LoginManager


abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

#login_manager = LoginManager()
app = Flask(__name__, template_folder='flask/templates', static_folder='flask/static')
#login_manager.init_app(app)

statusFile = "logs/programStatus.log"

webHost = '127.0.0.1'
webPort = '5000'

tempChannelHtmlID = []
tempChannelID = []
tempChannelTitle = []

"""@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = flask_login.LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('index'))
    return flask.render_template('login.html', form=form)"""

@app.route("/")
@app.route("/index.html")
def home():
    if CONN is not None:
        CONN.send(["AYD", "STATUS"])
    aydStatus = readData(5)

    print(aydStatus)
    return render_template('index.html', downloader_status=aydStatus)


@app.route("/config")
def config():
    return render_template('config.html')


@app.route("/channels")
def channels():
    return render_template('channels.html')


@app.route("/handleChannels", methods=['POST'])
def channelsHandler():
    global tempChannelHtmlID
    global tempChannelID
    global tempChannelTitle
    data = request.form

    for item in data:
        if "Delete_" in item:
            print("Deleting Channel")
            channelID = item.split("_")[1]

            # delete item that is not in youtubeData yet
            if len(channelID) == 1:
                htmlID = item.replace("Delete_", "")
                for i in range(0, len(tempChannelHtmlID)):
                    if tempChannelHtmlID[i] == htmlID:
                        tempChannelHtmlID[i] = ""
                        tempChannelID[i] = ""
                        tempChannelTitle[i] = ""
            else:
                with open("data/youtubeData.xml", "r") as f:
                    originalData = f.readlines()
                with open("data/youtubeData.xml", "w") as f:
                    for originalLine in originalData:
                        if channelID not in originalLine:
                            f.write(originalLine)

                break

    if 'action' in data:
        if "Save" in data['action']:
            print("Saving new values")
            dataDict = dict(data)
            del dataDict["action"]

            with open("data/youtubeData.xml", "r") as f:
                originalData = f.readlines()
            with open("data/youtubeData.xml", "w") as f:
                f.write('<opml version="1.1">\n<body>\n')
                for key, values in sorted(dataDict.items()):
                    if values[0] is not "" or values[1] is not "":
                        f.write('<outline title="' + str(values[0]) +
                                '" xmlUrl="https://www.youtube.com/feeds/videos.xml?channel_id=' +
                                str(values[1]) + '"/>\n')
                f.write('</body>\n</opml>')
                tempChannelHtmlID = []
                tempChannelTitle = []
                tempChannelID = []

        if "Add" in data['action']:
            count = 0
            dataDict = dict(data)
            del dataDict["action"]
            for key, values in sorted(dataDict.items()):
                count += 1
                if "t_" in key:
                    for idx in range(0, len(tempChannelHtmlID)):
                        if tempChannelHtmlID[idx] == key:
                            tempChannelTitle[idx] = values[0]
                            tempChannelID[idx] = values[1]
            tempChannelHtmlID.append("t_" + str(count))
            tempChannelTitle.append("")
            tempChannelID.append("")
            #tempChannels.append(["t_" + str(count), "", ""])

        if "Reset" in data['action']:
            tempChannelHtmlID = []
            tempChannelTitle = []
            tempChannelID = []


    print("GOT:" + str(data))
    return redirect("/channels", code=302)


@app.route("/handleConfig", methods=['POST'])
def configHandler():
    data = request.form

    if 'action' in data:
        if "Save" in data['action']:
            print("Saving new values")
            dataDict = dict(data)
            del dataDict["action"]
            # TODO dave to config file

    print("GOT:" + str(dataDict))
    return redirect("/config", code=302)


@app.route('/getYoutubeChannels/')
def youtubeChannels():
    global tempChannelHtmlID
    global tempChannelTitle
    global tempChannelID
    htmlChannels = []

    data = listparser.parse('data/youtubeData.xml')
    idx = 0
    #try:
    for i in range(0, len(data.feeds)):
        title = data.feeds[i].title  # channel Title
        xmlurl = data.feeds[i].url  # formatted like 'https://www.youtube.com/feeds/videos.xml?channel_id=CHANNELID'
        indexofid = xmlurl.find("id=")
        channelID = xmlurl[indexofid + 3:]

        #html = '<div class="col-4 col-12-xsmall">'
        htmlChannels.append('<input type="text" name="' + str(idx) + '" id="' + title + '" value="' + title + '" />')
        htmlChannels.append('<input type="text" name="' + str(idx) + '" id="' + channelID + '" value="' + channelID + '" />')
        htmlChannels.append('<input type="submit" name="Delete_' + channelID + '" value="Delete" class="primary" id="' + channelID + '" />')
        idx += 1

    for i in range(0, len(tempChannelHtmlID)):
        if tempChannelHtmlID[i] is not "":
            htmlChannels.append('<input type="text" name="' + str(tempChannelHtmlID[i]) + '" id="' + str(tempChannelTitle[i]) + '" value="' + str(tempChannelTitle[i]) + '" />')
            htmlChannels.append('<input type="text" name="' + str(tempChannelHtmlID[i]) + '" id="' + str(tempChannelID[i]) + '" value="' + str(tempChannelID[i]) + '" />')
            htmlChannels.append('<input type="submit" name="Delete_' + str(tempChannelHtmlID[i]) + '" value="Delete" class="primary" id="' + str(tempChannelID[i]) + '" />')
            #htmlChannels.append('<a href="#" class="icon brands fa-save"><span class="label">Not Saved</span></a>')

    #except Exception as e:
    #    print("Error reading 'data/youtubeData.xml':" + str(e))
    #    htmlChannels = ["Error 'data/youtubeData.xml' is malformed"]

    return render_template('channelsTable.html', dataList=htmlChannels)


@app.route("/logs")
def logs():

    return ""

@app.route('/statusLabel/')
def statusLabel():
    if CONN is not None:
        CONN.send(["AYD", "STATUS"])
    aydStatus = readData(5)

    print(aydStatus)
    return render_template('statusLabel.html', downloader_status=aydStatus)


@app.route('/start/')
def downloaderStart():  # TODO Add program start
    if CONN is not None:
        CONN.send(["AYD", "START"])
    return '', 204


@app.route('/stop/')
def downloaderStop():  # TODO Add program stop
    if CONN is not None:
        CONN.send(["AYD", "STOP"])
    return '', 204

# <input type="text" name="name" id="name" value="" placeholder="Name" />
# <label for="human">I am a human and not a robot</label>
@app.route('/configTable/')
def configTable():
    f = open('data/config')
    fileLines = f.readlines()
    f.close()

    htmlConfig = []
    try:
        for i in range(0, len(fileLines)):
            id = fileLines[i].split("=")[0].strip()
            data = fileLines[i].split("=")[1].strip()

            # Build input tag
            html = '<label for="' + id + '">' + id + '</label>\n'\
            # TODO add dropdowns to SCHMODE, VIDEOFORMAT
            html += '<input type="text" name="' + id + '" id="' + id + '" value="' + data + '" />'
            htmlConfig.append(html)
    except:
        htmlConfig = "Error 'data/config' is malformed"

    return render_template('configTable.html', configList=htmlConfig)



@app.route('/downloaderList/')
def downloaderList():
    #data from js function in browser
    text = request.args.get('jsdata')

    f = open('data/log.txt')
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
    with open('data/fullDataLog.txt', 'r') as f:
        lines = f.readlines()
        # ID, Channel Name, Title, Quality, Date, ImagePath
        for line in lines:
            info = line.split('?')
            if info[0] == videoID:
                return info
    return ["Empty", "Empty", "Empty", "Empty", "Empty", "Empty"]


def readData(timeout):
    if CONN is not None:
        for i in range(0, timeout):
            if CONN.poll():
                results = CONN.recv()
                if results[0] == "WEB":
                    return results[1]
            time.sleep(1)

    return "No connection"


class youtubeData:
    def __init__(self):
        self.htmlKey


def startWeb(conn, args):
    global CONN
    print("Current Working Directory:" + os.getcwd() + '\n')
    # check if another instance is running
    # me = singleton.SingleInstance()  # will sys.exit(-1) if other instance is running

    CONN = conn
    if CONN is not None:
        CONN.send(["MAIN", "SITE:http://" + webHost + ":" + webPort])

    app.run(debug=False, host=webHost, port=webPort)


# run the application
if __name__ == "__main__":
    startWeb(None, "")
