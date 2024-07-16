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
        self.DeformLabel = QtWidgets.QLabel("Deform Value 0")
        self.DeformSlider.setMinimum(0)
        self.DeformSlider.setMaximum(10)
        self.DeformSlider.setSingleStep(2)
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
        self.Deform(value)
        


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
            self.CutMesh = {}

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
        selected = self.GetMesh()
        for item in selected:
            Poly = self.CutMesh[item]
            translate_x = cmds.getAttr("%s.translateX" % item)
            translate_y = cmds.getAttr("%s.translateY" % item)
            translate_z = cmds.getAttr("%s.translateZ" % item)
            scale_x = cmds.getAttr("%s.scaleX" % item)
            scale_y = cmds.getAttr("%s.scaleY" % item)
            scale_z = cmds.getAttr("%s.scaleZ" % item)
            rotate_x = cmds.getAttr("%s.rotateX" % item)
            rotate_y = cmds.getAttr("%s.rotateY" % item)
            rotate_z = cmds.getAttr("%s.rotateZ" % item)
            if "Cube" in item:
                SubdiW = cmds.getAttr("%s.subdivisionsWidth" % Poly)
                SubdiD = cmds.getAttr("%s.subdivisionsDepth" % Poly)
                SubdiH = cmds.getAttr("%s.subdivisionsHeight" % Poly)
                Height = cmds.getAttr("%s.height" % Poly)

                newCube = cmds.polyCube()
                cmds.setAttr(newCube[0] + ".translateX", translate_x)
                cmds.setAttr(newCube[0] + ".translateY", translate_y)
                cmds.setAttr(newCube[0] + ".translateZ", translate_z)
                cmds.setAttr(newCube[0] + ".scaleX", scale_x)
                cmds.setAttr(newCube[0] + ".scaleY", scale_y)
                cmds.setAttr(newCube[0] + ".scaleZ", scale_z)
                cmds.setAttr(newCube[0] + ".rotateX", rotate_x)
                cmds.setAttr(newCube[0] + ".rotateY", rotate_y)
                cmds.setAttr(newCube[0] + ".rotateZ", rotate_z)
                cmds.setAttr(newCube[1] + ".subdivisionsWidth", SubdiW)
                cmds.setAttr(newCube[1] + ".subdivisionsDepth", SubdiD)
                cmds.setAttr(newCube[1] + ".subdivisionsHeight", SubdiH)
                cmds.setAttr(newCube[1] + ".height", Height)
                self.CutMesh[newCube[0]] = newCube[1]

            elif "Sphere" in item:
                SubdiH = cmds.getAttr("%s.subdivisionsHeight" % Poly)
                SubdiA = cmds.getAttr("%s.subdivisionsAxis" % Poly)

                newSphere = cmds.polySphere()
                cmds.setAttr(newSphere[0] + ".translateX", translate_x)
                cmds.setAttr(newSphere[0] + ".translateY", translate_y)
                cmds.setAttr(newSphere[0] + ".translateZ", translate_z)
                cmds.setAttr(newSphere[0] + ".scaleX", scale_x)
                cmds.setAttr(newSphere[0] + ".scaleY", scale_y)
                cmds.setAttr(newSphere[0] + ".scaleZ", scale_z)
                cmds.setAttr(newSphere[0] + ".rotateX", rotate_x)
                cmds.setAttr(newSphere[0] + ".rotateY", rotate_y)
                cmds.setAttr(newSphere[0] + ".rotateZ", rotate_z)
                cmds.setAttr(newSphere[1] + ".subdivisionsHeight", SubdiH)
                cmds.setAttr(newSphere[1] + ".subdivisionsAxis", SubdiA)
                self.CutMesh[newSphere[0]] = newSphere[1]

                cmds.polyExtrudeFacet (newSphere, tk = 0.01)
                cmds.select(newSphere)


    """Deletes Selected Cutting Meshes"""
    def Delete(self):
        select = self.GetMesh()
        count = 0
        for items in select:
            ToDelete = select[count]
            if ToDelete in self.CutMesh:
                self.CutMesh.pop(ToDelete)
                print(ToDelete + " is Deleted")
            count = count + 1
        print (self.CutMesh)
        cmds.delete()


    def cut(self):
        print('test')
    """add subdivision to selected Cutting Mesh"""

    def Deform(self,Deformation):
        sel = cmds.ls(sl=True, o=True)[0]
        sel_vtx = cmds.ls('{}.vtx[:]'.format(sel), fl=True)
        #cmds.move(0,Deformation,0, sel_vtx[0], r = True)
        cmds.setAttr ("pCubeShape1.pnts[5].pnty", Deformation)
        print (sel_vtx)
        """for item in sel:
            sel_vtx = cmds.ls('{}.vtx[:]'.format(sel), fl=True)
            for vtx in sel_vtx:
                cmds.move(0,Deformation,0, vtx)"""


    def Subdivise(self,Subdivisions):
        selected = self.GetMesh()
        for item in selected:
            Poly = self.CutMesh[item]
            if 'Cube' in item:
                cmds.setAttr( Poly + ".subdivisionsWidth", Subdivisions)
                cmds.setAttr( Poly + ".subdivisionsDepth", Subdivisions)
            else:
                if Subdivisions < 4:
                    return
                cmds.setAttr( Poly + ".subdivisionsHeight", Subdivisions)



    """Add a plane to cut into the mesh"""
    def AddPlane(self):
        plane = cmds.polyCube( w=1,sx=1, sy=1, sz=1, h=0.01)
        self.CutMesh[plane[0]] = plane[1]

    def AddSphere(self):
        sphere = cmds.polySphere( sx=10, sy=10, r=1)
        self.CutMesh[sphere[0]] = sphere[1]
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