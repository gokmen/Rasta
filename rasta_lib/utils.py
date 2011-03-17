#!/usr/bin/python
# -*- coding: utf-8 -*-

''' Rasta RST Editor
    2010 - Gökmen Göksel <gokmeng:gmail.com> '''

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as Published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.

# Python Core
import os
import re
import sys

# i18n Support
import gettext
_ = gettext.translation('rasta', fallback=True).ugettext
INSTALL_PACKAGE_WARNING = _('Please install "%s" package.')

# Docutils
try:
    import docutils.io
    import docutils.nodes
    from docutils.core import Publisher
    from StringIO import StringIO
except ImportError:
    sys.exit(INSTALL_PACKAGE_WARNING % 'docutils')

# PyQt4 Core Libraries
try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4 import QtWebKit
except ImportError:
    sys.exit(INSTALL_PACKAGE_WARNING % 'Qt4')

# Rasta Core Library
try:
    from mainWindow import Ui_Rasta
except ImportError:
    sys.exit(_('Please run "setup.py build" first.'))

# Log Model for log view
from model import LogTableModel

TMPFILE = '/tmp/untitled.rst'

# Global Publisher for Docutils
PUB = Publisher(source_class=docutils.io.StringInput,
        destination_class=docutils.io.StringOutput)
PUB.set_reader('standalone', None, 'restructuredtext')
PUB.set_writer('html')
PUB.get_settings()
PUB.settings.halt_level = 7
PUB.settings.warning_stream = StringIO()

def clear_log(log):
    ''' Removes not needed lines from log output '''
    try:
        log = unicode(log)
        return re.findall("line\=\"(.*?)\"", log)[0], re.findall("\<paragraph\>(.*?)\<\/paragraph\>", log)[0]
    except:
        return 1, _('Rasta parse error: %s' % log)

