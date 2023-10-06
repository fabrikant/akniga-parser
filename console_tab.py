from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import QProcess, QProcessEnvironment
from PyQt5.QtGui import QTextCursor
from pathlib import Path
import PyQt5
import os

class ConsoleTabItem(QWidget):

    def __init__(self, parent, command, str_command):
        super().__init__(parent)
        self.setAttribute(PyQt5.QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        uic.loadUi(Path(__file__).parent.joinpath('ui').joinpath('console_item.ui'), self)
        self.str_command = str_command
        self.process = QProcess()
        # self.process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_finished)
        command = ['python']+command
        try:
            self.process.start(command[0], command[1:])
        except Exception as error:
            self.console_text.append(f"{error}")

    def print_message(self, data):
        if 'nt' in os.name:
            os_code = 'CP1251'
        else:
            os_code = 'utf-8'
        stdout = bytes(data).decode(os_code, errors='replace')
        if not "" == stdout:
            self.console_text.moveCursor(QTextCursor.End)
            self.console_text.insertPlainText(stdout)
            self.console_text.moveCursor(QTextCursor.End)

    def on_stdout(self):
        self.print_message(self.process.readAllStandardOutput())

    def on_stderr(self):
        self.print_message(self.process.readAllStandardError())

    def on_finished(self):
        self.console_text.append(f'Процесс завершен с кодом: {self.process.exitCode()}')
        self.console_text.moveCursor(QTextCursor.End)

    def stop_process(self):
        if not self.process is None:
            if not self.process.finished:
                self.process.kill()


class ConsoleTab(QTabWidget):

    def __init__(self, parent):
        super().__init__(parent)

    def start_process(self, command, type_command=None):

        index = self.find_item_by_command(command)
        if index is None:
            if type_command is None:
                tab_text = command[-2].strip('/').split('/')[-1]
            else:
                tab_text = type_command
            self.setCurrentIndex(self.addTab(ConsoleTabItem(self, command, self.command_to_str(command)), tab_text))
        else:
            self.setCurrentIndex(index)

    def command_to_str(self, command):
        return f'{command[0]} {"".join(command[1:])}'

    def find_item_by_command(self, command):
        str_command = self.command_to_str(command)
        for index in range(self.count()):
            item = self.widget(index)
            if item.str_command == str_command:
                return index
        return None

    def on_close_tab_request(self, index):
        item = self.widget(index)
        if item:
            item.stop_process()
            item.close()
        self.removeTab(index)
