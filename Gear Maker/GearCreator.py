import maya.cmds as cmds

def CreateGear(teeth = 10, lenght = 0.4):
    """
    this function creates a gear with the following arguments:
     teeth = number of teeth wanted
     lenght = length of the extrude

     return:
     returns a tupple of the transform, constructor and extrude node

    """
    #teeth are every outward blocks so spans is twice that
    spans = teeth * 2

    transform, constructor = cmds.polyPipe(subdivisionsAxis = spans)

    sideFaces = range (spans *2, spans *3, 2)

    cmds.select(clear = True)

    for face in sideFaces:
        cmds.select('%s.f[%s]' % (transform, face), add = True)

    extrude = cmds.polyExtrudeFacet(localTranslateZ=lenght)[0]
    print (extrude)
    return transform, constructor, extrude

def changeTeeth(constructor, extrude, teeth = 10, lenght = 0.4):
    spans = teeth*2

    cmds.polyPipe(constructor, edit = True, subdivisionsAxis = spans)

    sideFaces = range (spans *2, spans *3, 2)
    faceNames = []

    for face in sideFaces:
        faceName = 'f[%s]' % (face)
        faceNames.append(faceName)

        cmds.setAttr('%s.inputComponents' % (extrude), len(faceNames), *faceNames, type ="componentList")