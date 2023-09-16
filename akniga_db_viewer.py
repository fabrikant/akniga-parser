import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore, QtGui
from PyQt5.Qt import QStandardItemModel, QAbstractTableModel, QStandardItem
from PyQt5.QtCore import Qt, QVariant
import akniga_sql as sql


class FilterItem(QStandardItem):
    def __init__(self, db_object=None, checkable=False):
        super().__init__()
        self.db_object = db_object
        self.setText(db_object.name)
        self.setCheckable(checkable)
        self.setEditable(False)

class BooksTableModel(QAbstractTableModel):
    def __init__(self, db_books=None, hidden_columns=1):
        QAbstractTableModel.__init__(self, None)
        self.db_books = db_books
        self.db_books_list = self.db_books.all()
        self.visible_columns = len(self.db_books.column_descriptions) - hidden_columns

    def rowCount(self, parent):
        return len(self.db_books_list)

    def columnCount(self, parent):
        return self.visible_columns

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        else:
            return self.db_books_list[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.db_books.column_descriptions[col]['name']
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return col
        else:
            return QVariant()

    def get_description(self, row):
        return self.db_books_list[row][len(self.db_books.column_descriptions) - 1].description

    def sort(self, Ncol, order):
        print('sort', Ncol, order)


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui/main.ui', self)
        # self.books_constraints = set()




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
        treeView.expandAll()
        self.get_data()

    def on_filter_check_uncheck(self, checked_item):
        self.get_data()

    def set_constraints(self, db_books):

        def iter_items(root):
            def recurse(parent):
                for row in range(parent.rowCount()):
                    child = parent.child(row, 0)
                    yield child
                    if child.hasChildren():
                        yield from recurse(child)

            if root is not None:
                yield from recurse(root)

        tree = self.filtersTree
        root_item = tree.model().invisibleRootItem()
        for type_item_num in range(root_item.rowCount()):
            type_item = root_item.child(type_item_num, 0)
            set_filter = False
            constraints = set()
            for filter_item in iter_items(type_item):
                if filter_item.checkState() == 2:
                    constraints.update(filter_item.db_object.books)
                    set_filter = True
            if set_filter:
                ids = []
                for book_constr in constraints:
                    ids.append(book_constr.book_id)
                db_books = db_books.filter(sql.Book.id.in_(ids))

                db_books = db_books.filter(sql.Book.id.in_(ids))

        return db_books

    def on_book_row_selected(self, selection1, selection2):
        description = self.table_books.model().get_description(selection1.first().indexes()[0].row())
        self.description.setDocument(QtGui.QTextDocument(description))

    def set_columns_width(self, table, max_width):
        for num_col in range(table.model().columnCount(None)):
            width = max_width if table.columnWidth(num_col) > max_width else table.columnWidth(num_col)
            table.setColumnWidth(num_col, width)

    # Работа с данными
    def get_data(self):
        self.description.setDocument(QtGui.QTextDocument(''))
        db_books = self.session.query(sql.Book.title.label('Название'), sql.Author.name.label('Автор'),
                                      sql.Book.duration.label('Продолжительность'),
                                      sql.Performer.name.label('Исполнитель'), sql.Book.free.label('Бесп.'), sql.Book)

        db_books = self.set_constraints(db_books)

        db_books = db_books.join(sql.Author).join(sql.Performer)
        db_books = db_books.limit(1000).offset(0)

        table = self.table_books
        table.setModel(BooksTableModel(db_books))
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        selectionModel = self.table_books.selectionModel()
        selectionModel.selectionChanged.connect(self.on_book_row_selected)

        self.set_columns_width(table, 350)



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