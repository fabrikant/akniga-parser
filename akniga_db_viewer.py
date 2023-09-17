import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore, QtGui
from PyQt5.Qt import QStandardItemModel, QAbstractTableModel, QStandardItem
from PyQt5.QtCore import Qt, QVariant, QTime
from PyQt5.QtGui import QIntValidator
import akniga_sql as sql
import logging

logger = logging.getLogger(__name__)


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

    def sort(self, col, order):
        def get_key(row):
            return row[col]
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


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui/main.ui', self)
        self.session = None


    def on_start_connecting(self):
        self.session = sql.get_session('sqlite:///akniga.db')
        self.load_constraints()
        self.load_sections()
        self.get_data()

    def on_filter_check_uncheck(self, checked_item):
        self.get_data()

    def on_filter_time_clear(self):
        self.time_min.setTime(QTime(0, 0))
        self.time_max.setTime(QTime(0, 0))
        self.get_data()

    def on_filter_title_clear(self):
       self.clear_text_filter(self.filter_title)

    def on_filter_author_clear(self):
        self.clear_text_filter(self.filter_author)

    def on_filter_performer_clear(self):
        self.clear_text_filter(self.filter_performer)

    def on_filter_seria_clear(self):
        self.clear_text_filter(self.filter_seria)

    def clear_text_filter(self, text_field):
        if not text_field.text() == '':
            text_field.setText('')
            self.get_data()

    def on_filter_edit(self):
        self.get_data()

    def on_filter_text_changed(self, QString):
        if QString == '':
            self.get_data()

    def on_remove_constraints(self):
        self.load_constraints()
        self.get_data()

    def on_remove_sections(self):
        self.load_sections()
        self.get_data()

    def on_book_layout_changed_selected(self, **kwargs):
        description = ''
        sel_list = self.table_books.selectionModel().selectedIndexes()
        if len(sel_list):
            description = self.table_books.model().get_description(sel_list[0].row())
        self.description.setDocument(QtGui.QTextDocument(description))

    def on_page_next(self):
        model = self.table_books.model()
        model.next_page()
        self.page_current.setText(f'{model.page_number}')

    def on_page_prev(self):
        model = self.table_books.model()
        model.prev_page()
        self.page_current.setText(f'{model.page_number}')

    def on_page_reload(self):
        self.get_data()

    def on_page_set(self):
        model = self.table_books.model()
        model.set_page(int(f'0{self.page_current.text()}'))
        self.page_current.setText(f'{model.page_number}')

    # Жанры (Sections)
    def load_sections(self):
        sections_list = self.sections_list
        model = QStandardItemModel()
        model.itemChanged.connect(self.on_filter_check_uncheck)

        for db_section in self.session.query(sql.Section).order_by(sql.Section.name).all():
            item = FilterItem(db_section, True)
            model.appendRow(item)

        sections_list.setModel(model)

    def set_sections(self, db_books):
        model = self.sections_list.model()
        set_filter = False
        constraints = set()
        for num in range(model.rowCount()):
            filter_item = model.item(num)
            if filter_item.checkState() == 2:
                constraints.update(filter_item.db_object.books)
                set_filter = True
        if set_filter:
            ids = []
            for book_constr in constraints:
                ids.append(book_constr.book_id)
            db_books = db_books.filter(sql.Book.id.in_(ids))

        return db_books

    # Характеристики
    def load_constraints(self):

        def create_constraints_items(parent_item, type_id, parent_id):
            for db_filter in (self.session.query(sql.Filter).filter_by(types_id=type_id, parent_id=parent_id).
                    order_by(sql.Filter.name).all()):
                item = FilterItem(db_filter, True)
                parent_item.appendRow(item)
                create_constraints_items(item, type_id, db_filter.id)

        constraints_tree = self.constraints_tree
        constraints_tree.setHeaderHidden(True)
        treeModel = QStandardItemModel()
        treeModel.itemChanged.connect(self.on_filter_check_uncheck)

        rootNode = treeModel.invisibleRootItem()

        for db_filter_type in self.session.query(sql.FilterType).order_by(sql.FilterType.name).all():
            item = FilterItem(db_filter_type, False)
            rootNode.appendRow(item)
            create_constraints_items(item, db_filter_type.id, None)

        constraints_tree.setModel(treeModel)
        constraints_tree.expandAll()

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

        tree = self.constraints_tree
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

        return db_books

    # Работа с данными
    def set_filter(self, db_books, value, field):
        val = value.strip()
        if len(val):
            val = '%'+val+'%'
            db_books = db_books.filter(field.ilike(val))
        return db_books

    def get_data(self):
        if self.session is None:
            return
        self.description.setDocument(QtGui.QTextDocument(''))
        db_books = self.session.query(sql.Book.title.label('Название'), sql.Author.name.label('Автор'),
                                      sql.Seria.name.label('Серия'), sql.Book.duration_hours.label('час.'),
                                      sql.Book.duration_minutes.label('мин.'), sql.Performer.name.label('Исполнитель'),
                                      sql.Book.free.label('Беспл.'), sql.Book)

        db_books = self.set_constraints(db_books)
        db_books = self.set_sections(db_books)

        db_books = self.set_filter(db_books, self.filter_title.text(), sql.Book.title)
        db_books = self.set_filter(db_books, self.filter_author.text(), sql.Author.name)
        db_books = self.set_filter(db_books, self.filter_performer.text(), sql.Performer.name)
        db_books = self.set_filter(db_books, self.filter_seria.text(), sql.Seria.name)

        time = self.time_min.time().hour() * 60 + self.time_min.time().minute()
        if time:
            db_books = db_books.filter(sql.Book.duration >= time)

        time = self.time_max.time().hour() * 60 + self.time_max.time().minute()
        if time:
            db_books = db_books.filter(sql.Book.duration <= time)

        if self.filter_free.isChecked():
            db_books = db_books.filter(sql.Book.free)

        db_books = db_books.outerjoin(sql.Author).outerjoin(sql.Performer).outerjoin(sql.Seria)


        table = self.table_books
        table_model = BooksTableModel(db_books)
        table.setModel(table_model)
        table_model.layoutChanged.connect(self.on_book_layout_changed_selected)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        selectionModel = self.table_books.selectionModel()
        selectionModel.selectionChanged.connect(self.on_book_layout_changed_selected)

        # Интерфейсные вещи
        self.set_columns_width(table, 350)
        self.page_count.setText(f'из {table_model.pages_count}')
        self.record_count.setText(f'Всего записей: {table_model.records_count}')
        self.page_current.setText(f'{table_model.page_number}')
        self.page_current.setValidator(QIntValidator(1, table_model.pages_count))

    def set_columns_width(self, table, max_width):
        for num_col in range(table.model().columnCount(None)):
            width = max_width if table.columnWidth(num_col) > max_width else table.columnWidth(num_col)
            table.setColumnWidth(num_col, width)





if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())