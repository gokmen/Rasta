#!/usr/bin/python
# -*- coding: utf-8 -*-

''' Rasta RST Editor
    2010 - Gökmen Göksel <gokmeng:gmail.com> '''

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as Published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.

from utils import *

# i18n Support
import gettext
_ = gettext.translation('rasta', fallback=True).ugettext

from qrstedit import RstTextEdit

class Rasta(QMainWindow):
    ''' Rasta main class '''

    def __init__(self, arguments):
        QMainWindow.__init__(self)
        self.ui = Ui_Rasta()
        self.ui.setupUi(self)

        self.ui.textEdit = RstTextEdit(self.ui.splitter)
        self.ui.webView = QtWebKit.QWebView(self.ui.splitter)

        self.setUnifiedTitleAndToolBarOnMac(True)

        self._latest_html = None

        # System settings
        self.settings = QSettings()
        self.readSettings()

        self.file_name = TMPFILE
        if len(arguments) > 1:
            if not unicode(arguments[1]).startswith('--'):
                self.loadFile(arguments[1])
                self.updateRst(force = True)
        else:
            self.showHelp()

        self.buildToolbar()

        if '--hide-source' in arguments:
            self.ui.actionShow_Source.toggle()

    def updateRst(self, source = None, force = False):
        ''' Rebuild current source and show it in webview '''
        if self.ui.actionLive_Update.isChecked() or\
                self.sender() == self.ui.actionUpdate_Now or\
                source or force:
            self.last_scroll_position = self.ui.webView.page().mainFrame().scrollBarValue(Qt.Vertical)
            if not source:
                source = unicode(self.ui.textEdit.toPlainText())

            PUB.set_source(source)
            PUB.set_destination()
            PUB.document = PUB.reader.read(PUB.source, PUB.parser, PUB.settings)
            PUB.apply_transforms()

            logs = []
            self.ui.textEdit.clearFlags()
            for node in PUB.document.traverse(docutils.nodes.problematic):
                node.parent.replace(node, node.children[0])
            for node in PUB.document.traverse(docutils.nodes.system_message):
                log = clear_log(node)
                node.parent.remove(node)
                logs.append(log)
                line = int(log[0])
                self.ui.textEdit.addFlag(line)

            html = PUB.writer.write(PUB.document, PUB.destination)

            model = LogTableModel(logs, self)
            self.ui.logs.setModel(model)
            self.ui.logs.resizeColumnsToContents()
            self._latest_html = html
            self.ui.webView.setHtml(unicode(html, 'UTF-8'))
            self.ui.webView.page().mainFrame().setScrollBarValue(Qt.Vertical, self.last_scroll_position)
            if len(logs) > 0 and self.ui.actionShow_Logs.isChecked():
                self.ui.Logs.show()
            else:
                self.ui.Logs.hide()
            self.ui.textEdit.lineNumber.update()

    def addTable(self):
        ''' Add Rst style table '''
        cursor = self.ui.textEdit.textCursor()
        cursor.beginEditBlock()
        char_format = QTextCharFormat()
        char_format.setFontFixedPitch(True)
        cursor.setCharFormat(char_format)
        row = QInputDialog.getInteger(self,
                _('Add Table'), _('Number of rows :'), 1)
        if row[1]:
            column = QInputDialog.getInteger(self, _('Add Table'),
                    _('Number of columns :'), 1)
            if column[1]:
                cell_size = QInputDialog.getInteger(self, _('Add Table'),
                            _('Cell size :'), 8)
                if cell_size[1]:
                    cursor.insertText('\n')
                    for times in range(row[0]):
                        cursor.insertText('%s+\n' % ('+%s' % ('-' * cell_size[0]) * column[0]))
                        cursor.insertText('%s|\n' % ('|%s' % (' ' * cell_size[0]) * column[0]))
                    cursor.insertText('%s+\n' % ('+%s' % ('-' * cell_size[0]) * column[0]))
        cursor.endEditBlock()

    def editTrigger(self):
        ''' If user clicks some of edit action it calls this method '''
        marker = None
        header = None
        cursor = self.ui.textEdit.textCursor()
        if cursor.hasSelection():
            selection = cursor.selectedText()
            if self.sender() == self.ui.actionBold:
                marker = '**'
            elif self.sender() == self.ui.actionItalic:
                marker = '*'
            elif self.sender() == self.ui.actionCode:
                marker = '``'
            elif self.sender() == self.ui.actionSymbol_1:
                 header = '~'
            elif self.sender() == self.ui.actionSymbol_2:
                 header = '*'
            elif self.sender() == self.ui.actionSymbol_3:
                 header = '-'
            elif self.sender() == self.ui.actionLink:
                link, res = QInputDialog.getText(self,
                        _('Insert Link'), _('Address :'))
                if res:
                    if not unicode(link[0]).startswith('http'):
                        link = 'http://%s' % link

                    cursor.beginEditBlock()
                    cursor.removeSelectedText()
                    cursor.insertText("`%s <%s>`_" % (selection, link))
                    cursor.endEditBlock()

            if header:
                add = '' if cursor.positionInBlock() - len(selection) == 0 else '\n' * 2
                cursor.beginEditBlock()
                cursor.removeSelectedText()
                cursor.insertText("%s%s\n%s\n" % (add, selection, (header * len(selection))))
                cursor.endEditBlock()

            if marker:
                cursor.beginEditBlock()
                cursor.removeSelectedText()
                cursor.insertText("%s%s%s" % (marker, selection, marker))
                cursor.endEditBlock()

    ## File Operations

    def newFile(self):
        ''' Create new file '''
        if self.checkModified():
            self.ui.textEdit.clear()
            self.file_name = TMPFILE
        self.setWindowTitle('Rasta - %s' % self.file_name)

    def fileOpen(self):
        ''' It shows Open File dialog '''
        if self.checkModified():
            file_name = QFileDialog.getOpenFileName(self)
            if not file_name.isEmpty():
                self.loadFile(file_name)

    def loadFile(self, file_name, parse_string=False):
        ''' Load given file and show it in QSci component '''
        try:
            file_object = file(file_name, 'r')
        except Exception, msg:
            QMessageBox.warning(self, 'Rasta',
                                QString(_('Cannot read file %1:\n%2.'))
                                .arg(file_name)
                                .arg(msg))
            return

        self.file_name = file_name
        content = unicode(file_object.read())
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.restoreOverrideCursor()
        if parse_string:
            return content
        self.ui.textEdit.setPlainText(content)
        self.ui.textEdit.document().setModified(False)
        self.setWindowTitle('Rasta :: %s' % file_name)
        file_object.close()

    def resizeEvent(self, event):
        self.ui.textEdit.lineNumber.resizeEvent(event)

    def saveFile(self):
        ''' File save operation '''
        if self.file_name == TMPFILE or self.sender() == self.ui.actionSave_As:
            get_new_file_name = QFileDialog.getSaveFileName(self, _('Save File'))
            if not get_new_file_name.isEmpty():
                self.file_name = get_new_file_name
            else:
                return
        try:
            file_object = file(self.file_name, 'w')
        except Exception, msg:
            QMessageBox.warning(self, 'Rasta',
                                QString(_('Cannot write file %1:\n%2.'))
                                .arg(self.file_name)
                                .arg(msg))
            return False
        QApplication.setOverrideCursor(Qt.WaitCursor)
        file_object.write(self.ui.textEdit.toPlainText())
        QApplication.restoreOverrideCursor()
        self.ui.textEdit.document().setModified(False)
        self.setWindowTitle('Rasta :: %s' % self.file_name)
        file_object.close()
        return True

    def exportFile(self):
        ftype = None
        if self.sender() == self.ui.actionExportHTML:
            ftype = 'html'

        if ftype:
            get_new_file_name = QFileDialog.getSaveFileName(self,
                                                            _('Save File'))
            if not get_new_file_name.isEmpty():
                export_name = get_new_file_name
            else:
                return

            try:
                file_object = file(export_name, 'w')
            except Exception, msg:
                QMessageBox.warning(self, 'Rasta',
                                    QString(_('Cannot write file %1:\n%2.'))
                                    .arg(export_name)
                                    .arg(msg))
                return False

            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.updateRst()
            file_object.write(self._latest_html)
            file_object.close()
            QApplication.restoreOverrideCursor()
            return True

    ## Some Dialogs

    def showFontDialog(self):
        ''' Show font selection dialog for RstEdit component '''
        self.ui.textEdit.setFont(QFontDialog.getFont(self.ui.textEdit.font())[0])

    def showAbout(self):
        ''' Show About dialog '''
        QMessageBox.about(self, _('Rasta the Rst Editor'),
                               _('Live view supported Qt4 based Webkit '
                                 'integrated Rst editor for Pardus Developers'
                                 ' and all others.\n\n Author: Gökmen Göksel '
                                 '<gokmeng@gmail.com>'))

    def showHelp(self):
        ''' Show help for rst, it loads HELP document to the webview '''
        _tmp = self.file_name
        if os.path.exists('/usr/share/rasta/HELP'):
            self.updateRst(source = self.loadFile('/usr/share/rasta/HELP',
                           parse_string = True))
        else:
            self.ui.webView.load(
                    QUrl('http://developer.pardus.org.tr/howto/howto-rst.html'))
        self.file_name = _tmp

    ## Settings

    def writeSettings(self):
        ''' Write settings config file '''

        # For MainWindow
        self.settings.beginGroup('MainWindow')
        self.settings.setValue('size', self.size())
        self.settings.setValue('pos', self.pos())
        self.settings.setValue('liveupdate',
                self.ui.actionLive_Update.isChecked())
        self.settings.setValue('showlogs', self.ui.actionShow_Logs.isChecked())
        self.settings.setValue('spellcheck', self.ui.actionSpellcheck.isChecked())
        self.settings.endGroup()

        # For TextEdit
        self.settings.beginGroup('TextEdit')
        self.settings.setValue('size', self.ui.textEdit.size())
        self.settings.setValue('font', self.ui.textEdit.font().toString())
        self.settings.endGroup()

    def readSettings(self):
        ''' Read settings from config file '''

        # For MainWindow
        self.settings.beginGroup('MainWindow')
        self.resize(self.settings.value('size', QSize(800, 400)).toSize())
        self.move(self.settings.value('pos', QPoint(20, 20)).toPoint())
        self.ui.actionLive_Update.setChecked(
                self.settings.value('liveupdate', True).toBool())
        self.ui.actionShow_Logs.setChecked(
                self.settings.value('showlogs', True).toBool())
        self.ui.Logs.setVisible(self.ui.actionShow_Logs.isChecked())
        self.ui.actionSpellcheck.setChecked(
            self.settings.value('spellcheck', True).toBool())
        if not self.ui.actionSpellcheck.isChecked():
            self.ui.textEdit.toggleSpellChecking()
        self.settings.endGroup()

        # For TextEdit
        self.settings.beginGroup('TextEdit')
        self.ui.textEdit.resize(
                self.settings.value('size', QSize(300, 560)).toSize())
        self.buildSci(self.settings.value('font', 'Monospace'))
        self.settings.endGroup()

    ## UI Utils

    def buildToolbar(self):
        ''' Build toolbar actions and connect them to proper methods '''

        # Toolbar
        self.ui.toolBar.addAction(self.ui.actionNew)
        self.ui.toolBar.addAction(self.ui.actionOpen)
        self.ui.toolBar.addAction(self.ui.actionSave)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addAction(self.ui.actionLive_Update)
        self.ui.toolBar.addAction(self.ui.actionUpdate_Now)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addAction(self.ui.actionUndo)
        self.ui.toolBar.addAction(self.ui.actionRedo)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addAction(self.ui.actionBold)
        self.ui.toolBar.addAction(self.ui.actionItalic)
        self.ui.toolBar.addAction(self.ui.actionCode)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addAction(self.ui.actionLink)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addAction(self.ui.actionAdd_Table)

        # Connections
        self.ui.actionOpen.triggered.connect(self.fileOpen)
        self.ui.actionSave.triggered.connect(self.saveFile)
        self.ui.actionSave_As.triggered.connect(self.saveFile)
        self.ui.actionExportHTML.triggered.connect(self.exportFile)
        self.ui.actionNew.triggered.connect(self.newFile)
        self.ui.actionUpdate_Now.triggered.connect(self.updateRst)
        self.ui.actionShow_Logs.toggled.connect(self.ui.Logs.setVisible)
        self.ui.actionShow_Source.toggled.connect(self.ui.textEdit.setVisible)
        self.ui.actionShow_Output.toggled.connect(self.ui.webView.setVisible)
        self.ui.actionSpellcheck.toggled.connect(self.ui.textEdit.toggleSpellChecking)
        self.ui.actionBold.triggered.connect(self.editTrigger)
        self.ui.actionItalic.triggered.connect(self.editTrigger)
        self.ui.actionCode.triggered.connect(self.editTrigger)
        self.ui.actionSymbol_1.triggered.connect(self.editTrigger)
        self.ui.actionSymbol_2.triggered.connect(self.editTrigger)
        self.ui.actionSymbol_3.triggered.connect(self.editTrigger)
        self.ui.actionLink.triggered.connect(self.editTrigger)
        self.ui.actionAdd_Table.triggered.connect(self.addTable)
        self.ui.actionRst_Howto.triggered.connect(self.showHelp)
        self.ui.actionWrap_Text.triggered.connect(self.ui.textEdit.wrapText)
        self.ui.actionSelect_Editor_Font.triggered.connect(self.showFontDialog)
        self.ui.actionAbout.triggered.connect(self.showAbout)
        self.ui.textEdit.textChanged.connect(self.updateRst)
        self.ui.logs.doubleClicked.connect(self.goToLine)
        self.ui.actionSpellcheck.setEnabled(SPELL_CHECK)

    def buildSci(self, font = None):
        ''' It builds RstEdit component '''
        self.ui.textEdit.setFont(QFont(font))

    def goToLine(self, index):
        ''' Set cursor position to the given index '''
        self.ui.textEdit.setFocus()
        self.ui.textEdit.setCurrentLine(
                index.child(index.row(),0).data().toInt()[0]-1)

    def checkModified(self):
        ''' Checks if the document was modified and asks for saving '''
        if (self.ui.textEdit.document().isModified()):
            ret = QMessageBox.warning(self, 'Rasta',
                          _('The document has been modified.\n'
                            'Do you want to save your changes?'),
                          QMessageBox.Save |
                          QMessageBox.Discard |
                          QMessageBox.Cancel)
            if (ret == QMessageBox.Save):
                return self.saveFile()
            elif (ret == QMessageBox.Cancel):
                return False
        return True

    def closeEvent(self, event):
        ''' Catch close event to write settings before closing '''
        self.writeSettings()
        if not self.checkModified():
            event.ignore()
            return
        event.accept()

