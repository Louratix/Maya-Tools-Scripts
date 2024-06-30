import ControllerLibrary
from importlib import reload
reload(ControllerLibrary)
from Qt import QtWidgets, QtCore, QtGui
from maya import cmds
import pprint
import json

class ControllerLibraryUI(QtWidgets.QDialog):
    """
    The Controller library UI is a dialog that lets us save and import controllers    
    """

    def __init__(self):
        super(ControllerLibraryUI, self).__init__()
        
        self.setWindowTitle('Controller Library UI')

        #the library variable points to an instance of our controller library
        self.library = ControllerLibrary.ControllerLibrary()

        #every time we create a new instance, we will automatically build our UI and populatre it
        self.buildUI()
        self.populate()

        
    def buildUI(self):
        """this method builds out the UI"""
        
        #this is the master Layout
        layout = QtWidgets.QVBoxLayout(self)

        #this is the child horizontal widget
        saveWidget = QtWidgets.QWidget()
        saveLayout = QtWidgets.QHBoxLayout(saveWidget)
        layout.addWidget(saveWidget)

        self.saveNameField = QtWidgets.QLineEdit()
        saveLayout.addWidget(self.saveNameField)

        saveBtn = QtWidgets.QPushButton('save')
        saveBtn.clicked.connect(self.save)
        saveLayout.addWidget(saveBtn)

        #these are our Parameters for our thumbnail size 
        size = 64
        buffer = 12
        #this will create a grid list widget to display our controller thumbnails
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setViewMode(QtWidgets.QListWidget.IconMode)
        self.listWidget.setIconSize(QtCore.QSize(size, size))
        self.listWidget.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.listWidget.setGridSize(QtCore.QSize(size+buffer, size+buffer))
        layout.addWidget(self.listWidget)

        #this is our child widget that holds all the buttons
        btnWidget = QtWidgets.QWidget()
        btnLayout = QtWidgets.QHBoxLayout(btnWidget)
        layout.addWidget(btnWidget)

        importBtn = QtWidgets.QPushButton('Import')
        importBtn.clicked.connect(self.load)
        btnLayout.addWidget(importBtn)

        refreshBtn = QtWidgets.QPushButton('Refresh')
        refreshBtn.clicked.connect(self.populate)
        btnLayout.addWidget(refreshBtn)

        closeBtn = QtWidgets.QPushButton('Close')
        closeBtn.clicked.connect(self.close)
        btnLayout.addWidget(closeBtn)

    def populate(self):
        """this clears the list widget and then repopulates it with the contents of our library"""
        self.listWidget.clear()
        self.library.find()

        for name, info in self.library.items():
            item = QtWidgets.QListWidgetItem(name)
            self.listWidget.addItem(item)

            screenshot = info.get ('screenshot')
            if screenshot:
                icon = QtGui.QIcon(screenshot)
                item.setIcon(icon)

            item.setToolTip(pprint.pformat(info))

    def load(self):
        """this loads the currently selected controller"""
        CurrentItem = self.listWidget.currentItem()
        if not CurrentItem:
            return
        
        name = CurrentItem.text()
        self.library.load(name)

    def save(self):
        """this saves the controller with the given name"""
        name = self.saveNameField.text()
        if not name.strip():
            cmds.warning ("You must give a Name")
            return

        """for name, info in self.library.items():
            Name = info.get ('name')
            if Name == name:
                cmds.warning ("name already in use")
                return"""

        self.library.save(name)
        self.populate()

def showUI ():
    """
    this shows and returns a handle to the ui
    Returns:
        QDialog
    """
    ui = ControllerLibraryUI()
    ui.show()
    return ui