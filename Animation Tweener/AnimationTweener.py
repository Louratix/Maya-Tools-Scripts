import maya.cmds as cmds

def tween(percentage, obj = None, attrs = None,selection = True):
    if not obj and not selection:
        raise ValueError("No object was given to tween")
    if not obj:
        obj = cmds.ls(sl=1)[0]
    if not attrs:
        attrs = cmds.listAttr(obj, keyable = True)

    currentTime = cmds.currentTime(query = True)

    for attr in attrs:
        attrFull = '%s.%s' % (obj, attr)
        keyFrames = cmds.keyframe(attrFull, query = True)

        if not keyFrames:
            continue

        previousKeyFrames = [frames for frames in keyFrames if frames < currentTime]

        laterKeyFrames = [frames for frames in keyFrames if frames > currentTime]
        
        if not previousKeyFrames and not laterKeyFrames:
            continue

        previousFrame = max(previousKeyFrames) if previousKeyFrames else None
        nextFrame = min(laterKeyFrames) if laterKeyFrames else None

    
        previousValue = cmds.getAttr(attrFull, time = previousFrame)
        nextValue = cmds.getAttr(attrFull, time = nextFrame)
        if nextFrame is None:
            currentValue = previousValue
        elif previousFrame is None:
            currentValue = nextValue
        elif previousValue == nextValue:
            currentValue = previousValue
        else:
            difference = nextValue - previousValue
            weightedDifference = (difference * percentage) / 100.0
            currentValue = previousValue + weightedDifference

        cmds.setAttr(attrFull, currentValue)
        cmds.setKeyframe(attrFull, time = currentTime, value = currentValue)

class tweenWindow(object):

    windowName = "Tweener Window"

    def show(self):
        if cmds.window(self.windowName, query = True, exists = True):
            cmds.deleteUI(self.windowName)

        cmds.window(self.windowName)

        self.buildUI()

        cmds.showWindow()

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

    def close(self, *args):
        cmds.deleteUI(self.windowName)
