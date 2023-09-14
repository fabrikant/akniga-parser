import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui
from PyQt5.Qt import QStandardItemModel, QStandardItem
import akniga_sql as sql


class FilterItem(QStandardItem):
    def __init__(self, base_object=None, checkable=False):
        super().__init__()
        self.base_object = base_object
        self.setText(base_object.name)
        self.setCheckable(checkable)


def create_filter_items(session, parent_item, type_id, parent_id):
    for bd_filter in (session.query(sql.Filter).filter_by(types_id=type_id, parent_id=parent_id).
            order_by(sql.Filter.name).all()):
        item = FilterItem(bd_filter, True)
        parent_item.appendRow(item)
        create_filter_items(session, item, type_id, bd_filter.id)


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('ui/main.ui', self)


    def on_start_connecting(self):
        session = sql.get_session('sqlite:///akniga.db')
        treeView = self.filtersTreeView
        treeView.setHeaderHidden(True)
        treeModel = QStandardItemModel()
        rootNode = treeModel.invisibleRootItem()

        for bd_filter_type in session.query(sql.FilterType).order_by(sql.FilterType.name).all():
            item = FilterItem(bd_filter_type, False)
            rootNode.appendRow(item)
            create_filter_items(session, item, bd_filter_type.id, None)

        treeView.setModel(treeModel)
        treeView.expandAll()



    # def onButtonOpenPathClick(self):
    #     path = QFileDialog.getExistingDirectory(self, caption='Open directory')
    #     self.linePath.setText(path)
    #
    # def onButtonDownloadClick(self):
    #     sub_window = ProcessWindow(self.lineURL.text(), self.linePath.text())
    #     self.mdiArea.addSubWindow(sub_window)
    #     sub_window.show()
    #
    # def onButtonPaste(self):
    #     if 'akniga.org' in app.clipboard().text():
    #         self.lineURL.setText(app.clipboard().text())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())