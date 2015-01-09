#! python3
# -*- coding: utf-8 -*-

import os

from datetime import datetime as dt, timedelta
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QModelIndex, QPoint, QRect
from PyQt4.QtGui import QBrush, QPen, QColor, QFontMetrics, QFileDialog
from .util import s2dt, dt2s
from .settings import *
from .model import Task, TaskModel
from .config import config
from .treewidgetitem import TreeWidgetItem

_ONEDAY = timedelta(days=1)

class CalendarDrawingInfo():
    def __init__(self):
        pass

    def prepare(self, painter, rect, start, end):
        if painter is None:
            zeroRect = QRect()
            def boundingRect(s):
                """指定された文字列の描画サイズを取得する"""
                return zeroRect
        else:
            fm = QFontMetrics(painter.font())
            def boundingRect(s):
                """指定された文字列の描画サイズを取得する"""
                return fm.boundingRect(s)

        self.ys = [0,0,0,0]
        self.ys[CALENDAR_TOP] = rect.top()
        dh = (rect.bottom() - self.ys[CALENDAR_TOP])/CALENDAR_BOTTOM
        self.ys[CALENDAR_MONTH] = self.ys[CALENDAR_YEAR] + dh
        self.ys[CALENDAR_DAY] = self.ys[CALENDAR_MONTH] + dh
        self.ys[CALENDAR_BOTTOM] = rect.bottom()
        #----
        xs_ = rect.left()
        xe_ = rect.right()
        #----
        date = start
        self.xs = [[rect.left()], [rect.left()], [rect.left()]]
        self.ts = [[str(date.year)], [str(date.month)], [str(date.day)]]
        self.bs = [[boundingRect(self.ts[0][0])], [boundingRect(self.ts[1][0])], [boundingRect(self.ts[2][0])]]
        x = xs_
        pdate = date
        x += DAY_WIDTH
        while date <= end:
            date += _ONEDAY
            #-----------------------
            if pdate.day != date.day:
                y = self.ys[2]
                text = str(date.day)
                self.xs[2].append(x)
                self.ts[2].append(text)
                self.bs[2].append(boundingRect(text))
            if pdate.month != date.month:
                y = self.ys[1]
                text = str(date.month)
                self.xs[1].append(x)
                self.ts[1].append(text)
                self.bs[1].append(boundingRect(text))
            if pdate.year != date.year:
                y = self.ys[0]
                text = str(date.year)
                self.xs[0].append(x)
                self.ts[0].append(text)
                self.bs[0].append(boundingRect(text))
            #-----------------------
            x += DAY_WIDTH
            pdate = date
        else:
            self.xs[0].append(x)
            self.xs[1].append(x)
            self.xs[2].append(x)

    def drawHeader(self, painter, rect, pen4line, pen4text):
        painter.setPen(pen4line)
        self.drawCalendarHorizontalLine_(painter, rect)
        for i in range(3):
            self.drawCalendarVerticalLine_(painter, i, self.ys[i], self.ys[i+1]-1, pen4text)

    def drawCalendarHorizontalLine_(self, painter, rect):
        xs_ = rect.left()
        xe_ = rect.right()
        painter.drawLine(xs_, self.ys[1], xe_, self.ys[1])
        painter.drawLine(xs_, self.ys[2], xe_, self.ys[2])

    def drawCalendarVerticalLine_(self, painter, i, top, bottom, pen4text = None):
        yhigh = top
        ylow  = bottom
        ytext = ylow-CALENDAR_BOTTOM_MARGIN
        for j in range(len(self.ts[i])):
            xpos = self.xs[i][j]
            painter.drawLine(xpos, yhigh, xpos, ylow)
            #xpos += CALENDAR_LEFT_MARGIN
            xpos = (self.xs[i][j]+self.xs[i][j+1]-self.bs[i][j].width())/2
            if pen4text is not None:
                painter.setPen(pen4text)
                painter.drawText(xpos, ytext, self.ts[i][j])

    def drawItemBackground(self, painter, top, bottom, pen4line):
        painter.setPen(pen4line)
        self.drawCalendarVerticalLine_(painter, CALENDAR_DAY, top, bottom)


class GanttHeaderView(QtGui.QHeaderView):
    def __init__(self, ganttWidget):
        super(GanttHeaderView, self).__init__ (Qt.Horizontal, ganttWidget)
        self.ganttWidget = ganttWidget
        color = QColor(Qt.lightGray)
        color.setAlpha(128)
        self.pen4line = QPen(color)
        self.pen4text = QPen(Qt.darkGray)
        self.sectionResized.connect(self._adjustSectionSize)

    def resizeEvent(self, event):
        super(GanttHeaderView, self).resizeEvent(event)
        self._adjustSectionSize()

    def _adjustSectionSize(self):
        self.ganttWidget.getChartScrollBar().adjustSectionSize()

    def sizeHint(self):
        sh = super(GanttHeaderView, self).sizeHint()
        sh.setHeight(sh.height()*2.4)
        return sh

    def paintSection(self, painter, rect, logicalIndex):
        super(GanttHeaderView, self).paintSection(painter, rect, logicalIndex)
        if logicalIndex != COLUMN_CHART:
            return
        painter.save()
        #print("paintSection", rect, logicalIndex)
        painter.setClipRect(rect)
        sv = self.ganttWidget.getChartScrollBar().value()
        painter.translate(-sv, 0)
        rect.setRight(rect.right() + sv)
        cdi = CalendarDrawingInfo()
        cdi.prepare(painter, rect, self.ganttWidget.ganttModel.start, self.ganttWidget.ganttModel.end + _ONEDAY)
        cdi.drawHeader(painter, rect, self.pen4line, self.pen4text)
        painter.restore()

class ChartScrollBar(QtGui.QScrollBar):
    """チャート部用のスクロールバーを作成する"""

    def __init__(self, ganttWidget):
        super(ChartScrollBar, self).__init__(Qt.Horizontal, ganttWidget)
        self.ganttWidget = ganttWidget
        self.valueChanged.connect(self.adjustScrollPosition)

    def adjustSectionSize(self):
        """チャート部を、Widgetの端まで広げる"""
        header = self.ganttWidget.header()
        if header is None:
            return
        width = header.width()
        for i in range(header.count()):
            if i != COLUMN_CHART:
                width -= header.sectionSize(i)
        if width >= 0:
            header.resizeSection(COLUMN_CHART, width)
        self._adjustScrollBar()

    def _adjustScrollBar(self):
        """スクロールバーの最大値を設定、必要あれば現在値も修正する"""
        self.setMaximum(self.ganttWidget.preferableWidth() - self.ganttWidget.header().sectionSize(COLUMN_CHART))

    def adjustScrollPosition(self, value):
        #print("adjustScrollPosition", value, self.updatesEnabled())
        #self.ganttWidget.paintEvent(QtGui.QPaintEvent(QRect(0,0,1004,639)))
        self.ganttWidget.header().headerDataChanged(Qt.Horizontal, COLUMN_CHART, COLUMN_CHART)
        self.ganttWidget.headerItem().emitDataChanged()


class Widget_(QtGui.QTreeWidget):
    def __init__(self, model = TaskModel()):
        super(Widget_, self).__init__()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._csb = ChartScrollBar(self)
        self.setHeader(GanttHeaderView(self))
        self.ganttModel = model
        self.pen4chartBoundary = QPen(QColor(128,128,128,128))
        self.brush4chartFill = QBrush(QColor(0,64,64,128))
        self.brush4chartFillProgress = QBrush(QColor(255,0,0,128))
        self.cdi = None
        self.setHeaderLabels(["項目名","開始日","終了日","担当者", ""])

    @property
    def ganttModel(self):
        return self._ganttModel

    @ganttModel.setter
    def ganttModel(self, model):
        if model is None:
            return
        self._ganttModel = model
        self.clear()
        items = TreeWidgetItem.Items(model.children)
        self.addTopLevelItems(items)
        self._sync_expand_collapse(items)

    def _sync_expand_collapse(self, items):
        for item in items:
            self._sync_expand_collapse(item.childItems())
            if item.task.expanded:
                self.expandItem(item)
            else:
                self.collapseItem(item)

    def preferableWidth(self):
        if self.ganttModel is None:
            return 0
        return self.xpos(self.ganttModel.end+_ONEDAY)

    def xpos(self, dt):
        tdelta = dt - self.ganttModel.start
        return tdelta.days * DAY_WIDTH

    def paintEvent(self, e):
        rect = e.rect()
        #print("paintEvnt", rect)
        rect.setLeft(self.columnViewportPosition(COLUMN_CHART))
        self.cdi = CalendarDrawingInfo()
        self.cdi.prepare(None, rect, self.ganttModel.start, self.ganttModel.end + _ONEDAY)
        super(Widget_, self).paintEvent(e)

    def drawRow(self, painter, options, index):
        """ガントチャート1行を描画する"""
        super(Widget_, self).drawRow(painter, options, index)
        painter.save()
        #print(self.visualRect(index))
        itemRect = self.visualRect(index.sibling(index.row(), COLUMN_CHART))
        #itemRect = self.visualItemRect(item)
        #print("\tdrawRow:", itemRect)
        painter.setClipRect(itemRect)
        painter.translate(-self.getChartScrollBar().value(), 0)
        #----
        self.drawItemBackground(painter, itemRect)
        task = self.itemFromIndex(index).data(COLUMN_CHART, Qt.UserRole)
        if task is not None:
            self.drawChart(painter, task, self._chartRect(task, itemRect))
        #----
        painter.restore()

    def _chartRect(self, task, rect):
        """taskを描画する矩形の座標を算出する"""
        y = (rect.top()+rect.bottom())/2
        x0 = self.columnViewportPosition(COLUMN_CHART)
        x1 = x0 + self.xpos(task.start)
        x2 = x0 + self.xpos(task.end+_ONEDAY)
        #print(x1, x2)
        return QRect(x1, y-CHART_HEIGHT/2, x2-x1, CHART_HEIGHT)

    def drawChart(self, painter, task, chartRect):
        #painter.drawLine(x1, y, x2, y)
        painter.fillRect(chartRect, self.brush4chartFill)
        painter.setPen(self.pen4chartBoundary)
        painter.drawRect(chartRect)
        #--進捗率の表示--
        if task.pv > 0:
            progressRect = QRect(
                chartRect.left(),
                chartRect.top()+(chartRect.height()-PROGRESST_HEIGHT)/2,
                chartRect.width() * task.ev/task.pv,
                PROGRESST_HEIGHT)
            painter.fillRect(progressRect, self.brush4chartFillProgress)
            painter.drawRect(progressRect)

    def drawItemBackground(self, painter, itemRect):
        #this methhod is called outside paintEvent in MacOS X
        if self.cdi is not None:
            self.cdi.drawItemBackground(painter, itemRect.top(), itemRect.bottom(), self.pen4chartBoundary)

    def getChartScrollBar(self):
        """チャート部用のスクロールバーを取得する"""
        return self._csb

class GanttWidget(Widget_):
    #-----------------------------------------------------------------------
    # Qtシグナル
    #-----------------------------------------------------------------------
    currentFileChanged = QtCore.pyqtSignal(str)

    #-----------------------------------------------------------------------
    # コンストラクタ
    #-----------------------------------------------------------------------
    def __init__(self, model = None):
        super(GanttWidget, self).__init__()
        #-----------------------------------------------------------------------
        self._currentFileName = None
        self._path = None
        self._workingDirectory = None
        #-----------------------------------------------------------------------
        self.itemChanged.connect(self.taskChanged)
        self.itemCollapsed.connect(self.taskCollapsed)
        self.itemExpanded.connect(self.taskExpanded)

    #-----------------------------------------------------------------------
    # その他
    #-----------------------------------------------------------------------
    @property
    def path(self):
        return self._path

    @property
    def workingDirectory(self):
        if self._path is None:
            self._path = os.getcwd()
        return self._path

    @property
    def currentFileName(self):
        return self._currentFileName

    def load(self, fileName):
        try:
            self._workingDirectory = os.path.dirname(fileName)
            self.ganttModel = TaskModel.load(fileName)
            config.addLastUsed(fileName)
            self._currentFileName = fileName
            self.currentFileChanged.emit(self._currentFileName)
        except :
            if DEBUG:
                raise
            else:
                print("Unexpected error:", sys.exc_info())
                QtGui.QMessageBox.warning(self,
                    "がんと", "<%s>を開けませんでした" % fileName, "OK")

    def saveFile(self, fileName):
        try:
            print("save %s" % fileName)
            self._workingDirectory = os.path.dirname(fileName)
            TaskModel.dump(self.ganttModel, fileName)
            self._currentFileName = fileName
            self.currentFileChanged.emit(self._currentFileName)
        except:
            if DEBUG:
                raise
            else:
                print("Unexpected error:", sys.exc_info())
                QtGui.QMessageBox.warning(self,
                    "がんと", "<%s>を開けませんでした" % fileName, "OK")

    #---------------------------------------------------------------------------
    #   アクション
    #---------------------------------------------------------------------------
    def insert(self, action):
        """カレントアイテムの場所に新規タスクを挿入する"""
        (ci, index, parent, parentTask) = self._get_item_info()
        newItem = TreeWidgetItem(Task.defaultTask())
        parent.insertChild(index, newItem)
        parentTask.children.insert(index, newItem.task)

    def remove(self, action):
        """カレントアイテムを削除する"""
        (ci, index, parent, parentTask) = self._get_item_info()
        if ci is None:
            return
        parentTask.children.remove(ci.task)
        parent.removeChild(ci)

    def _get_item_info(self, ci = None):
        if ci is None:
            ci = self.currentItem()
        if ci is None:
            parent = self.invisibleRootItem()
            parentTask = self.ganttModel
            index = 0
        elif self._isToplevel(ci):
            parent = self.invisibleRootItem()
            parentTask = self.ganttModel
            index = parent.indexOfChild(ci)
        else:
            parent = ci.parent()
            parentTask = parent.task
            index = parent.indexOfChild(ci)
        return (ci, index, parent, parentTask)

    def _isToplevel(self, item):
        if item.parent() is None:
            return True
        if self.indexFromItem(item.parent(), 0).isValid():
            return False
        return True

    def levelUp(self, action):
        (ci, index, parent, parentTask) = self._get_item_info()
        if ci is None:
            return
        if self._isToplevel(ci):
            #トップレベルにいるなら、レベルを上げようがない
            return
        #親アイテムから離脱する
        parentTask.children.remove(ci.task)
        parent.removeChild(ci)
        #親アイテムの直近の弟になる。
        (parent, parent_index, granpa, granpaTask) = self._get_item_info(parent)
        granpa.insertChild(parent_index+1, ci)
        granpaTask.children.insert(parent_index+1, ci.task)
        self._sync_expand_collapse([ci])
        #対象タスクをカレントタスクにする
        self.setCurrentItem(ci)

    def levelDown(self, action):
        (ci, index, parent, parentTask) = self._get_item_info()
        if ci is None:
            return
        modelIndex = self.indexFromItem(ci, 0)
        if modelIndex.row() <= 0:
            #兄アイテムがいない場合は処理を行わない
            return
        #年の近い兄アイテムを探しておく
        sibling = self.itemFromIndex(modelIndex.sibling(modelIndex.row()-1, 0))
        #親アイテムから離脱する
        parentTask.children.remove(ci.task)
        parent.removeChild(ci)
        #年の近い兄アイテムの末子になる
        sibling.addChild(ci)
        sibling.task.children.append(ci.task)
        self._sync_expand_collapse([ci])
        #対象タスクをカレントタスクにする
        self.setCurrentItem(ci)

    def up(self, action):
        """同一レベル内で一つ上に移動する"""
        (ci, index, parent, parentTask) = self._get_item_info()
        if ci is None:
            return
        newIndex = index - 1
        if newIndex < 0:
            #すでに一番上にいるなら処理を行わない
            return
        #一つ上の位置に挿入する
        self._move(ci, newIndex, parent, parentTask)

    def down(self, action):
        """同一レベル内で一つ下に移動する"""
        (ci, index, parent, parentTask) = self._get_item_info()
        if ci is None:
            return
        newIndex = index + 1
        if parent.childCount() <= newIndex:
            #すでに一番下にいるなら処理を行わない
            return
        #一つ下の位置に挿入する
        self._move(ci, newIndex, parent, parentTask)

    def _move(self, ci, newIndex, parent, parentTask):
        #一旦、親アイテムから離脱する
        parentTask.children.remove(ci.task)
        parent.removeChild(ci)
        #新しい位置に挿入する
        parent.insertChild(newIndex, ci)
        parentTask.children.insert(newIndex, ci.task)
        self._sync_expand_collapse([ci])
        #対象タスクをカレントタスクにする
        self.setCurrentItem(ci)

    def open(self, action):
        """ファイルを開く"""
        fileName = QFileDialog.getOpenFileName(self,
                        'ファイルを開く', self.workingDirectory)
        print("load %s" % fileName)
        if len(fileName) <= 0:
            return
        self.load(fileName)

    def save(self, action):
        """ファイルを保存する"""
        if self._currentFileName is None:
            self.saveAs()
        else:
            self.saveFile(self._currentFileName)

    def saveAs(self, action):
        """ファイル名を指定して保存する"""
        fileName = QFileDialog.getSaveFileName(self,
                        'ファイルを保存する', self.workingDirectory)
        if len(fileName) <= 0:
            return
        self.saveFile(self._currentFileName)

    def timescaleDay(self, action):
        pass

    def timescaleWeek(self, action):
        pass

    def timescaleMonth(self, action):
        pass

    #---------------------------------------------------------------------------
    def taskChanged(self, item, column):
        task = item.task
        if column == 0:
            task.name = item.name
        if column == 1:
            task.start = s2dt(item.start)
        if column == 2:
            task.end = s2dt(item.end)

    def taskExpanded(self, item):
        item.task.expanded = True

    def taskCollapsed(self, item):
        item.task.expanded = False