from Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm
from functools import partial
import Qt
import logging
from maya import OpenMayaUI as omui
import json
import os
import time
import maya.cmds as cmds


logging.basicConfig()
logger = logging.getLogger('LightingManager')
logger.setLevel(logging.DEBUG)

if Qt.__binding__ == 'Pyside':
    logger.debug('Using Pyside with shiboken')
    from shiboken import wrapInstance
    from Qt.QtCore import Signal
elif Qt.__binding__.startswith('PyQt'):
    logger.debug('Using PyQt with Sip')
    from sip import wrapinstance as wrapInstance
    from Qt.QtCore import pyqtSignal as Signal
else:
    logger.debug('Using Pyside2 with shiboken')
    from shiboken2 import wrapInstance
    from Qt.QtCore import Signal

def getMayaMainWindow():
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(int(win), QtWidgets.QMainWindow)
    return ptr

def getDock(name = 'LightingManagerDock'):
    deleteDock(name)
    ctrl = pm.workspaceControl(name, dockToMainWindow = ('right', 1), label = "Lighting Manager")
    qtCtrl = omui.MQtUtil_findControl(ctrl)
    ptr = wrapInstance(int(qtCtrl), QtWidgets.QWidget)
    return ptr

def deleteDock(name = 'LightingManagerDock'):
    if pm.workspaceControl(name, query = True, exists = True):
        pm.deleteUI(name)

class lightmanager (QtWidgets.QWidget):

    '''add light name to carry in the save file?'''

    LightTypes = {
        "Point Light": pm.pointLight,
        "Spot Light": pm.spotLight,
        "Directional Light": pm.directionalLight,
        "Area Light": partial(pm.shadingNode, 'areaLight', asLight = True),
        "Volume Light": partial(pm.shadingNode, 'volumeLight', asLight = True)
    }


    def __init__(self, dock = True):
        if dock:
            parent = getDock()
        else:
            deleteDock()

            try:
                pm.deleteUI('LightingManager')
            except:
                logger.debug('No previous UI exist')
            parent = QtWidgets.QDialog(parent = getMayaMainWindow())
            parent.setObjectName ('LightingManager')
            parent.setWindowTitle('Lighting Manager')
            layout = QtWidgets.QVBoxLayout(parent)

        super(lightmanager, self).__init__(parent = parent)
        self.BuildUI()
        self.Populate()
        self.parent().layout().addWidget(self)
        if not dock:
            parent.show()

    def Populate(self):
        while self.scrollLayout.count():
            widget = self.scrollLayout.takeAt(0).widget()
            if widget:
                widget.setVisible(False)
                widget.deleteLater()

        for light in pm.ls(type=["areaLight", "spotLight", "pointLight", "directionalLight", "volumeLight"]):
            self.AddLight(light)

    def BuildUI(self):
        layout = QtWidgets.QGridLayout(self)

        self.lightTypeCB = QtWidgets.QComboBox()
        for lightType in sorted(self.LightTypes):
            self.lightTypeCB.addItem(lightType)
        layout.addWidget(self.lightTypeCB, 0, 0, 1, 2)

        createBtn = QtWidgets.QPushButton("create")
        createBtn.clicked.connect(self.CreateLight)
        layout.addWidget(createBtn, 0, 2)

        scrollWidget = QtWidgets.QWidget()
        scrollWidget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.scrollLayout = QtWidgets.QVBoxLayout(scrollWidget)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollWidget)
        layout.addWidget(scrollArea, 1, 0, 1, 3)

        saveBtn = QtWidgets.QPushButton('Save')
        saveBtn.clicked.connect(self.saveLights)
        layout.addWidget(saveBtn, 2, 0)

        importBtn = QtWidgets.QPushButton('Import')
        importBtn.clicked.connect(self.importLights)
        layout.addWidget(importBtn, 2, 1)

        refreshBtn = QtWidgets.QPushButton("Refresh")
        refreshBtn.clicked.connect(self.Populate)
        layout.addWidget(refreshBtn, 2, 2)

    def saveLights(self):
        properties = {}

        for lightWidget in self.findChildren(lightwidget):
            light = lightWidget.light
            transform = light.getTransform()

            properties[str(transform)] = {
                'translate': list(transform.translate.get()),
                'rotation':list(transform.rotate.get()),
                'lightType':pm.objectType(light),
                'intensity':light.intensity.get(),
                'color':light.color.get(),
                'name':str(transform)
            }
        
        print (properties)

        directory = self.getDirectory()

        result = cmds.promptDialog(
                title='Save',
                message='Please select a Name for the SaveFile',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == 'OK':
            choice = cmds.promptDialog(query=True, text=True)
            choice += ".json"

            lightFile = os.path.join(directory, choice)
            with open (lightFile, 'w') as f:
                json.dump(properties, f, indent = 4)
        
        logger.info('Saving file to %s' % lightFile)

    def getDirectory(self):
        directory = os.path.join(pm.internalVar(userAppDir = True), 'lightManager')
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory

    def importLights(self):
        directory = self.getDirectory()
        fileName = QtWidgets.QFileDialog.getOpenFileName(self, "Light Browser", directory)
        with open (fileName[0], 'r') as f:
            properties = json.load(f)

        for light, info in properties.items():
            lightType = info.get('lightType')
            for lt in self.LightTypes:
                if ('%sLight' % lt.split()[0].lower()) == lightType:
                    print (lt)
                    break
            else:
                logger.info('Cannot find a corresponding light type for %s (%s)' % (light, lightType))
                continue

            light = self.CreateLight(lightType = lt)

            light.intensity.set(info.get('intensity'))
            light.color.set(info.get('color'))
            transform = light.getTransform()
            transform.translate.set(info.get('translate'))
            transform.rotate.set(info.get('rotation'))
            transform.rename(info.get('name'))

        self.Populate()

    def CreateLight(self, lightType = None, add = True):
        if not lightType:
            lightType = self.lightTypeCB.currentText()
        F = self.LightTypes[lightType]

        light = F()
        if add:
            self.AddLight(light)

            return light

    
    def AddLight(self, light):
        widget = lightwidget(light)
        self.scrollLayout.addWidget(widget)
        widget.onSolo.connect(self.onSolo)

    def onSolo(self, value):
        lightwidgets = self.findChildren(lightwidget)
        
        for widgets in lightwidgets:
            if widgets != self.sender():
                widgets.DisableLight(value)

class lightwidget (QtWidgets.QWidget):

    onSolo = Signal(bool)

    def __init__(self, light):
        super(lightwidget, self).__init__()
        if isinstance(light, str):
            light = pm.PyNode (light)
        if isinstance(light, pm.nodetypes.Transform):
            light = light.getShape()

        self.light = light
        self.BuildUI()


    def BuildUI(self):
        layout = QtWidgets.QGridLayout(self)

        self.name = QtWidgets.QCheckBox(str(self.light.getTransform()))
        self.name.setChecked(self.light.visibility.get())
        self.name.toggled.connect(lambda val: self.light.getTransform().visibility.set (val))
        layout.addWidget(self.name, 0, 0)

        soloBtn = QtWidgets.QPushButton('Solo')
        soloBtn.setCheckable(True)
        soloBtn.toggled.connect(lambda val: self.onSolo.emit(val))
        layout.addWidget(soloBtn, 0, 1)

        deleteBtn = QtWidgets.QPushButton('X')
        deleteBtn.clicked.connect(self.DeleteLight)
        deleteBtn.setMaximumWidth(10)
        layout.addWidget(deleteBtn, 0, 2)

        intensity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        intensity.setMinimum(1)
        intensity.setMaximum(2000)
        intensity.setValue(self.light.intensity.get())
        intensity.valueChanged.connect(lambda val: self.light.intensity.set(val))
        layout.addWidget(intensity, 1, 0, 1, 2)

        self.colorBtn = QtWidgets.QPushButton()
        self.colorBtn.setMaximumWidth(20)
        self.colorBtn.setMaximumHeight(20)
        self.SetBtnColor()
        self.colorBtn.clicked.connect(self.SetColor)
        layout.addWidget(self.colorBtn, 1, 2)

    def SetBtnColor(self, color = None):
        if not color:
            color = self.light.color.get()
        
        assert len(color) == 3, 'You must provide a list of 3 colors.'

        r,g,b = [c*255 for c in color]

        self.colorBtn.setStyleSheet('background-color: rgba(%s, %s, %s, 1.0)' % (r, g, b))

    def SetColor(self):
        lightColor = self.light.color.get()
        color = pm.colorEditor(rgbValue = lightColor)

        r,g,b,a = [float(c) for c in color.split()]
        color = (r,g,b)

        self.light.color.set(color)
        self.SetBtnColor(color)


    def DisableLight(self, value):
        self.name.setChecked(not value)

    def DeleteLight(self):
        self.setParent(None)
        self.setVisible(False)
        self.deleteLater()

        pm.delete(self.light.getTransform())


def showUI():
    ui = lightmanager()
    ui.show()
    return ui