#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os, json
import sys
from PyQt4 import QtGui
from PyQt4.QtGui import QAction, QWidget, QVBoxLayout, QMenuBar, QFileDialog
from pygantt import TaskModel, Task, GanttWidget

def __SampleModel():
    model = TaskModel('サンプル工事', '2014/11/01', '2015/09/30')
    task = Task('たすく1', '2014/11/01', '2014/12/01', 1000, 600)
    task.add(Task('たすく1-1', '2014/12/01', '2015/03/01', 400, 200))
    task.add(Task('たすく1-2', '2014/12/10', '2014/12/31', 300, 100))
    task.add(Task('たすく1-3', '2015/01/01', '2015/01/18', 100, 80))
    model.add(task)
    task = Task('たすく2', '2014/11/01', '2014/12/01')
    task2_1 = task.add(Task('たすく2-1', '2014/11/01', '2014/12/01'))
    task2_1.add(Task('たすく2-1-1', '2014/11/01', '2014/11/10'))
    task2_1.add(Task('たすく2-1-2', '2014/11/05', '2014/11/20'))
    task2_1.add(Task('たすく2-1-3', '2014/11/18', '2014/12/01'))
    task.add(Task('たすく2-2', '2014/11/01', '2014/12/01'))
    task.add(Task('たすく2-3', '2014/11/01', '2014/12/01'))
    model.add(task)
    task = Task('たすく3', '2014/11/01', '2014/12/01')
    task.add(Task('たすく3-1', '2014/11/01', '2014/12/01'))
    task.add(Task('たすく3-2', '2014/11/01', '2014/12/01'))
    task.add(Task('たすく3-3', '2014/11/01', '2014/12/01'))
    model.add(task)
    print(TaskModel.dump(model, os.getcwd()+'\\hoge.json.txt'))
    return model

def SampleModel():
    path = os.getcwd()+'\\hoge.json.txt'
    model = TaskModel.load(path)
    TaskModel.dump(model, os.getcwd()+'\\hoge.json.txt.bak.txt')
    return model

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self._setup_gui()
        self._path = None
        self._workingDirectory = None

    def _setup_gui(self):
        #-- GUI部品の作成
        self.ganttWidget = GanttWidget()
        self.ganttWidget.ganttModel = SampleModel()
        self.main_frame = QWidget()
        #-- GUI部品のレイアウト
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.ganttWidget)
        main_layout.addWidget(self.ganttWidget.getChartScrollBar())
        self.main_frame.setLayout(main_layout)
        self.setCentralWidget(self.main_frame)
        #-- メニュー／アクションの作成
        self.createActions()
        self.createMenus()
        #-- その他(シグナル/スロットの接続とか)
        self.setWindowTitle("がんと")
        self.resize(1024, 768)

    def _createAction(self, name, func):
        action = QAction(name, self)
        action.triggered.connect(func)
        self.actions[name] = action

    def createActions(self):
        self.actions = {}
        self._createAction('Load', self.loadAction)
        self._createAction('Save', self.saveAction)
        self._createAction('Exit', self.exitAction)
        self._createAction('Insert', self.insertAction)
        self._createAction('Remove', self.removeAction)

    def createMenus(self):
        menuBar = self.menuBar()
        if True:
            fileMenu = menuBar.addMenu("File")
            fileMenu.addAction(self.actions['Load'])
            fileMenu.addAction(self.actions['Save'])
            fileMenu.addSeparator()
            fileMenu.addAction(self.actions['Exit'])
            editMenu = menuBar.addMenu("Edit")
            editMenu.addAction(self.actions['Insert'])
            editMenu.addAction(self.actions['Remove'])

    @property
    def path(self):
        return self._path

    @property
    def workingDirectory(self):
        if self._path is None:
            self._path = os.getcwd()
        return self._path

    #---------------------------------------------------------------------------
    #   アクション
    #---------------------------------------------------------------------------
    def loadAction(self):
        """ファイルを開く"""
        fileName = QFileDialog.getOpenFileName(self,
                        'ファイルを開く', self.workingDirectory)
        print("load %s" % fileName)
        if len(fileName) <= 0:
            return
        try:
            model = TaskModel.load(fileName)
            self._workingDirectory = os.path.dirname(fileName)
            self.ganttWidget.ganttModel = model
        except :
            print("Unexpected error:", sys.exc_info())
            QtGui.QMessageBox.warning(self,
                "がんと", "<%s>を開けませんでした" % fileName, "OK")

    def saveAction(self):
        print("save")
        print(json.dumps(SampleModel()))

    def exitAction(self):
        sys.exit()

    def insertAction(self):
        self.ganttWidget.insertAction()

    def removeAction(self):
        self.ganttWidget.removeAction()

def main():
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec_()

if __name__ == '__main__':
    main()
