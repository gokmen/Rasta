#!/usr/bin/env python
# -*- coding: utf-8 -*-

''' Rasta RST Editor
    2010 - Gökmen Göksel <gokmeng:gmail.com> '''

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.

# RstTextEdit Widget based on John Schember 's (2009) SpellText Edit which has
# MIT License

import re
import sys

from utils import *
from PyQt4.Qt import *

# i18n Support
import gettext
_ = gettext.translation('rasta', fallback=True).ugettext

def wrap(text, limit = 80):
    import textwrap
    result = ''

    for line in text.splitlines():
        if len(line) > limit:
            lines = textwrap.wrap(line, limit)
            result += '\n'.join(lines)
            result += '\n'
        else:
            result += '%s\n' % line

    return result

class RstTextEdit(QPlainTextEdit):

    def __init__(self, *args):
        QPlainTextEdit.__init__(self, *args)
        self.lineNumber = LineNumber(self)

        if SPELL_CHECK:
            # Default dictionary based on the current locale.
            self.dict = enchant.Dict()
            self.highlighter = RstHighlighter(self.document())
            self.highlighter.setDict(self.dict)

        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.highlightCurrentLine()

        insertShortcut = QShortcut(Qt.Key_Insert, self)
        insertShortcut.activated.connect(lambda: self.setOverwriteMode(not self.overwriteMode()))

    def addFlag(self, line):
        if not line in self.lineNumber._flaged_lines:
            self.lineNumber._flaged_lines.append(line)
            self.lineNumber.update()

    def clearFlags(self):
        self.lineNumber._flaged_lines = []

    def toggleSpellChecking(self):
        if not SPELL_CHECK:
            return

        if not self.highlighter.dict:
            self.highlighter.setDict(self.dict)
        else:
            self.highlighter.setDict(None)
        self.highlighter.rehighlight()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            # Rewrite the mouse event to a left button event so the cursor is
            # moved to the location of the pointer.
            event = QMouseEvent(QEvent.MouseButtonPress, event.pos(),
                Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QPlainTextEdit.mousePressEvent(self, event)

    def setCurrentLine(self, line):
        # Hacky, but works.
        self.verticalScrollBar().setValue(0)
        block = QTextBlock(self.firstVisibleBlock())
        while block.isValid():
            if block.blockNumber() == line:
                cursor = self.textCursor()
                cursor.setPosition(block.position(), QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
                break
            block = block.next()

    def wrapText(self, width = 80):
        self.correctWord(wrap(unicode(self.textCursor().selectedText())))

    def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            lineColor.setAlpha(100)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def contextMenuEvent(self, event):
        popup_menu = self.createStandardContextMenu()

        # Select the word under the cursor.
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        self.setTextCursor(cursor)

        # Check if the selected word is misspelled and offer spelling
        # suggestions if it is.
        if self.textCursor().hasSelection():
            text = unicode(self.textCursor().selectedText())
            if not self.dict.check(text):
                spell_menu = QMenu(_('Spelling Suggestions'))
                for word in self.dict.suggest(text):
                    action = SpellAction(word, spell_menu)
                    action.correct.connect(self.correctWord)
                    spell_menu.addAction(action)
                # Only add the spelling suggests to the menu if there are
                # suggestions.
                if len(spell_menu.actions()) != 0:
                    popup_menu.insertSeparator(popup_menu.actions()[0])
                    popup_menu.insertMenu(popup_menu.actions()[0], spell_menu)

        popup_menu.exec_(event.globalPos())

    def correctWord(self, word):
        # Replaces the selected text with word.
        cursor = self.textCursor()
        cursor.beginEditBlock()

        cursor.removeSelectedText()
        cursor.insertText(word)

        cursor.endEditBlock()

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        painter.setPen(Qt.lightGray)
        fw = self.fontMetrics().width('X')
        cw = (80 * fw) + (fw / 2) + 2
        painter.drawLine(cw, 0, cw, self.height())
        painter.end()
        QPlainTextEdit.paintEvent(self, event)

class LineNumber(QWidget):

    """ Line Number widget for RstTextEdit component """

    def __init__(self, editor):
        QWidget.__init__(self, editor)
        self.editor = editor
        self.editor.blockCountChanged.connect(self.updateAreaWidth)
        self.editor.updateRequest.connect(self.updateLineNumber)
        self._flaged_lines = []
        self.updateAreaWidth()

    def resizeEvent(self, event):
        cr = QRect(self.editor.contentsRect())
        self.setGeometry(QRect(cr.left(), cr.top(), self.areaWidth(), cr.height()))

    def updateLineNumber(self, rect, num):
        if num:
            self.scroll(0, num)
        else:
            self.update(0, rect.y(), self.width(), rect.height())

        if rect.contains(self.editor.viewport().rect()):
            self.updateAreaWidth()

    def updateAreaWidth(self, width = 0):
        self.editor.setViewportMargins(self.areaWidth(), 0, 0, 0)

    def sizeHint(self):
        return QSize(self.areaWidth(), 0)

    def areaWidth(self):
        digits = 3
        max_ = max(1, self.editor.blockCount())
        while max_ >= 1000:
            max_ /= 1000
            digits += 1
        # padding = 10 if len(self._flaged_lines) == 0 else 26
        return 26 + self.editor.fontMetrics().width(QChar('9')) * digits

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), Qt.lightGray)
        painter.setPen(Qt.black)
        block = QTextBlock(self.editor.firstVisibleBlock())
        blockNumber = block.blockNumber()
        top = int(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + int(self.editor.blockBoundingRect(block).height())
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = QString.number(blockNumber + 1)
                painter.drawText(0, top, self.width() - 4, self.editor.fontMetrics().height(),
                                 Qt.AlignRight, number)
                if blockNumber + 1 in self._flaged_lines:
                    painter.drawPixmap(0, top, QPixmap(':/icons/warning.png'))

            block = block.next()
            top = bottom
            bottom = top + int(self.editor.blockBoundingRect(block).height())
            blockNumber += 1

class RstHighlighter(QSyntaxHighlighter):

    """ Rst Highlighter for Rest format """

    WORDS = u'(?iu)[\w\']+'

    def __init__(self, *args):
        QSyntaxHighlighter.__init__(self, *args)

        self.dict = None

    def setDict(self, dict):
        self.dict = dict

    def highlightBlock(self, text):
        if not self.dict:
            return

        text = unicode(text)

        format = QTextCharFormat()
        start = 0
        for line in text.splitlines():
            if any(line.lstrip(' ').startswith(pointer) 
                    for pointer in ('*', '-', '#.')):
                format.setForeground(QBrush(Qt.darkCyan))
                self.setFormat(start, start + len(line), format)
            start = len(line)

        format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        format.setUnderlineColor(Qt.red)

        for word_object in re.finditer(self.WORDS, text):
            if not self.dict.check(word_object.group()):
                self.setFormat(word_object.start(),
                    word_object.end() - word_object.start(), format)

class SpellAction(QAction):
    """ A special QAction that returns the text in a signal."""

    correct = pyqtSignal(unicode)

    def __init__(self, *args):
        QAction.__init__(self, *args)
        self.triggered.connect(lambda x: self.correct.emit(
            unicode(self.text())))

