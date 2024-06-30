import maya.cmds as cmds

SUFFIXES = {
"mesh":"geo",
"joint":"jnt",
"nurbsCurve":"nCurve",
"locator":"lcr",
"camera": None
}

DEFAULT_SUFFIX = "grp"

def Rename (selection = False) :
    """MayaScriptRenamer
    Renames all current object in the dashboard with a Suffix,

    Arguments = wether there is a selection or not.

    Return = List of objects the function operated on.
    """

    objects = cmds.ls(selection = selection, dag = True, long = True)

    if selection and not objects:
        raise RuntimeError ("nothing is selected")

    objects.sort(key=len, reverse = True)

    for obj in objects:
        shortName =(obj.split("|")[-1])
        children = cmds.listRelatives(obj, children=True, fullPath=True) or []
        
        if len(children)== 1:
            child = children[0]
            objType = cmds.objectType(child)
        else:
            objType = cmds.objectType(obj)
            
        suffix = SUFFIXES.get(objType,DEFAULT_SUFFIX)

        if not suffix:
            continue

        if obj.endswith('_' + suffix):
            continue
            
        newName = "%s_%s" % (shortName, suffix)
        cmds.rename(obj, newName)

        index = objects.index(obj)
        objects[index] = obj.replace(shortName, newName)

    return objects
