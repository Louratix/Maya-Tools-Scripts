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
        layout = QtWidgets.QGridLayout(self)

        self.ChunksSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.ChunkLabel = QtWidgets.QLabel("Chunks Amount 1")
        self.ChunksSlider.setMinimum(1)
        self.ChunksSlider.setMaximum(100)
        layout.addWidget(self.ChunkLabel,0,0)
        layout.addWidget(self.ChunksSlider,0,1)
        self.ChunksSlider.valueChanged.connect(self.update_chunks)

        self.StartStopBtn = QtWidgets.QPushButton("START")
        self.StartStopBtn.clicked.connect(self.Start)
        self.StartStopBtn.setStyleSheet("background-color : green")
        layout.addWidget(self.StartStopBtn,1,0,1,3)


    def update_chunks(self):
        value = self.ChunksSlider.value()
        self.ChunkLabel.setText(f"Subdiv Value: {value}")
        #self.Subdivise(value)

    def Start(self):
        #value = self.ChunksSlider.value()
        print ("hello")
        ToCut = self.GetMesh()
        BoundingBox = cmds.exactWorldBoundingBox()
        print (BoundingBox)

        PointsCount = self.ChunksSlider.value()
        VoroX = [random.uniform(BoundingBox[0], BoundingBox[3]) for i in range(PointsCount)]
        VoroY = [random.uniform(BoundingBox[1], BoundingBox[4]) for i in range(PointsCount)]
        VoroZ = [random.uniform(BoundingBox[2], BoundingBox[5]) for i in range(PointsCount)]
        VoroCenter = zip(VoroX,VoroY,VoroZ)

        for Voro in VoroCenter:
            angleX = random.uniform(0, 180)
            angleY = random.uniform(0, 180)
            angleZ = random.uniform(0, 180)
            randAng = (angleX, angleY, angleZ)
            cmds.polyCut(ToCut, ef = True, df = False, eo = [0,0,0], pc = Voro, ro = randAng)
            cmds.polyCloseBorder(ToCut)
        
        cmds.polySeparate(ToCut)


    def GetMesh(self):
        Selected = cmds.ls(selection = True)
        if not Selected:
            raise RuntimeError ("Nothing is selected")
        return Selected