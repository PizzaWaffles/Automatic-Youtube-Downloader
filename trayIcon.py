import pystray
from PIL import Image


def on_activate(icon, quit):
    if quit:
        print('KILLAYD')
        icon.stop()
        #exit(1)
    else:
        print('doing nothing...')

# Create a Tray Icon
trayIcon = pystray.Icon(
    'Automatic Youtube Downloader',
    icon=Image.open("icon.png"),
    menu=pystray.Menu(
        pystray.MenuItem(
            'Print',
            lambda icon: on_activate(icon, False)
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            'Quit',
            lambda icon: on_activate(icon, True)
        )
    )
)

trayIcon.run()
