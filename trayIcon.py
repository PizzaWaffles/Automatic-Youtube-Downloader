import pystray
from PIL import Image
import os
from tendo import singleton

def on_activate(icon, command, conn):
    if command == "quit":
        conn.send(["AYD", "TERMINATE"])
        #print('KILLAYD')

        icon.stop()
        exit(1)
    if command == "restart":
        conn.send(["AYD", "RESTART"])

    if command == "web":
        conn.send(["WEB", "OPENSITE"])



def startTray(conn, args):

    # Create a Tray Icon
    trayIcon = pystray.Icon(
        'Automatic Youtube Downloader',
        icon=Image.open("icon.png"),
        menu=pystray.Menu(
            pystray.MenuItem(
                'Open Webpage',
                lambda icon: on_activate(icon, "web", conn)
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                'Restart AYD',
                lambda icon: on_activate(icon, "restart", conn)
            ),
            pystray.MenuItem(
                'Quit',
                lambda icon: on_activate(icon, "quit", conn)
            )
        )
    )

    trayIcon.run()


#if __name__ == '__main__':
#    start()

