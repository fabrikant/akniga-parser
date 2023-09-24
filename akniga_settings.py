from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QIntValidator
from pathlib import Path
from akniga_dl import NAMING_DEEP, NAMING_WIDE, NAMING_ID, DOWNLOAD_REQUESTS, DOWNLOAD_FFMPEG
from PyQt5.QtCore import QSettings

settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'akniga', 'akniga_parser', None)

class SettingsDialog(QDialog):

    def __init__(self):
        super(SettingsDialog, self).__init__()
        uic.loadUi(Path(__file__).parent.joinpath('ui').joinpath('settings.ui'), self)

        self.books_download_method.addItem('Запросами к сайту', DOWNLOAD_REQUESTS)
        self.books_download_method.addItem('Программой ffmpeg', DOWNLOAD_FFMPEG)

        self.books_naming_method.addItem('Каталоги: Автор/Серия/Название', NAMING_DEEP)
        self.books_naming_method.addItem('Каталог: Автор-Серия-Название', NAMING_WIDE)
        self.books_naming_method.addItem('Каталог: Идентификатор из адреса страницы', NAMING_ID)

        self.page_start.setValidator(QIntValidator())
        self.page_stop.setValidator(QIntValidator())
        self.read_settings()

    def read_settings(self):

        self.connection_string.setText(settings.value('connection_string', type=str))
        self.page_start.setText(str(settings.value('DatabaseUpdate/start-page', type=int)))
        self.page_stop.setText(str(settings.value('DatabaseUpdate/stop-page', type=int)))
        self.full_scan.setCheckState(settings.value('DatabaseUpdate/full-scan', defaultValue=0, type=int))
        self.update.setCheckState(settings.value('DatabaseUpdate/update', defaultValue=0, type=int))

        self.books_dir.setText(settings.value('DownloadBooks/output', type=str))

        current_data = settings.value('DownloadBooks/download-method', type=str, defaultValue=DOWNLOAD_REQUESTS)
        index = self.books_download_method.findData(current_data)
        if index > -1:
            self.books_download_method.setCurrentIndex(index)

        current_data = settings.value('DownloadBooks/naming', type=str, defaultValue=NAMING_DEEP)
        index = self.books_naming_method.findData(current_data)
        if index > -1:
            self.books_naming_method.setCurrentIndex(index)

        self.app_parser.setText(settings.value('Applications/parser', type=str))
        self.app_downloader.setText(settings.value('Applications/downloader', type=str))


    def write_settings(self):
        settings.setValue('connection_string', self.connection_string.text())

        settings.setValue('DatabaseUpdate/start-page', int(f'0{self.page_start.text()}'))
        settings.setValue('DatabaseUpdate/stop-page', int(f'0{self.page_stop.text()}'))
        settings.setValue('DatabaseUpdate/full-scan', self.full_scan.checkState())
        settings.setValue('DatabaseUpdate/update', self.update.checkState())

        settings.setValue('DownloadBooks/output', self.books_dir.text())
        settings.setValue('DownloadBooks/download-method', self.books_download_method.currentData())
        settings.setValue('DownloadBooks/naming', self.books_naming_method.currentData())

        settings.setValue('Applications/parser', self.app_parser.text())
        settings.setValue('Applications/downloader', self.app_downloader.text())

    def on_books_dir_select(self):
        path = QFileDialog.getExistingDirectory(self, caption='Выбрать каталог')
        self.books_dir.setText(path)

    def on_app_parser_select(self):
        path, _ = QFileDialog.getOpenFileNames(self, caption='akniga_parser')
        self.app_parser.setText(path[0])

    def on_app_downloader_select(self):
        path, _ = QFileDialog.getOpenFileNames(self, caption='akniga_dl')
        self.app_downloader.setText(path[0])
