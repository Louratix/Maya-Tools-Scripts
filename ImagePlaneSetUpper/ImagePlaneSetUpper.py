import maya.cmds as cmds
from Qt import QtCore, QtWidgets, QtGui
import os

class ImagePlanes():
    def createIPF():
        path = cmds.workspace(fn = True) + "/images"
        List = []

        for obj in os.listdir(path):
            List.append(obj)
            
        if 'front.png' in List:
            path += "/front.png"
            IPF = cmds.imagePlane(name = "Front Image Reference", fileName = path)
            cmds.move(0, 25, -30)
        elif 'front.jpg' in List:
            path += "/front.jpg"
            IPF = cmds.imagePlane(name = "Front Image Reference", fileName = path)
            cmds.move(0, 25, -30)
        else:
            IPF = cmds.imagePlane(name = "Front Image Reference", w = 50, h = 50)
            cmds.move(0, 25, -30)

    def createIPT():

        path = cmds.workspace(fn = True) + "/images"
        List = []

        for obj in os.listdir(path):
            List.append(obj)

        if 'top.png' in List:
            path += "/top.png"
            IPT = cmds.imagePlane(name = "Top Image Reference", fileName = path)
            cmds.move(0, 50, 0)
            cmds.rotate(90, 0, 0)
        elif 'top.jpg' in List:
            path += "/top.jpg"
            IPT = cmds.imagePlane(name = "Top Image Reference", fileName = path)
            cmds.move(0, 50, 0)
            cmds.rotate(90, 0, 0)
        else:
            IPT = cmds.imagePlane(name = "Top Image Reference", w = 50, h = 50)
            cmds.move(0, 50, 0)
            cmds.rotate(90, 0, 0)

    def createIPS():

        path = cmds.workspace(fn = True) + "/images"
        List = []

        for obj in os.listdir(path):
            List.append(obj)
        
        if 'side.png' in List:
            path += "/side.png"
            IPS = cmds.imagePlane(name = "Side Image Reference", fileName = path)
            cmds.move(-30, 25, 0)
            cmds.rotate(0, 90, 0)
        elif 'side.jpg' in List:
            path += "/side.jpg"
            IPS = cmds.imagePlane(name = "Side Image Reference", fileName = path)
            cmds.move(-30, 25, 0)
            cmds.rotate(0, 90, 0)
        else:
            IPS = cmds.imagePlane(name = "Side Image Reference", w = 50, h = 50)
            cmds.move(-30, 25, 0)
            cmds.rotate(0, 90, 0)

class ImagePlanesUI(QtWidgets.QWidget):
    def __init__ (self):
        super(ImagePlanesUI, self).__init__()
        self.BuildUI()

    def BuildUI(self):
        layout = QtWidgets.QVBoxLayout(self)

        btnWidget = QtWidgets.QWidget()
        btnLayout = QtWidgets.QHBoxLayout(btnWidget)
        layout.addWidget(btnWidget)

        frontBtn = QtWidgets.QPushButton('Front')
        frontBtn.clicked.connect(ImagePlanes.createIPF)
        btnLayout.addWidget(frontBtn)

        sideBtn = QtWidgets.QPushButton('Side')
        sideBtn.clicked.connect(ImagePlanes.createIPS)
        btnLayout.addWidget(sideBtn)

        topBtn = QtWidgets.QPushButton('Top')
        topBtn.clicked.connect(ImagePlanes.createIPT)
        btnLayout.addWidget(topBtn)