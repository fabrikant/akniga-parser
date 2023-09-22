from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import QProcess, QProcessEnvironment
from PyQt5.QtGui import QTextCursor
from pathlib import Path

class ConsoleTabItem(QWidget):

    def __init__(self, parent, command, str_command):
        super().__init__(parent)
        uic.loadUi(Path(__file__).parent.joinpath('ui').joinpath('console_item.ui'), self)
        self.str_command = str_command
        system_env = QProcessEnvironment.systemEnvironment()
        self.process = QProcess()
        self.process.setProcessEnvironment(system_env)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_finished)

        command_path = command[0]
        if command_path.is_file():
            programm = str(command_path)
            arguments = command[1:]
        elif command_path.with_suffix('.exe').is_file():
            programm = str(command_path.with_suffix('.exe'))
            arguments = command[1:]
        elif command_path.with_suffix('.py').is_file():
            programm = 'python'
            arguments = [str(command_path.with_suffix('.py'))] + command[1:]
        else:
            programm = 'echo'
            arguments = [f'Не найден исполняемый файл {str(command_path)}']

        print(programm)
        print(arguments)
        try:
            self.process.start(programm, arguments)
        except Exception as error:
            self.console_text.append(f"{error}")

    def print_message(self, data):
        stdout = bytes(data).decode("utf8")
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
        # Сюда передается док, который нужно закрывать, когда больше нет закладок
        self.console_dock = None

    def start_process(self, command):

        index = self.find_item_by_command(command)
        if index is None:
            tab_text = str(command[0])
            if 'akniga_parser' in tab_text:
                tab_text = 'db update'
            elif 'akniga_dl' in tab_text:
                tab_text = command[-2].strip('/').split('/')[-1]
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
        self.removeTab(index)
        item = self.widget(index)
        if item:
            item.stop_process()
            item.close()
        if not self.console_dock is None:
            if not self.count():
                self.console_dock.close()
