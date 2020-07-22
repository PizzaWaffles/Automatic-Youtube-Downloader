import subprocess
import os
import sys
import threading
import traceback
from multiprocessing import Process, Pipe
import webbrowser
import time

# Local imports
import AYD
import frontend
import trayIcon

statusFile = "logs/programStatus.log"
startedTray = False


def check_dependencies():
    try:
        print("Checking Dependencies....")
        homeDirectory = os.getcwd()
        pythonPath = sys.executable
        print("Python Path: " + pythonPath)
        getPoetryCmd = [pythonPath, os.path.join(homeDirectory, "poetry", "get_poetry.py")]
        runPoetryCmd = [pythonPath, os.path.join(homeDirectory, "poetry", "bin", "poetry"), "update"]
        if sys.platform.startswith("win"):
            print('Using Windows System Settings')
            sys.stdout.flush()
            subprocess.run(getPoetryCmd, shell=True)
            sys.stdout.flush()
            subprocess.run(runPoetryCmd, shell=True)
            sys.stdout.flush()
        else:
            sys.stdout.flush()
            proc = subprocess.call(getPoetryCmd)
            if proc > 0:
                print("An error occurred with downloading poetry")
                exit(1)

            sys.stdout.flush()
            proc = subprocess.call(runPoetryCmd)
            if proc > 0:
                print("An error occurred with running poetry")
                exit(1)
    except Exception as e:
        print(str(e))
        print(traceback.format_exc())
        print("An error occurred updating dependencies, try again")
        exit()
    print("Complete.\n")


class write:
    verbose = False

    def __init__(self, verbose, logF):
        self.verbose = verbose
        self.file = logF
        if not self.verbose:
            print("Running program quietly, use -V flag for verbose, console output will still be stored in logs/")

    def print(self, s):
        self.file.write(s)
        if self.verbose:
            print(s)


class myProcess:
    def __init__(self, procFunction, arguments):
        self._myTarget = procFunction
        self._myArgs = arguments
        self._parent_conn, self._child_conn = Pipe()
        self._p = Process(target=self._myTarget, args=(self._child_conn, self._myArgs))
        self._hasTerminated = False
        self._numDied = 0
        self._diedDate = 0

    def start(self):
        if self._hasTerminated:
            self._parent_conn, self._child_conn = Pipe()
            self._p = Process(target=self._myTarget, args=(self._child_conn, self._myArgs))
            self._p.start()
        elif not self._p.is_alive():
            self._p.start()

    def proc(self):
        return self._p

    def conn(self):
        if not self._p.is_alive() and not self._hasTerminated:
            tempDate = time.strftime("%Y%m%d")
            if self._diedDate is tempDate:
                # More than once today
                self._numDied += 1
                if self._numDied >= 5:
                    print("Process has died more than 5 times today, unable to restart")
                    exit(-1)
            elif self._diedDate is 0:
                # First time since running
                self._diedDate = time.strftime("%Y%m%d")
                self._numDied += 1
            else:
                # Has died in the past but today is a new day
                self._numDied = 1
                self._diedDate = time.strftime("%Y%m%d")


            print("Process has died, trying to restart..")
            self.terminate()
            time.sleep(5)
            self.start()
        return self._parent_conn

    def child_conn(self):
        return self._child_conn

    def terminate(self, force=False):
        if self._p.is_alive() or not force:
            self._hasTerminated = True
            self._parent_conn.close()
            self._child_conn.close()
            self._p.terminate()


def start():
    global startedTray
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    open(statusFile, 'w').close()       # clear status file

    global VERBOSE
    """if not os.path.isfile('poetry.lock'):
        response = input("You need to update your dependencies to continue. Update? (y/n) ")
        if response.strip().lower() == 'y':
            check_dependencies()
        else:
            print("Exiting....")
            exit(1)"""

    # while True:
    # TODO Add taskbar icon and menu
    # if sys.platform.startswith("win"):

    # No console window, daemon
    LogFileName = "logs/MainConsole.log"
    MainLogFile = open(LogFileName, 'w+')


    trayProc = myProcess(trayIcon.startTray, "")
    trayProc.start()
    aydProc = myProcess(AYD.startAyd, sys.argv[1:])
    aydProc.start()
    webProc = myProcess(frontend.startWeb, "")
    webProc.start()

    aydStatus = ""
    webSite = ""

    # Start main loop
    while True:
        if aydProc.conn().poll():
            recv = aydProc.conn().recv()
            print("Received from AYD: " + str(recv))

            if recv[0] == "MAIN":
                aydStatus = recv[1]

        if webProc.conn().poll():
            recv = webProc.conn().recv()
            print("Received from WEB: " + str(recv))

            # recv in format: TO, MESSAGE
            if recv[0] == "AYD":
                if recv[1] == "STATUS":
                    webProc.conn().send(["WEB", aydStatus])
                if recv[1] == "STOP":
                    aydProc.terminate()
                    aydStatus = "Stopped"
                if recv[1] == "START":
                    aydProc.start()
            if recv[0] == "MAIN":
                if "SITE:" in recv[1]:
                    webSite = recv[1].replace("SITE:", "")

        if trayProc.conn().poll():
            recv = trayProc.conn().recv()
            print("Received from TRAY: " + str(recv))

            if recv[1] == "TERMINATE":
                aydProc.terminate()
                webProc.terminate()
                trayProc.terminate()
                exit(1)

            if recv[0] == "WEB":
                if recv[1] == "OPENSITE":
                    # may have to thread
                    webbrowser.open(webSite)
                if recv[1] == "RESTART":
                    aydProc.terminate()
                    aydProc.start()

if __name__ == "__main__":
    VERBOSE = False
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    mainThread = threading.Thread(target=start)
    mainThread.name = "Main Thread"
    try:
        mainThread.start()
        mainThread.join()
        #start()
    except Exception as e:
        print(traceback.format_exc())
        print(e)
    print("Fully Exited Program...")
    sys.exit(1)
