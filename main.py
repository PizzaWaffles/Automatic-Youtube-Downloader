import subprocess
import os
import sys
from threading import Thread
import threading
from queue import Queue, Empty
import traceback
import time
import signal


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


def queueOutput(out, queue, id):
    for line in iter(out.readline, b''):
        queue.put((id + ":").encode() + line)
    out.close()



def checkQueue(q):
    #if not qLock.acquire(False):
    try:
        #line = q.get_nowait()  # or q.get(timeout=.1)
        line = q.get(timeout=.1)
    except Empty:
        return 0
    else:  # got line
        #qLock.release()
        return line


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


class myThread(threading.Thread):
    def __init__(self, workQueue, workqueueLock, stdoutQueue, cmd, nID):
        super(myThread, self).__init__()
        self.workQueue = workQueue
        self.myQueue = Queue()
        self.workQueueLock = workqueueLock
        self.stdoutQueue = stdoutQueue
        self.proc = ''
        self.cmd = cmd
        self.id = nID

        ON_POSIX = 'posix' in sys.builtin_module_names
        self.proc = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                    bufsize=1, close_fds=ON_POSIX)
        stdoutThread = Thread(target=queueOutput, args=(self.proc.stdout, self.stdoutQueue, self.id))
        stdoutThread.daemon = True
        stdoutThread.name = "STDOUT " + self.id + " Thread"
        stdoutThread.start()

    def get_proc(self):
        return self.proc

    def sendData(self, string):
        self.proc.stdin.write(string.encode())
        self.proc.stdin.flush()

    def run(self):
        data = ''
        while 1:
            # read program stdout
            '''if not self.myQueue.empty():
                data = self.myQueue.get()
                workQueue(str(id) + ":" + str(data))'''
            time.sleep(.1)
            if not self.workQueueLock.acquire(False):
                # see if we have any task from parent
                if not self.workQueue.empty():
                    data = self.workQueue.get()
                    data = data.decode(sys.stdout.encoding).strip()
                    if data.split(':')[0] == self.id:
                        print("Got data for me:" + self.id)
                        print(data)
                    else:
                        self.workQueue.put(data.encode())
                self.workQueueLock.release()

            if data == self.id + ':quit':
                print("Teminating " + self.id)
                os.kill(self.proc.pid, signal.SIGILL)
                return 1
            if self.proc.poll() is not None:
                print("Program had died terminating thread.")
                return 1

        #print(str(id) + ":" + str(self.proc.stderr))
        #print(str(id) + ":" + str(self.proc.returncode))


def start():
    global VERBOSE
    if not os.path.isfile('poetry.lock'):
        response = input("You need to update your dependencies to continue. Update? (y/n) ")
        if response.strip().lower() == 'y':
            check_dependencies()
        else:
            print("Exiting....")
            exit(1)

    pythonPath = sys.executable
    aydCmd = [pythonPath, os.path.join("./poetry", "bin", "poetry"), "run", "python", "AYD.py"]
    webCmd = [pythonPath, os.path.join("./poetry", "bin", "poetry"), "run", "python",
        os.path.join("./flask", "frontend.py")]
    trayCmd = [pythonPath, os.path.join("./poetry", "bin", "poetry"), "run", "python", "trayIcon.py"]

    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            if sys.argv[i] == '-V':
                VERBOSE = True
            aydCmd.append(sys.argv[i])

    # while True:
    # TODO Add taskbar icon and menu
    # if sys.platform.startswith("win"):

    from tendo import singleton
    # check if another instance is running
    me = singleton.SingleInstance()  # will sys.exit(-1) if other instance is running

    # No console window, daemon
    LogFileName = "logs/MainConsole.log"
    MainLogFile = open(LogFileName, 'w+')

    w = write(VERBOSE, MainLogFile)

    workQueue = Queue()
    workQueueLock = threading.Lock()
    aydQueue = Queue()
    webQueue = Queue()
    trayQueue = Queue()

    #inputQueueLock = threading.Lock()

    w.print("Starting Automatic Youtube Downloader daemon...")
    # aydThread, aydQueue, aydProc = startThread(aydCmd)
    aydThread = myThread(workQueue, workQueueLock, aydQueue, aydCmd, "AYD")
    aydThread.setDaemon(True)
    aydThread.name = "AYD Thread"
    aydThread.start()
    w.print("Complete.")

    w.print("Starting WebUI...")
    # webThread, webQueue, webProc = startThread(webCmd)
    webThread = myThread(workQueue, workQueueLock, webQueue, webCmd, "WEB")
    webThread.setDaemon(True)
    webThread.name = "WEBUI Thread"
    webThread.start()
    w.print("Complete.")

    w.print("Starting TrayIcon...")
    # trayThread, trayQueue, trayProc = startThread(trayCmd)
    trayThread = myThread(workQueue, workQueueLock, trayQueue, trayCmd, "TRAY")
    trayThread.setDaemon(True)
    trayThread.name = "TRAY Thread"
    trayThread.start()
    w.print("Complete.")

    # Start main loop
    while True:
        #w.print("Checking queue....")
        ret = checkQueue(aydQueue)
        if ret != 0 and ret is not None:
            ret = ret.decode(sys.stdout.encoding).strip()
            w.print(ret)

            if ret.split(':')[1] == "KILLAYD":
                while 1:
                    if not workQueueLock.acquire(False):  # aquire returns false if queue is locked
                        workQueue.put(b'AYD:quit')
                        workQueueLock.release()
                        break

            if ret.split(':')[1] == "AYDSTATUS":
                while 1:
                    if not workQueueLock.acquire(False):  # aquire returns false if queue is locked
                        if aydThread.isAlive():
                            webThread.sendData('Running\n')
                            break
                        else:
                            webThread.sendData('Not Running\n')
                            break
        ret = checkQueue(webQueue)
        if ret != 0 and ret is not None:
            ret = ret.decode(sys.stdout.encoding).strip()
            w.print(ret)

            if ret.split(':')[1] == "KILLAYD":
                while 1:
                    if not workQueueLock.acquire(False):  # aquire returns false if queue is locked
                        workQueue.put(b'AYD:quit')
                        workQueueLock.release()
                        break

            if ret.split(':')[1] == "AYDSTATUS":
                while 1:
                    if not workQueueLock.acquire(False):  # aquire returns false if queue is locked
                        if aydThread.isAlive():
                            webThread.sendData('Running\n')
                            break
                        else:
                            webThread.sendData('Not Running\n')
                            break
        ret = checkQueue(trayQueue)
        if ret != 0 and ret is not None:
            ret = ret.decode(sys.stdout.encoding).strip()
            w.print(ret)

            if ret.split(':')[1] == "KILLAYD":
                while 1:
                    if not workQueueLock.acquire(False):  # aquire returns false if queue is locked
                        workQueue.put(b'AYD:quit')
                        workQueueLock.release()
                        break

            if ret.split(':')[1] == "AYDSTATUS":
                while 1:
                    if not workQueueLock.acquire(False):  # aquire returns false if queue is locked
                        if aydThread.isAlive():
                            webThread.sendData('Running\n')
                            break
                        else:
                            webThread.sendData('Not Running\n')
                            break


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
    except Exception as e:
        print(traceback.traceback.format_exc())
        print(e)
    print("Why am i here")
    sys.exit(1)
