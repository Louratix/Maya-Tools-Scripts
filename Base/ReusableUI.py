from AnimationTweener import tween
from GearCreatorClass import Gear
import maya.cmds as cmds

class baseWindow(object):

    windowName = "Base Window"

    def show(self):
        if cmds.window(self.windowName, query = True, exists = True):
            cmds.deleteUI(self.windowName)

        cmds.window(self.windowName)
        self.buildUI()
        cmds.showWindow()

    def buildUI(self):
        pass

    def reset(self, *args):
        pass

    def close(self, *args):
        cmds.deleteUI(self.windowName)

class TweenerUI (baseWindow):

    windowName = "Tween Window"

    def buildUI(self):
        column = cmds.columnLayout()
        cmds.text(label = "use this slider to tween the object")
        row = cmds.rowLayout(numberOfColumns = 2)
        self.slider = cmds.floatSlider (min = 0, max = 100, value = 50, step = 1, changeCommand = tween)
        cmds.button(label = "Reset", command = self.reset)
        cmds.setParent(column)
        cmds.button(label = "close", command = self.close)

    def reset(self, *args):
        cmds.floatSlider(self.slider, edit = True, value = 50)

class GearUI(baseWindow):

    windowName = "Gear Window"

    def __init__(self):
        self.gear = None

    def buildUI(self):
        column = cmds.columnLayout()
        cmds.text(label = "use this slider to modify the extrudes of the gear")

        cmds.rowLayout (numberOfColumns=4)
        self.label = cmds.text(label = "10")
        self.slider = cmds.intSlider(min=5,max=30,value=10,step=1,dragCommand=self.modifyGear)
        cmds.button(label="Make a Gear", command = self.makeGear)
        cmds.button(label="reset", command=self.reset)

        cmds.setParent(column)
        cmds.button(label="Close", command = self.close)

    def makeGear(self, *args):
        teeth = cmds.intSlider(self.slider, query = True, value = True)
        self.gear = Gear()

        self.gear.CreateGear(teeth = teeth)


    def modifyGear(self, teeth):
        if self.gear:
            self.gear.changeTeeth(teeth = teeth)

        cmds.text(self.label, edit=True, label = teeth)

    def reset(self, *args):
        self.gear = None
        cmds.intSlider(self.slider, edit = True, value = 10)
        cmds.text(self.label, edit = True, label = 10)