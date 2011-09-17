#!/usr/bin/python

from sys import argv
from PySide.QtGui import QApplication

from mock_connection import MockConnection, MOCK_UCS_TREES
from mock_tree import create_tree

UCS_CONN = MockConnection
MOCK_UCS_TREES[('localhost', 80, 'admin', '')] = create_tree()

from mainwindow import BrowserWindow

if __name__ == '__main__':
    app = QApplication(argv)
    conn = UCS_CONN('localhost', 80)
    conn.login('admin', '')
    w = BrowserWindow(conn)
    w.show()
    app.exec_()