import sys
import subprocess
import os
import datetime

def check_dependencies():
    try:
        print("Checking Dependencies....")
        homeDirectory = os.getcwd()
        pythonPath = sys.executable
        print("Python Path: " + pythonPath)
        getPoetryCmd = [pythonPath, os.path.join(homeDirectory, "Automatic-Youtube-Downloader", "poetry", "get_poetry.py"), "--version", "0.12.11"]
        runPoetryCmd = [os.path.join(homeDirectory, "Automatic-Youtube-Downloader", "poetry", "bin", "poetry"), "update"]
        if sys.platform.startswith("win"):
            print('Using Windows System Settings')
            subprocess.run(getPoetryCmd, shell=True, cwd=os.path.join(homeDirectory, "Automatic-Youtube-Downloader"))
            subprocess.run(runPoetryCmd, shell=True, cwd=os.path.join(homeDirectory, "Automatic-Youtube-Downloader"))
        else:
            sys.stdout.flush()
            proc = subprocess.call(getPoetryCmd, cwd=os.path.join(homeDirectory, "Automatic-Youtube-Downloader"))
            if proc > 0:
                print("An error occurred with downloading poetry")
                exit(1)

            sys.stdout.flush()
            proc = subprocess.call(runPoetryCmd, cwd=os.path.join(homeDirectory, "Automatic-Youtube-Downloader"))
            if proc > 0:
                print("An error occurred with running poetry")
                exit(1)
    except Exception as e:
        print(str(e))
        print("An error occurred updating dependencies, try again")
        exit()
    print("Complete.\n")


if __name__ == "__main__":
    print("\nStart")
    now = datetime.datetime.now()
    now.strftime('%m-%d-%y %H:%M:%S')
    check_dependencies()

    pythonPath = sys.executable
    homeDirectory = os.getcwd()
    cmd = [pythonPath, os.path.join(homeDirectory, "Automatic-Youtube-Downloader", "poetry", "bin", "poetry"), "run", "python",
        os.path.join(homeDirectory, "Automatic-Youtube-Downloader", "main.py")]
    if len(sys.argv) > 1:
        for i in range(1, len(sys.argv)):
            cmd.append(sys.argv[i])

    if sys.platform.startswith("win"):
        #print('Using Windows System Settings')
        subprocess.run(cmd, shell=True, cwd=os.path.join(homeDirectory, "Automatic-Youtube-Downloader"))
    else:
        sys.stdout.flush()
        proc = subprocess.call(cmd)
        if proc > 0:
            print("An error occurred with downloading poetry")
            exit(1)
