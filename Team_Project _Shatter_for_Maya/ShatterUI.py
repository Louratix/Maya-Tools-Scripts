from asyncio.windows_events import NULL
import logging
import maya.cmds as cmds # type: ignore
from maya import OpenMayaUI as omui # type: ignore
import random

Version = cmds.about(version=True) 

logging.basicConfig()
logger = logging.getLogger('Shatter Tool')
logger.setLevel(logging.DEBUG)

if int(Version) < 2025:
    import Qt
    from Qt import QtWidgets, QtCore, QtGui
    if Qt.__binding__ == 'Pyside':
        logger.debug('Using Pyside with shiboken')
        from shiboken import wrapInstance # type: ignore
        from Qt.QtCore import Signal # type: ignore
    elif Qt.__binding__.startswith('PyQt'):
        logger.debug('Using PyQt with Sip')
        from sip import wrapinstance as wrapInstance # type: ignore
        from Qt.QtCore import pyqtSignal as Signal # type: ignore
    else:
        logger.debug('Using Pyside2 with shiboken2')
        from shiboken2 import wrapInstance # type: ignore
        from Qt.QtCore import Signal # type: ignore
else:
    logger.debug('Using Pyside6 with shiboken6')
    from PySide6.QtCore import Qt # type: ignore
    from PySide6 import QtCore, QtWidgets, QtGui # type: ignore
    from shiboken6 import wrapInstance # type: ignore
    from PySide6.QtCore import Signal # type: ignore

def getMayaMainWindow():
    if int(Version) < 2025:
        win = omui.MQtUtil_mainWindow()
        ptr = wrapInstance(int(win), QtWidgets.QMainWindow)
        return ptr
    else:
        win = omui.MQtUtil.mainWindow()
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
        self.DeformSlider.setSingleStep(2)
        self.DeformSlider.setMinimum(0)
        self.DeformSlider.setMaximum(5)
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
            self.ToShatter = self.GetMesh()
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
            cmds.polySeparate( self.ToShatter )


    def Copy(self):
        selected = self.GetMesh()
        NewlyCopied = []
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
            if "Plane" in item:
                SubdiW = cmds.getAttr("%s.subdivisionsWidth" % Poly)
                #SubdiD = cmds.getAttr("%s.subdivisionsDepth" % Poly)
                SubdiH = cmds.getAttr("%s.subdivisionsHeight" % Poly)
                Height = cmds.getAttr("%s.height" % Poly)

                newCube = cmds.polyPlane()
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
                #cmds.setAttr(newCube[1] + ".subdivisionsDepth", SubdiD)
                cmds.setAttr(newCube[1] + ".subdivisionsHeight", SubdiH)
                cmds.setAttr(newCube[1] + ".height", Height)
                self.CutMesh[newCube[0]] = newCube[1]
                NewlyCopied.append(newCube[0])

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
                NewlyCopied.append(newSphere[0])
        print (NewlyCopied)
        cmds.select(NewlyCopied)


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
        """add subdivision to selected Cutting Mesh"""
        sel = self.GetMesh()
        ShatterList = []
        for item in sel:
            cmds.polyExtrudeFacet (item, tk = 0.001)
            if item in self.CutMesh:
                ShatterList.append(item)
        CutMesh = cmds.polyCBoolOp( self.ToShatter, ShatterList, op=2, n=str(self.ToShatter))
        self.ToShatter = CutMesh[0]
        cmds.delete(self.ToShatter,constructionHistory = True)  
            

    def Deform(self,Deformation):
        #Deformation = Deformation * 0.1
        sel = cmds.ls(sl=True, o=True)
        for item in sel:
            NumVer = cmds.polyEvaluate( v=True)
            Vertex = 0
            itemSTR = self.CutMesh[item]
            if "Plane" in item:
                while Vertex < NumVer:
                    cmds.setAttr ("pPlaneShape" + str(int(''.join(filter(str.isdigit, itemSTR)))) + ".pnts[" + str(Vertex) + "]" + ".pnty", random.randint(0, Deformation)*0.02)
                    Vertex = Vertex + 2
            elif "Sphere" in item:
                while Vertex < NumVer:
                    cmds.setAttr ("pSphereShape" + str(int(''.join(filter(str.isdigit, itemSTR)))) + ".pnts[" + str(Vertex) + "]" + ".pnty", random.randint(0, Deformation)*0.03)
                    cmds.setAttr ("pSphereShape" + str(int(''.join(filter(str.isdigit, itemSTR)))) + ".pnts[" + str(Vertex) + "]" + ".pntx", random.randint(0, Deformation)*0.03)
                    Vertex = Vertex + 2



    def Subdivise(self,Subdivisions):
        selected = self.GetMesh()
        for item in selected:
            Poly = self.CutMesh[item]
            if 'Plane' in item:
                cmds.setAttr( Poly + ".subdivisionsWidth", Subdivisions)
                cmds.setAttr( Poly + ".subdivisionsHeight", Subdivisions)
            else:
                if Subdivisions < 4:
                    return
                cmds.setAttr( Poly + ".subdivisionsHeight", Subdivisions)



    """Add a plane to cut into the mesh"""
    def AddPlane(self):
        plane = cmds.polyPlane( w=1,sx=1, sy=1, h=1)
        self.CutMesh[plane[0]] = plane[1]

    def AddSphere(self):
        sphere = cmds.polySphere( sx=10, sy=10, r=1)
        self.CutMesh[sphere[0]] = sphere[1]
    


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