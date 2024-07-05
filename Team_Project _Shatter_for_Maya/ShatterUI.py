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

        self.DeformSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.DeformLabel = QtWidgets.QLabel("Deform Value 1")
        self.DeformSlider.setMinimum(1)
        self.DeformSlider.setMaximum(100)
        layout.addWidget(self.DeformLabel,3,1)
        layout.addWidget(self.DeformSlider,3,2,1,2)
        self.DeformSlider.valueChanged.connect(self.update_Deform)

        self.SubSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.SubLabel = QtWidgets.QLabel("Subdiv Value 1")
        self.SubSlider.setMinimum(1)
        self.SubSlider.setMaximum(10)
        layout.addWidget(self.SubLabel,4,1)
        layout.addWidget(self.SubSlider,4,2,1,2)
        self.SubSlider.valueChanged.connect(self.update_Sub)

        self.StartStopBtn = QtWidgets.QPushButton("START")
        self.StartStopBtn.setCheckable(True)
        self.StartStopBtn.clicked.connect(self.toggle)
        self.StartStopBtn.setStyleSheet("background-color : green")
        layout.addWidget(self.StartStopBtn,1,1,1,3)

        self.CutBtn = QtWidgets.QPushButton("CUT")
        self.CutBtn.clicked.connect(self.cut)
        self.CutBtn.setStyleSheet("QPushButton:Disabled {background-color: darkslategrey; color: grey}")
        self.CutBtn.setDisabled(True)
        layout.addWidget(self.CutBtn,5,1)

        self.CopyBtn = QtWidgets.QPushButton("Copy")
        self.CopyBtn.clicked.connect(self.Copy)
        self.CopyBtn.setDisabled(True)
        layout.addWidget(self.CopyBtn,5,2)

        self.DeleteBtn = QtWidgets.QPushButton("Delete")
        self.DeleteBtn.clicked.connect(self.Delete)
        self.DeleteBtn.setDisabled(True)
        layout.addWidget(self.DeleteBtn,5,3)

    """Updating the Sliders"""
    def update_Sub(self):
        value = self.SubSlider.value()
        self.SubLabel.setText(f"Subdiv Value: {value}")
        self.Subdivise(value)

    def update_Deform(self):
        value = self.DeformSlider.value()
        self.DeformLabel.setText(f"Deform Value: {value}")
        


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
            self.DeleteBtn.setDisabled(False)
            self.CutBtn.setDisabled(False)
            self.CutBtn.setStyleSheet("background-color: darkturquoise;")
            self.CopyBtn.setDisabled(False)
            self.CutMesh = []

            #cmds.createDisplayLayer(name = "Shatter")

        else:
            self.StartStopBtn.setText("Start")
            self.StartStopBtn.setStyleSheet("background-color : green")
            self.CenterBtn.setDisabled(False)
            self.DuplicateBtn.setDisabled(False)
            self.HistoryBtn.setDisabled(False)
            self.AddSphereBtn.setDisabled(True)
            self.AddPlaneBtn.setDisabled(True)
            self.DeleteBtn.setDisabled(True)
            self.CutBtn.setStyleSheet("QPushButton:Disabled {background-color: darkslategrey; color: grey}")
            self.CutBtn.setDisabled(True)
            self.CopyBtn.setDisabled(True)


    def Copy(self):
        print("test Copy")

    """Deletes Selected Cutting Meshes"""
    def Delete(self):
        select = self.GetMesh()
        count = 0
        for items in select:
            ToDelete = select[count]
            if ToDelete in self.CutMesh:
                self.CutMesh.remove(ToDelete)
                print(ToDelete + " is Deleted")
            count = count + 1
        cmds.delete()


    def cut(self):
        print('test')
    """add subdivision to selected Cutting Mesh"""

    def Subdivise(self,Subdivisions):
        selected = cmds.ls(selection = True)
        print(selected)
        selectedSTR = selected[0]
        #cmds.polySubdivideFacet( selected, dv=Subdivisions )
        if 'Cube' in selected[0]:
            cmds.setAttr( "polyCube" + selectedSTR[-1] + ".subdivisionsWidth", Subdivisions)
            cmds.setAttr( "polyCube" + selectedSTR[-1] + ".subdivisionsDepth", Subdivisions)
        else:
            cmds.setAttr( "polySphere" + selectedSTR[-1] + ".subdivisionsHeight", Subdivisions)



    """Add a plane to cut into the mesh"""
    def AddPlane(self):
        plane = cmds.polyCube( w=1,sx=1, sy=1, sz=1, h=0.01)
        self.CutMesh.append(plane[0])
        print (self.CutMesh)

    def AddSphere(self):
        sphere = cmds.polySphere( sx=10, sy=10, r=1)
        self.CutMesh.append(sphere[0])
        print (self.CutMesh)
        cmds.polyExtrudeFacet (sphere, tk = 0.01)
        cmds.select(sphere)


    """Toggles XR View ON or OFF"""
    def ToggleXR(self):
        Panel = ["1", "2", "3", "4"]
        length = len(Panel)
        for obj in range(length):
            result = cmds.modelEditor('modelPanel' + Panel[obj], q=True, xr=True,wireframeOnShaded = True)
            cmds.modelEditor('modelPanel' + Panel[obj], e=True, xr=not result, wireframeOnShaded =not result)


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
            raise RuntimeError ("Nothing is selected")
        return Selected