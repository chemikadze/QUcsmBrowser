#!/usr/bin/python

from pyucsm import *

from PySide import QtCore, QtGui
from PySide.QtCore import Qt, QObject, SIGNAL, SLOT
from PySide.QtGui import QMainWindow, QTableView, QTreeView, QSplitter
from PySide.QtGui import QStandardItemModel, QStandardItem

from async_resolver import AsyncResolver

class BrowserWindow(QMainWindow):

    MO_ROLE = Qt.UserRole+1

    def __init__(self, conn):
        super(BrowserWindow, self).__init__()
        self._conn = conn
        self._resolver = AsyncResolver()
        self._resolver.object_resolved.connect(self._data_resolved)
        self._resolver.start()
        self._init_models()
        self._init_gui()
        self._init_data()
        self._init_connections()

    def __del__(self):
        self._resolver.stop_work()
        self._resolver.terminate()

    def _init_models(self):
        self._hierarchy_model = QStandardItemModel()
        self._hierarchy_model.setColumnCount(2)
        self._hierarchy_model.setHorizontalHeaderLabels(['class', 'dn'])
        self._details_model = QStandardItemModel()
        self._details_model.setColumnCount(2)
        self._details_model.setHorizontalHeaderLabels(['Property', 'Value'])

    def _init_gui(self):
        self._widget = QSplitter(self, Qt.Horizontal)
        self._hierarchy_view = QTreeView(self._widget)
        self._details_view = QTableView(self._widget)

        self._widget.addWidget(self._hierarchy_view)
        self._widget.addWidget(self._details_view)
        self._widget.setStretchFactor(0, 2)
        self._widget.setStretchFactor(1, 1)
        self.setCentralWidget(self._widget)

        self._hierarchy_view.setModel(self._hierarchy_model)
        self._details_view.setModel(self._details_model)

        self._hierarchy_view.expanded.connect(self._mo_item_expand)

    def _init_data(self):
        item = self._row_for_mo(self._conn.resolve_dn(''))
        self._hierarchy_model.insertRow(0, item)

    def _init_connections(self):
        self.connect(self._resolver,
                        SIGNAL('object_resolved(QVariant)'),
                     self,
                        SLOT('_data_resolved(QVariant)'))
        self._hierarchy_view.activated.connect(self._item_activated)
        #self.connect(self._hierarchy_view.selectionModel(),
        #                SIGNAL('currentChanged(QModelIndex,QModelIndex)'),
        #             self,
        #                SLOT('_current_changed(QModelIndex, QModelIndex)'))
        self.connect(self._hierarchy_view.selectionModel(),
                        SIGNAL('activated(QModelIndex)'),
                     self,
                        SLOT('_item_activated(QModelIndex)'))


    def _row_for_mo(self, mo):
        row = [QStandardItem(mo.ucs_class), QStandardItem(mo.dn)]
        for item in row:
            item.setEditable(False)
        row[0].appendColumn([QStandardItem('Loading...')])
        row[0].setData(mo, self.MO_ROLE)
        return row

    def _add_mo_in_tree(self, mo, index=QtCore.QModelIndex()):
        item = None
        if index.isValid():
            item = self._hierarchy_model.itemFromIndex(index)
        else:
            item = self._get_item_for_dn(self._parent_dn(mo.dn))
        if item:
            item.appendColumn([self._row_for_mo(mo)[0]])
        self.auto_width()

    def _add_mos_in_tree(self, mos, index=QtCore.QModelIndex()):
        item = None
        if index.isValid():
            item = self._hierarchy_model.itemFromIndex(index)
        else:
            if not mos:
                return
            item = self._get_item_for_dn(self._parent_dn(mos[0].dn))
        while item.columnCount():
            item.removeColumn(0)
        items = map(self._row_for_mo, mos)
        if items:
            for x in xrange(len(items[0])):
                item.appendColumn([row[x] for row in items])
        self.auto_width()

    @staticmethod
    def _parent_dn(dn):
        parent_dn, _, rn = dn.rpartition('/')
        return parent_dn

    def _get_item_for_dn(self, dn):
        parent_dn = dn
        items = self._hierarchy_model.findItems(parent_dn, column=1)
        if items:
            return self._hierarchy_model.item(items[0].row())
        return None

    @QtCore.Slot('_data_resolved(QVariant)')
    def _data_resolved(self, datav):
        print 'Data resolved: ', datav
        index, data = datav
        if isinstance(data, UcsmObject):
            self._add_mo_in_tree(data, index=index)
        else:
            self._add_mos_in_tree(data, index=index)

    @QtCore.Slot('_current_changed(QModelIndex,QModelIndex)')
    def _current_changed(self, curr, prev):
        self._item_activated(curr)

    @QtCore.Slot('_item_activated(QModelIndex)')
    def _item_activated(self, index):
        print 'Activated: %s data %s' % (index, index.data(self.MO_ROLE))
        if index.sibling(0, 0).isValid():
            index = index.sibling(0, 0)
            data = index.data(self.MO_ROLE)
            self.set_detail_object(data)

    def _mo_item_expand(self, index):
        obj = index.data(self.MO_ROLE)
        print 'Expanded object: %s' % obj
        try:
            self._resolver.add_task(lambda: (index,
                                        self._conn.resolve_children(obj.dn)))
        except (KeyError, AttributeError):
            QtGui.QMessageBox.critical(0, 'Error', 'Object does not have dn')

    def auto_width(self):
        for view in [self._hierarchy_view, self._details_view]:
            for col in xrange(view.model().columnCount()):
                view.resizeColumnToContents(col)

    def set_detail_object(self, object):
        self._details_model.removeRows(0, self._details_model.rowCount())
        for k, v in object.attributes.iteritems():
            row = [QStandardItem(k), QStandardItem(v)]
            for item in row:
                item.setEditable(False)
            self._details_model.appendRow(row)
        self.auto_width()