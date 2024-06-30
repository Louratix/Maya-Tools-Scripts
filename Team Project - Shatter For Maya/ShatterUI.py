from asyncio.windows_events import NULL
from queue import Empty
from Qt import QtWidgets, QtCore, QtGui
import Qt
import logging
import maya.cmds as cmds
from maya import OpenMayaUI as omui

logging.basicConfig()
logger = logging.getLogger('Shatter Tool')
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


class ShatterUI (QtWidgets.QWidget):
    """
    Basic UI that creates a shape to Cut Mesh a certain way
    """

    def __init__ (self):

        parent = QtWidgets.QDialog(parent = getMayaMainWindow())
        parent.setObjectName ('Shatter Tool')
        parent.setWindowTitle('Shatter Tool')
        layout = QtWidgets.QVBoxLayout(parent)
 
        super(ShatterUI, self).__init__(parent = parent)
        self.BuildUI()
        self.parent().layout().addWidget(self)

        parent.show()


    def BuildUI(self):
        layout = QtWidgets.QGridLayout(self)

        self.HistoryBtn = QtWidgets.QPushButton("Delete History")
        self.HistoryBtn.clicked.connect(self.DeleteHistory)
        layout.addWidget(self.HistoryBtn, 0, 1)

        self.DuplicateBtn = QtWidgets.QPushButton("Duplicate Object")
        self.DuplicateBtn.clicked.connect(self.Duplicate)
        layout.addWidget(self.DuplicateBtn, 0, 2)

        self.CenterBtn = QtWidgets.QPushButton("Center + Freeze")
        self.CenterBtn.clicked.connect(self.MoveToCenter)
        layout.addWidget(self.CenterBtn, 0, 3)

        self.AddPlaneBtn = QtWidgets.QPushButton("Add Plane")
        self.AddPlaneBtn.clicked.connect(self.AddPlane)
        self.AddPlaneBtn.setDisabled(True)
        layout.addWidget(self.AddPlaneBtn,2,2)

        self.AddSphereBtn = QtWidgets.QPushButton("Add Sphere")
        self.AddSphereBtn.clicked.connect(self.AddSphere)
        self.AddSphereBtn.setDisabled(True)
        layout.addWidget(self.AddSphereBtn,2,1)

        self.ToggleXRBTN = QtWidgets.QPushButton("Toggle XRay")
        self.ToggleXRBTN.clicked.connect(self.ToggleXR)
        layout.addWidget(self.ToggleXRBTN,2,3)

        self.SubSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        layout.addWidget(self.SubSlider,3,2)

        self.StartStopBtn = QtWidgets.QPushButton("START")
        self.StartStopBtn.setCheckable(True)
        self.StartStopBtn.clicked.connect(self.toggle)
        self.StartStopBtn.setStyleSheet("background-color : green")
        layout.addWidget(self.StartStopBtn,1,1,1,3)


    def toggle(self):       
        if self.StartStopBtn.isChecked():
            ToShatter = self.GetMesh()
            self.StartStopBtn.setText("STOP")
            self.StartStopBtn.setStyleSheet("QPushButton:checked {background-color: red; border: red;  min-height: 1.8em;}")
            self.CenterBtn.setDisabled(True)
            self.DuplicateBtn.setDisabled(True)
            self.HistoryBtn.setDisabled(True)
            self.AddSphereBtn.setDisabled(False)
            self.AddPlaneBtn.setDisabled(False)
            cmds.displaySurface(xRay=True)
        else:
            self.StartStopBtn.setText("Start")
            self.StartStopBtn.setStyleSheet("background-color : green")
            self.CenterBtn.setDisabled(False)
            self.DuplicateBtn.setDisabled(False)
            self.HistoryBtn.setDisabled(False)
            self.AddSphereBtn.setDisabled(True)
            self.AddPlaneBtn.setDisabled(True)
            cmds.displaySurface(xRay=False)
            

    """Add a plane to cut into the mesh"""
    def AddPlane(self):
        cmds.polyCube( sx=1, sy=1, sz=1, h=0.01)

    def AddSphere(self):
        cmds.polySphere( sx=10, sy=10, r=1)

    def ToggleXR(self):
        if cmds.displaySurface( xRay=True):
            cmds.displaySurface( xRay=False)
        else:
            cmds.displaySurface( xRay=True)



    """Moves Selected Mesh to World Center"""
    def MoveToCenter(self):
        ToMove = self.GetMesh()
        cmds.move (0, 0, 0, ToMove, rpr=True, a=True)
        cmds.makeIdentity (ToMove, a = True, t = True, r = True,s = True, n = False, pn =True)


    """Duplicates Selected Mesh and adds 'Shatter' to the name"""
    def Duplicate(self):
        ToDuplicate = self.GetMesh()
        cmds.duplicate (ToDuplicate)
        cmds.hide (ToDuplicate)
        ToRename = self.GetMesh()
        NewName = ToRename[0] + "_" + "shatter"
        cmds.rename(ToRename, NewName)

    """Deletes History"""
    def DeleteHistory(self):
        toDelete = self.GetMesh()
        cmds.delete(toDelete,constructionHistory = True)
        print ("History Deleted")

    def GetMesh(self):
        Selected = cmds.ls(selection = True)
        if not Selected:
            raise RuntimeError ("nothing is selected")
        return Selected