from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSettings
from PyQt5 import uic
from PyQt5.QtGui import QIntValidator
from akniga_global import config_file_name, NAMING_DEEP, NAMING_WIDE, NAMING_ID, DOWNLOAD_REQUESTS, DOWNLOAD_FFMPEG

class SettingsDialog(QDialog):

    def __init__(self):
        super(SettingsDialog, self).__init__()
        uic.loadUi('ui/settings.ui', self)

        self.books_download_method.addItem(DOWNLOAD_REQUESTS)
        self.books_download_method.addItem(DOWNLOAD_FFMPEG)

        self.books_naming_method.addItem(NAMING_DEEP)
        self.books_naming_method.addItem(NAMING_WIDE)
        self.books_naming_method.addItem(NAMING_ID)

        self.page_start.setValidator(QIntValidator())
        self.page_stop.setValidator(QIntValidator())
        self.read_settings()

    def read_settings(self):
        settings = QSettings(config_file_name, QSettings.IniFormat)

        self.connection_string.setText(settings.value('connection_string', type=str))
        self.page_start.setText(str(settings.value('DatabaseUpdate/start-page', type=int)))
        self.page_stop.setText(str(settings.value('DatabaseUpdate/stop-page', type=int)))
        self.full_scan.setCheckState(settings.value('DatabaseUpdate/full-scan', defaultValue=0, type=int))
        self.update.setCheckState(settings.value('DatabaseUpdate/update', defaultValue=0, type=int))
        self.genres.setCheckState(settings.value('DatabaseUpdate/genres', defaultValue=2, type=int))

        self.books_dir.setText(settings.value('DownloadBooks/output', type=str))
        self.books_download_method.setCurrentText(settings.value('DownloadBooks/download-method', type=str,
                                                                 defaultValue=DOWNLOAD_REQUESTS))

        self.books_naming_method.setCurrentText(settings.value('DownloadBooks/naming', type=str,
                                                                 defaultValue=NAMING_DEEP))

    def write_settings(self):
        settings = QSettings(config_file_name, QSettings.IniFormat)
        settings.setValue('connection_string', self.connection_string.text())

        settings.setValue('DatabaseUpdate/start-page', int(f'0{self.page_start.text()}'))
        settings.setValue('DatabaseUpdate/stop-page', int(f'0{self.page_stop.text()}'))
        settings.setValue('DatabaseUpdate/full-scan', self.full_scan.checkState())
        settings.setValue('DatabaseUpdate/update', self.update.checkState())
        settings.setValue('DatabaseUpdate/genres', self.genres.checkState())

        settings.setValue('DownloadBooks/output', self.books_dir.text())
        settings.setValue('DownloadBooks/download-method', self.books_download_method.currentText())

        settings.setValue('DownloadBooks/naming', self.books_naming_method.currentText())

    def on_books_dir_select(self):
        path = QFileDialog.getExistingDirectory(self, caption='Выбрать каталог')
        self.books_dir.setText(path)
