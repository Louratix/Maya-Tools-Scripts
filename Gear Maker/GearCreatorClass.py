import maya.cmds as cmds

class Gear(object):
    """
        This class lets us create a gear and modify its dents
    """
    def __init__ (self):
        """Initiate some values"""
        print("running init function")
        self.constructor = None
        self.extrude = None
        self.transform = None

    def CreateGear(self, teeth = 10, length = 0.4):
        """
        this function creates a gear with the following arguments:
        teeth = number of teeth wanted
        lenght = length of the extrude
        return:
        returns a tupple of the transform, constructor and extrude node
        """
        #teeth are every outward blocks so spans is twice that
        spans = teeth *2

        self.transform, self.constructor = cmds.polyPipe(subdivisionsAxis = spans)

        sideFaces = range (spans *2, spans *3, 2)

        cmds.select(clear = True)

        for face in sideFaces:
            cmds.select('%s.f[%s]' % (self.transform, face), add = True)

        self.extrude = cmds.polyExtrudeFacet(localTranslateZ=length)[0]
        #return transform, constructor, extrude

    def changeTeeth(self, teeth = 10, length = 0.4):
        """ 
        this function changes the gear's teeth and what face to extrude accordingly
        """
        spans = teeth*2

        cmds.polyPipe(self.constructor, edit = True, subdivisionsAxis = spans)

        sideFaces = range (spans *2, spans *3, 2)
        faceNames = []

        for face in sideFaces:
            faceName = 'f[%s]' % (face)
            faceNames.append(faceName)

            cmds.setAttr('%s.inputComponents' % (self.extrude), len(faceNames), *faceNames, type ="componentList")