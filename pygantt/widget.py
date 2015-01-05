#! python3
# -*- coding: utf-8 -*-

from datetime import datetime as dt, timedelta
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QModelIndex, QPoint, QRect
from PyQt4.QtGui import QBrush, QPen, QColor, QFontMetrics
from .util import s2dt
from .settings import Settings

DAY_WIDTH = 16
COLUMN_NAME  = 0
COLUMN_CHART = 1
CALENDAR_BOTTOM_MARGIN = 3
CALENDAR_LEFT_MARGIN = 3
CHART_HEIGHT = 12
PROGRESST_HEIGHT = 8

CALENDAR_TOP    = 0
CALENDAR_YEAR   = 0
CALENDAR_MONTH  = 1
CALENDAR_DAY    = 2
CALENDAR_BOTTOM = 3

_ONEDAY = timedelta(days=1)

class HeaderView_(QtGui.QHeaderView):
    def sizeHint(self):
        sh = super(HeaderView_, self).sizeHint()
        sh.setHeight(sh.height()*2.4)
        return sh

class DataHeaderView(HeaderView_):
    def __init__(self, parent = None):
        super(DataHeaderView, self).__init__ (Qt.Horizontal, parent)

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


class GanttHeaderView(HeaderView_):
    def __init__(self, ganttWidget, parent = None):
        super(GanttHeaderView, self).__init__ (Qt.Horizontal, parent)
        self.ganttWidget = ganttWidget
        color = QColor(Qt.lightGray)
        color.setAlpha(128)
        self.pen4line = QPen(color)
        self.pen4text = QPen(Qt.darkGray)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super(GanttHeaderView, self).paintSection(painter, rect, logicalIndex)
        painter.restore()
        #print("paintSection", rect, logicalIndex)
        if logicalIndex != 1:
            return
        cdi = CalendarDrawingInfo()
        cdi.prepare(painter, rect, self.ganttWidget.model2.start, self.ganttWidget.model2.end + _ONEDAY)
        cdi.drawHeader(painter, rect, self.pen4line, self.pen4text)


class Widget_(QtGui.QTreeWidget):
    def __init__(self, settings):
        super(Widget_, self).__init__()
        self.settings = settings
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def setModel2(self, model):
        self.model2 = model
        if model is None:
            return
        self.setHeaderLabels(model.headerLabels())
        self.addTopLevelItems(model.treeItems())
        #
        for i in range(self.topLevelItemCount()):
            self.expandItem(self.topLevelItem(i))

    def _collapse(self, index):
        mip = self.modelIndexPath(index)
        mip.reverse()
        tv_index = self.modelIndex_(index)
        super(Widget_, self).collapse(tv_index)

    def collapse(self, index):
        super(Widget_, self).collapse(self.modelIndex_(index))

    def expand(self, index):
        super(Widget_, self).expand(self.modelIndex_(index))

    def modelIndex_(self, index):
        mip = self.modelIndexPath(index)
        mip.reverse()
        mi = QModelIndex()
        for i in mip:
            mi = self.model().index(i[0], i[1], mi)
        return mi

    @staticmethod
    def modelIndexPath(index):
        path = []
        i = index
        while (i.isValid()):
            path.append((i.row(), i.column()))
            i = i.parent()
        return path

class DataWidget(Widget_):
    def __init__(self, settings, model = None):
        super(DataWidget, self).__init__(settings)
        self.setHeader(DataHeaderView(self))
        self.setModel2(model)
        self.setColumnWidth(3, 100)
        self.setMaximumWidth(400)

    def drawBranches (self, painter, rect, index):
        super(DataWidget, self).drawBranches (painter, rect, index)
        y = (rect.top()+rect.bottom())/2
        painter.drawLine(rect.right()-20, y, rect.right(), y)

class GanttWidget(Widget_):
    def __init__(self, settings, model = None):
        super(GanttWidget, self).__init__(settings)
        self.setHeader(GanttHeaderView(self))
        self.setModel2(model)
        self.setColumnWidth(COLUMN_NAME, 0)
        self.setColumnWidth(COLUMN_CHART, self.preferableWidth())
        self.pen4chartBoundary = QPen(QColor(128,128,128,128))
        self.brush4chartFill = QBrush(QColor(0,64,64,128))
        self.brush4chartFillProgress = QBrush(QColor(255,0,0,128))
        self.cdi = None

    def preferableWidth(self):
        return self.xpos(self.model2.end+_ONEDAY)

    def xpos(self, dt):
        tdelta = dt - self.model2.start
        return tdelta.days * DAY_WIDTH

    def paintEvent(self, e):
        super(GanttWidget, self).paintEvent(e)
        print(e.rect())
        self.cdi = CalendarDrawingInfo()
        self.cdi.prepare(None, e.rect(), self.model2.start, self.model2.end + _ONEDAY)


    def drawRow(self, painter, options, index):
        """ガントチャート1行を描画する"""
        super(GanttWidget, self).drawRow(painter, options, index)
        item = self.itemFromIndex(index)
        task = item.data(COLUMN_CHART, Qt.UserRole)
        #rect = self.visualRect(index)
        itemRect = self.visualItemRect(item)
        print("\tdrawRow:", itemRect)
        #print("\tdrawRow:", self.visualItemRect(item))
        chartRect = self._chartRect(task, itemRect)
        self.drawItemBackground(painter, itemRect)
        self.drawChart(painter, task, chartRect)

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

class GanttFrame(QtGui.QSplitter):
    def __init__ (self, parent = None, model = None):
        super(GanttFrame, self).__init__(parent)
        self.settings = Settings()
        self.dataWidget = DataWidget(self.settings, model.dataModel)
        self.ganttWidget = GanttWidget(self.settings, model.ganttModel)
        self.addWidget(self.dataWidget)
        self.addWidget(self.ganttWidget)
        #-- シグナル/スロットの接続
        self.dataWidget.collapsed.connect(self.ganttWidget.collapse)
        self.ganttWidget.collapsed.connect(self.dataWidget.collapse)
        self.dataWidget.expanded.connect(self.ganttWidget.expand)
        self.ganttWidget.expanded.connect(self.dataWidget.expand)
        dw_vsb = self.dataWidget.verticalScrollBar()
        gw_vsb = self.ganttWidget.verticalScrollBar()
        dw_vsb.valueChanged .connect(gw_vsb.setSliderPosition )
        gw_vsb.valueChanged .connect(dw_vsb.setSliderPosition )
        #check_box.stateChanged.connect(self.print_state)
