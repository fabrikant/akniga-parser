from PyQt5.QtWidgets import *
from table_model import BooksTableModel
from PyQt5.QtGui import QIntValidator
import webbrowser
from akniga_dl import NAMING_ID, DOWNLOAD_REQUESTS, BROWSER_CHROME
from akniga_settings import settings

class TableBooks(QTableView):

    def __init__(self, parent):
        super().__init__(parent)
        # Сюда передается функция для запуска процесса скачивания
        self.start_process_slot = None

    def on_get_data(self, db_books, main_window, clipboard):

        self.clipboard = clipboard
        table_model = BooksTableModel(db_books)

        # Подключение событий по выделению ячеек для показа описани книги
        self.setModel(table_model)
        table_model.layoutChanged.connect(main_window.on_book_layout_changed_selected)
        selection_model = self.selectionModel()
        selection_model.selectionChanged.connect(main_window.on_book_layout_changed_selected)

        # Размер ячеек
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.set_columns_width(350)

        # Панель страниц
        main_window.page_count.setText(f'из {table_model.pages_count}')
        main_window.record_count.setText(f'Всего записей: {table_model.records_count}')
        main_window.page_current.setText(f'{table_model.page_number}')
        main_window.page_current.setValidator(QIntValidator(1, table_model.pages_count))

    def get_current_url(self):
        url = None
        sel_list = self.selectionModel().selectedIndexes()
        if len(sel_list):
            url = self.model().get_url(sel_list[0].row())
        return url

    def open_url(self):
        url = self.get_current_url()
        if url:
            webbrowser.open(url)

    def copy_url(self):
        url = self.get_current_url()
        if url:
            self.clipboard.setText(url)

    def download_book(self):
        url = self.get_current_url()
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

    def set_columns_width(self, max_width):
        for num_col in range(self.model().columnCount(None)):
            width = max_width if self.columnWidth(num_col) > max_width else self.columnWidth(num_col)
            self.setColumnWidth(num_col, width)
