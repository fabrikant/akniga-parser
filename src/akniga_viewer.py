import sys
import os
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui
from PyQt5.QtCore import QSettings
from PyQt5.Qt import QStandardItemModel, QStandardItem
import akniga_sql as sql
from akniga_settings import SettingsDialog
from akniga_global import config_file_name
import logging

logger = logging.getLogger(__name__)


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
        self.config_file_name = config_file_name
        self.read_settings()
        self.session = None
        self.filter_time_slider.valueChanged.emit(self.filter_time_slider.sliderPosition())
        self.open_database()
        self.console_dock.hide()
        self.table_books.start_process_slot = self.on_request_to_start_process
        self.console_tab.console_dock = self.console_dock

    def read_settings(self):
        settings = QSettings(self.config_file_name, QSettings.IniFormat)
        self.connection_string = settings.value('connection_string')

    def write_settings(self):
        settings = QSettings(self.config_file_name, QSettings.IniFormat)
        settings.setValue('connection_string', self.connection_string)

    def open_database(self):
        self.setWindowTitle('akniga db viewer')
        if self.connection_string:
            try:
                self.session = sql.get_session(self.connection_string)
                self.load_constraints()
                self.load_sections()
                self.get_data()
                self.setWindowTitle(f'{self.windowTitle()}: {self.connection_string}')
            except Exception as message:
                logger.error(message)

    def on_db_connect(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Открыть файл',
                                                   filter='Базы sqlite (*.sqlite);;Все файлы (*.*)')
        if file_name:
            self.connection_string = f'sqlite:///{file_name}'
            self.open_database()
            self.write_settings()

    def on_db_create(self):
        file_name, _ = QFileDialog.getSaveFileName(self, caption='Имя файла', filter='Базы sqlite (*.sqlite)')
        if file_name:
            if os.path.exists(file_name):
                os.remove(file_name)
            self.connection_string = f'sqlite:///{file_name}'
            sql.create_database(self.connection_string)
            self.open_database()
            self.write_settings()

    def on_db_update(self):
        self.console_dock.show()
        command = ['src/akniga_parser.py', '-db', self.connection_string]

        settings = QSettings(config_file_name, QSettings.IniFormat)

        start = settings.value('DatabaseUpdate/start-page', type=int, defaultValue=0)
        stop = settings.value('DatabaseUpdate/stop-page', type=int, defaultValue=0)
        if start:
            command += ['--start-page', str(start)]
        if stop:
            command += ['--stop-page', str(stop)]
        if settings.value('DatabaseUpdate/full-scan', defaultValue=0, type=int) == 2:
            command += ['--full-scan']
        if settings.value('DatabaseUpdate/update', defaultValue=0, type=int) == 2:
            command += ['--update']
        if settings.value('DatabaseUpdate/genres', defaultValue=2, type=int) == 2:
            command += ['--genres']

        self.console_tab.start_process(command)

    def on_request_to_start_process(self, command):
        self.console_dock.show()
        self.console_tab.start_process(command)

    def on_settings(self):
        dlg = SettingsDialog()
        dlg.exec()

    def on_filter_check_uncheck(self, checked_item):
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
        self.load_constraints()
        self.load_sections()
        self.get_data()

    def on_page_set(self):
        model = self.table_books.model()
        model.set_page(int(f'0{self.page_current.text()}'))
        self.page_current.setText(f'{model.page_number}')

    def on_filter_time_slider_changed(self, values):
        slider = self.filter_time_slider
        self.time_min.setText(slider.get_description(values[0]))
        self.time_max.setText(slider.get_description(values[1]))

    def on_table_book_dbl_click(self, model_index):
        dict = {'Название': self.filter_title,
                   'Автор': self.filter_author,
                   'Серия': self.filter_seria,
                   'Исполнитель': self.filter_performer}
        model = self.table_books.model()
        value, column_name, _, _ = model.get_cell_information(model_index)
        if not value is None:
            filter_edit = dict[column_name]
            if not filter_edit is None:
                filter_edit.setText(value)
                self.get_data()

    # Жанры (Sections)
    def load_sections(self):
        if self.session is None:
            return

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
        if self.session is None:
            return

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
                                      sql.Book.year.label('Год'), sql.Book.rating.label('Рейтинг'),
                                      sql.Book.free.label('Беспл.'), sql.Book)

        db_books = self.set_constraints(db_books)
        db_books = self.set_sections(db_books)

        db_books = self.set_filter(db_books, self.filter_title.text(), sql.Book.title)
        db_books = self.set_filter(db_books, self.filter_author.text(), sql.Author.name)
        db_books = self.set_filter(db_books, self.filter_performer.text(), sql.Performer.name)
        db_books = self.set_filter(db_books, self.filter_seria.text(), sql.Seria.name)

        time_slider = self.filter_time_slider
        time_min_pos, time_max_pos = time_slider.sliderPosition()
        if not time_slider.default_value(time_min_pos):
            db_books = db_books.filter(sql.Book.duration >= time_slider.get_value(time_min_pos))
        if not time_slider.default_value(time_max_pos):
            db_books = db_books.filter(sql.Book.duration <= time_slider.get_value(time_max_pos))

        if self.filter_free.isChecked():
            db_books = db_books.filter(sql.Book.free)

        db_books = db_books.outerjoin(sql.Author).outerjoin(sql.Performer).outerjoin(sql.Seria)

        self.table_books.on_get_data(db_books, self, app.clipboard())


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
