import logging

from PyQt5.Qt import QAbstractTableModel
from PyQt5.QtCore import Qt, QVariant


class BooksTableModel(QAbstractTableModel):

    def __init__(self, db_books=None, hidden_columns=1):
        QAbstractTableModel.__init__(self, None)
        self.db_books = db_books
        self.db_books_list = self.db_books.all()
        self.visible_columns = len(self.db_books.column_descriptions) - hidden_columns
        self.sort(0, True)

        # pagination
        self.records_on_page = 1000
        self.records_count = len(self.db_books_list)
        self.pages_count = self.records_count // self.records_on_page + 1 \
            if self.records_count % self.records_on_page else 0
        self.page_number = 1 if self.records_count else 0

    def rowCount(self, parent):
        if self.page_number < self.pages_count:
            return self.records_on_page
        else:
            return self.records_count % self.records_on_page

    def columnCount(self, parent):
        return self.visible_columns

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        else:
            cur_row = (self.page_number - 1) * self.records_on_page + index.row()
            return self.db_books_list[cur_row][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.db_books.column_descriptions[col]['name']
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return (self.page_number - 1) * self.records_on_page + col + 1
        else:
            return QVariant()

    def get_description(self, row):
        return self.db_books_list[row][len(self.db_books.column_descriptions) - 1].description

    def get_url(self, row):
        return self.db_books_list[row][len(self.db_books.column_descriptions) - 1].url

    def sort(self, col, order):
        def get_key(row):
            val = row[col]
            if val is None:
                val = ''
            return val
        self.db_books_list.sort(reverse=not order, key=get_key)
        self.layoutChanged.emit()

    def next_page(self):
        if self.page_number < self.pages_count:
            self.page_number += 1
            self.layoutChanged.emit()

    def prev_page(self):
        if self.page_number > 1:
            self.page_number -= 1
            self.layoutChanged.emit()

    def set_page(self, new_page_number):
        if not new_page_number == self.page_number and 0 < new_page_number <= self.pages_count:
            self.page_number = new_page_number
            self.layoutChanged.emit()

    def get_cell_information(self, index):
        return (self.db_books_list[index.row()][index.column()],
                self.db_books.column_descriptions[index.column()]['name'],
                index.row(), index.column())
