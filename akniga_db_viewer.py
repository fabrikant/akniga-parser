import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore, QtGui
from PyQt5.Qt import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import akniga_sql as sql


class FilterItem(QStandardItem):
    def __init__(self, db_object=None, checkable=False):
        super().__init__()
        self.db_object = db_object
        self.setText(db_object.name)
        self.setCheckable(checkable)
        self.setEditable(False)


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui/main.ui', self)
        self.books_constraints = set()

    def on_start_connecting(self):
        self.session = sql.get_session('sqlite:///akniga.db')
        treeView = self.filtersTree
        treeView.setHeaderHidden(True)
        treeModel = QStandardItemModel()
        treeModel.itemChanged.connect(self.on_filter_check_uncheck)

        rootNode = treeModel.invisibleRootItem()

        for db_filter_type in self.session.query(sql.FilterType).order_by(sql.FilterType.name).all():
            item = FilterItem(db_filter_type, False)
            rootNode.appendRow(item)
            self.create_filter_items(self.session, item, db_filter_type.id, None)

        treeView.setModel(treeModel)
        # treeView.expandAll()
        self.get_data()

    def on_filter_check_uncheck(self, checked_item):
        tree = self.filtersTree
        self.books_constraints = set()

        def iter_items(root):
            def recurse(parent):
                for row in range(parent.rowCount()):
                    child = parent.child(row, 0)
                    yield child
                    if child.hasChildren():
                        yield from recurse(child)
                    # for column in range(parent.columnCount()):
                    #     child = parent.child(row, column)
                    #     yield child
                    #     if child.hasChildren():
                    #         yield from recurse(child)

            if root is not None:
                yield from recurse(root)

        for item in iter_items(tree.model().invisibleRootItem()):
            if item.checkState() == 2:
                # print(item.text())
                self.books_constraints.update(item.db_object.books)
        self.get_data()

    # Работа с данными
    def get_data(self):
        table = self.tableBooks
        table.setRowCount(0)

        # db_books = self.session.query(sql.Book).limit(1000).offset(0)
        db_books = self.session.query(sql.Book)
        if len(self.books_constraints):
            ids = []
            for book_constr in self.books_constraints:
                ids.append(book_constr.book_id)
            db_books = db_books.filter(sql.Book.id.in_(ids))
        tablerow = 0
        for db_book in db_books:
            table.setRowCount(tablerow+1)
            table.setItem(tablerow, 0, QTableWidgetItem(db_book.title))
            tablerow += 1
            #table.model().index(1,1)
            #table.model().data(table.model().index(1,0))
            #table.model().columnCount()
            # table.model().rowCount()
            # table.model().headerData(1, )
            # table.model().headerData(0, Qt.Orientation.Vertical, Qt.ItemDataRole.TextColorRole)



    def create_filter_items(self, session, parent_item, type_id, parent_id):
        for db_filter in (session.query(sql.Filter).filter_by(types_id=type_id, parent_id=parent_id).
                order_by(sql.Filter.name).all()):
            item = FilterItem(db_filter, True)
            parent_item.appendRow(item)
            self.create_filter_items(session, item, type_id, db_filter.id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())