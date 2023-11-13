from PyQt5.QtWidgets import *
from PyQt5 import uic
from pathlib import Path
from akniga_parser import akniga_url
from akniga_dl import NAMING_ID, DOWNLOAD_REQUESTS, BROWSER_CHROME
from akniga_settings import settings

class DownloadByURLDialog(QDialog):

    def __init__(self, start_process_slot):
        super(DownloadByURLDialog, self).__init__()
        uic.loadUi(Path(__file__).parent.joinpath('ui').joinpath('download_starter.ui'), self)
        # Сюда передается функция для запуска процесса скачивания
        self.start_process_slot = start_process_slot
        self.on_paste_url()

    def on_paste_url(self):
        if akniga_url in qApp.clipboard().text():
            self.url.setText(qApp.clipboard().text())

    def start_download(self):
        url = self.url.text()
        if not url:
            return

        command = ['akniga_dl.py', '--download-method',
                   settings.value('DownloadBooks/download-method', type=str, defaultValue=DOWNLOAD_REQUESTS),
                   '--naming', settings.value('DownloadBooks/naming', type=str, defaultValue=NAMING_ID),
                   '--browser', settings.value('DownloadBooks/browser', type=str, defaultValue=BROWSER_CHROME)]
        output = settings.value('DownloadBooks/output', type=str)
        if output == '':
            output = '.'

        command += [url, output]
        self.start_process_slot(command)
