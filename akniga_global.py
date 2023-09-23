from PyQt5.QtCore import QSettings

settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'akniga', 'akniga_parser', None)

NAMING_DEEP = 'deep'
NAMING_WIDE = 'wide'
NAMING_ID = 'id'
DOWNLOAD_REQUESTS = 'requests'
DOWNLOAD_FFMPEG = 'ffmpeg'



def request_heders():
    return {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 '
                         'Safari/537.36'}

