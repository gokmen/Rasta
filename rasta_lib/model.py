#!/usr/bin/python
# -*- coding: utf-8 -*-

''' Rasta RST Editor
    2010 - Gökmen Göksel <gokmeng:gmail.com> '''

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as Published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.

from PyQt4.QtCore import Qt
from PyQt4.QtCore import QVariant
from PyQt4.QtCore import QAbstractTableModel

# i18n Support
import gettext
_ = gettext.translation('rasta', fallback=True).ugettext

class LogTableModel(QAbstractTableModel):
    ''' Log table model for showing the logs in a proper way '''

    def __init__(self, logs, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = logs
        self.headerdata = [_('Line'), _('Message')]

    def rowCount(self, parent):
        ''' Return number of logs '''
        return len(self.arraydata)

    def columnCount(self, parent):
        ''' It always returns 2 for now: Line and Message '''
        return len(self.headerdata)

    def data(self, index, role):
        ''' Return data for given index and role '''
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.arraydata[index.row()][index.column()])

    def headerData(self, col, orientation, role):
        ''' Return Header data for given column '''
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.headerdata[col])
        return QVariant()
