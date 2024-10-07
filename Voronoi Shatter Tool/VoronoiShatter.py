#from asyncio.windows_events import NULL
import logging
import maya.cmds as cmds # type: ignore
from maya import OpenMayaUI as omui # type: ignore
import random

Version = cmds.about(version=True) 

logging.basicConfig()
logger = logging.getLogger('Voronoi Shatter Tool')
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


class VoronoiShatterUI (QtWidgets.QWidget):
    """
    Basic UI that creates a shape to Cut Mesh a certain way
    """

    def __init__ (self):

        parent = QtWidgets.QDialog(parent = getMayaMainWindow())
        parent.setObjectName ('Voronoi Shatter Tool')
        parent.setWindowTitle('Voronoi Shatter Tool')
        layout = QtWidgets.QVBoxLayout(parent)
 
        super(VoronoiShatterUI, self).__init__(parent = parent)
        self.BuildUI()
        self.parent().layout().addWidget(self)

        parent.show()


    def BuildUI(self):
        self.layout = QtWidgets.QGridLayout(self)

        self.ChunksSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.ChunkLabel = QtWidgets.QLabel("Chunks Amount 1")
        self.ChunksSlider.setMinimum(1)
        self.ChunksSlider.setMaximum(100)
        self.layout.addWidget(self.ChunkLabel,0,0)
        self.layout.addWidget(self.ChunksSlider,0,2)
        self.ChunksSlider.valueChanged.connect(self.update_chunks)

        self.CheckFillHole = QtWidgets.QCheckBox()
        self.CheckFillHoleLabel = QtWidgets.QLabel("Fill Holes:")
        self.CheckFillHole.stateChanged.connect(self.switch)
        self.layout.addWidget(self.CheckFillHoleLabel,1,0)
        self.layout.addWidget(self.CheckFillHole,1,1)
        

        self.TextureLabel = QtWidgets.QLabel("Texture to Fill:")
        self.TextureLabel.setDisabled(True)
        self.SelectTexture = QtWidgets.QComboBox()
        self.SelectTexture.addItem("Default")
        self.SelectTexture.addItems(self.selectTexture())
        self.SelectTexture.setDisabled(True)
        self.SelectTexture.activated.connect(self.SetIcon)
        self.TextureIcon = QtWidgets.QListWidget()
        self.TextureIcon.setViewMode(QtWidgets.QListWidget.IconMode)
        self.TextureIcon.setIconSize(QtCore.QSize(32, 32))
        self.TextureIcon.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.layout.addWidget(self.TextureLabel,2,0)
        self.layout.addWidget(self.SelectTexture,2,1)
        

        self.StartStopBtn = QtWidgets.QPushButton("START")
        self.StartStopBtn.clicked.connect(self.Start)
        self.StartStopBtn.setStyleSheet("background-color : green")
        self.layout.addWidget(self.StartStopBtn,3,0,1,3)


    def switch(self):
        if (self.CheckFillHole.isChecked() == True):
            self.TextureLabel.setDisabled(False)
            self.SelectTexture.setDisabled(False)
        else:
            self.TextureLabel.setDisabled(True)
            self.SelectTexture.setDisabled(True)

    def update_chunks(self):
        value = self.ChunksSlider.value()
        self.ChunkLabel.setText(f"Subdiv Value: {value}")
        #self.Subdivise(value)

    def Start(self):
        #value = self.ChunksSlider.value()
        ToCut = self.GetMesh()
        BoundingBox = cmds.exactWorldBoundingBox(ToCut)

        PointsCount = self.ChunksSlider.value()
        VoroX = [random.uniform(BoundingBox[0], BoundingBox[3]) for i in range(PointsCount)]
        VoroY = [random.uniform(BoundingBox[1], BoundingBox[4]) for i in range(PointsCount)]
        VoroZ = [random.uniform(BoundingBox[2], BoundingBox[5]) for i in range(PointsCount)]
        voroPoints = zip(VoroX,VoroY,VoroZ)

        cmds.setAttr(str(ToCut) + '.visibility', 0)
        chunksGrp = cmds.group(em = True, name = ToCut + '_Chunks_1')
        
        for ToCopies in voroPoints:
            Copies = cmds.duplicate(ToCut)
            cmds.setAttr(str(Copies[0]) + '.visibility', 1)
            cmds.parent(Copies, chunksGrp)

            for VoroCut in zip(VoroX,VoroY,VoroZ):
                if ToCopies != VoroCut:
                    aim = [(vec1 - vec2) for  (vec1, vec2) in zip(ToCopies, VoroCut)]
                    VoroCenter = [(vec1 + vec2)/2 for (vec1, vec2) in zip(VoroCut, ToCopies)]
                    planeAngle = cmds.angleBetween (euler = True, v1 = [0,0,1], v2 = aim)
                    cmds.polyCut(Copies[0], df = True, cutPlaneCenter = VoroCenter, cutPlaneRotate = planeAngle)

                    oriFaces = cmds.polyEvaluate(Copies[0], face = True)
                    cmds.polyCloseBorder(Copies[0], ch = False)
                    aftFaces = cmds.polyEvaluate(Copies[0], face = True)
                    newFaces = aftFaces - oriFaces

                    cutFaces = ('%s.f[%d]' % (Copies[0], (aftFaces + newFaces - 1)))
                    mat = self.SelectTexture.currentText()
                    shading_engine = cmds.sets(empty=True, renderable=True, noSurfaceShader=True, name="{}SG".format(mat))
                    cmds.defaultNavigation(connectToExisting=True, source=mat, destination=shading_engine, f=True)
                    cmds.sets(cutFaces, forceElement = shading_engine, e = True)
                
    def selectTexture(self):
        """
        list all materials used by geometry in the scene
        """
        scene_materials=[]
        all_sgs=cmds.ls(type='shadingEngine')
        for sg in all_sgs:
            # if an sg has 'sets' members, it is used in the scene
            if cmds.sets(sg, q=True):
                materials = cmds.listConnections('{}.surfaceShader'.format(sg))
                if materials:
                    scene_materials.extend(materials)
        return (list(set(scene_materials)))
    
    def SetIcon(self):
        Material = self.SelectTexture.currentText()
        print (Material)
        tempwin = cmds.window()
        cmds.columnLayout('r')
        port = cmds.swatchDisplayPort(rs=65, wh=(64, 64), sn=Material)

        ptr = omui.MQtUtil.findControl(port)
        qport = wrapInstance(int(ptr), QtWidgets.QWidget)

        widget = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        widget.setLayout(vbox)
        qport.setParent(widget)
        self.layout.addWidget(qport,2,2)
        cmds.deleteUI(tempwin)
        widget.show()

    def GetMesh(self):
        """
        Return selected Meshes, Checks if nothing is selected
        """
        Selected = cmds.ls(selection = True)
        if not Selected:
            raise RuntimeError ("Nothing is selected")
        return Selected