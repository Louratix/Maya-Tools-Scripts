import maya.cmds as cmds
import os
import json
import pprint

USERAPPDIR = cmds.internalVar(userAppDir=True)
print (USERAPPDIR)

DIRECTORY = os.path.join (USERAPPDIR, 'ControllerLibrary')

def createDirectory (Directory = DIRECTORY):
    """
    Creates a Directory if no directory already here

    Args: Directory(str) = the directory to create
    
    """

    if not os.path.exists(Directory):
        os.mkdir(Directory)

class ControllerLibrary(dict):

    def save(self, name, directory = DIRECTORY, screenshot = True, **info):

        createDirectory(directory)

        path = os.path.join(directory, '%s.ma' % name)
        infoFile = os.path.join(directory, '%s.json' % name)

        info['name'] = name
        info['path'] = path
        
        cmds.file(rename=path)

        if cmds.ls(selection = True):
            cmds.file(force = True, type = 'mayaAscii', exportSelected = True)
        else:
            cmds.file(save=True, type='mayaAscii', force =True )

        if screenshot:
            info ['screenshot'] = self.saveScreenshot(name, directory = DIRECTORY)

        with open (infoFile, 'w') as f:
            json.dump(info, f, indent = 4)

        self[name] = info


    def find(self, directory = DIRECTORY):
        self.clear

        if not os.path.exists(directory):
            print ('no models saved')
            return
        
        files = os.listdir(directory)
        mayaFiles = [f for f in files if f.endswith('.ma')]

        for ma in mayaFiles:
            name,ext = os.path.splitext(ma)
            path = os.path.join(directory, ma)

            infoFile = '%s.json' % name
            if infoFile in files:
                infoFile = os.path.join(directory, infoFile)

                with open (infoFile, 'r') as f:
                    info = json.load(f)
                
            else:
                info ={}

            screenshot = '%s.jpg' % name
            if screenshot in files:
                info['screenshot'] = os.path.join(directory, name)
            else:
                info['screenshot'] = os.path.join(directory, 'Default')
            
            info['name'] = name
            info['path'] = path

            self[name] = info


    def load(self, name):
        
        path = self[name]['path']
        cmds.file(path, i = True, usingNamespaces = False)

    def saveScreenshot (self, name, directory = DIRECTORY):
        path = os.path.join(directory, '%s.jpg' % name)

        cmds.viewFit()
        cmds.setAttr('defaultRenderGlobals.imageFormat', 8)
        cmds.playblast(completeFilename = path, forceOverwrite = True, format = 'image', width = 200, height = 200, showOrnaments = False, startTime =1, endTime = 1, viewer = False )
        