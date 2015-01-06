#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import os, json
import sys
from PyQt4 import QtGui
from PyQt4.QtGui import QAction, QWidget, QVBoxLayout, QMenuBar, QFileDialog
from pygantt import TaskModel, Task, GanttFrame

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
    import os
    print(TaskModel.dump(model, os.getcwd()+'\\hoge.json.txt'))
    return model

def SampleModel():
    import os
    path = os.getcwd()+'\\hoge.json.txt'
    model = TaskModel.load(path)
    TaskModel.dump(model, os.getcwd()+'\\hoge.json.txt.bak.txt')
    return model

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self._setup_gui()


    def _setup_gui(self):
        self.setWindowTitle("がんと")
        #-- GUI部品の作成
        hello_button = QtGui.QPushButton("波浪わーるど")
        check_box = QtGui.QCheckBox("Check Box")
        #-- GUI部品のレイアウト
        main_layout = QVBoxLayout()
        self.ganttFrame = GanttFrame(model = SampleModel())
        main_layout.addWidget(self.ganttFrame)
        main_layout.addWidget(hello_button)
        main_layout.addWidget(check_box)
        self.main_frame = QWidget()
        self.main_frame.setLayout(main_layout)
        self.setCentralWidget(self.main_frame)
        self.createActions()
        self.createMenus()
        #-- シグナル/スロットの接続
        hello_button.clicked.connect(self.on_click)
        check_box.stateChanged.connect(self.print_state)
        #
        self.resize(1024, 768)

    def on_click(self):
        print("Hello World")

    def print_state(self, state):
        if state == 0:
            print("Unchecked")
        else:
            print("Checked")

    def createActions(self):
        self.actions = {}
        self.actions['load'] = QAction("Load", self)
        self.actions['load'].triggered.connect(self.loadAction)
        self.actions['save'] = QAction("Save", self)
        self.actions['save'].triggered.connect(self.saveAction)
        self.actions['exit'] = QAction("Exit", self)
        self.actions['exit'].triggered.connect(self.exitAction)

    def createMenus(self):
        menuBar = self.menuBar()
        if True:
            fileMenu = menuBar.addMenu("File")
            fileMenu.addAction(self.actions['load'])
            fileMenu.addAction(self.actions['save'])
            fileMenu.addSeparator()
            fileMenu.addAction("Exit")
            editMenu = menuBar.addMenu("Edit")
            editMenu.addAction(self.actions['load'])
            editMenu.addAction(self.actions['save'])
            editMenu.addSeparator()
            editMenu.addAction(self.actions['exit'])

    def loadAction(self):
        fileName = QFileDialog.getOpenFileName(self, 'ファイルを開く', os.getcwd())
        print("load %s" % fileName)
        model = TaskModel.load(fileName)
        self.ganttFrame.ganttModel = model

    def saveAction(self):
        print("save")
        print(json.dumps(SampleModel()))

    def exitAction(self):
        sys.exit()


def main():
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec_()

if __name__ == '__main__':
    main()
