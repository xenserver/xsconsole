#!/usr/bin/env python

# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import imp, os, re, sys

from XSConsoleMenus import *

class Importer:
    plugIns = {}
    
    def __init__(self):
        pass
        
    def ImportAbsDir(self, inDir):
        if os.path.isdir(inDir): # Ignore non-existent directories
            for root, dirs, files in os.walk(inDir):
                for filename in files:
                    match =  re.match(r'([^/]+)\.py$', filename) # Pick out .py files in the base directory
                    if match:
                        importName = match.group(1)
                        fileObj = None
                        try:
                            try:
                                # Import using variable as module name
                                (fileObj, pathName, description) = imp.find_module(importName, [root])
                                imp.load_module(importName, fileObj, pathName, description)
                            except Exception, e:
                                print "PlugIn '"+importName+"' failed to load: "+str(e)
                        finally:
                            if fileObj is not None:
                                fileObj.close()
                            
                         
    def ImportRelativeDir(self, inDir):
        self.ImportAbsDir(sys.path[0]+'/'+inDir)
            
    @classmethod
    def RegisterNamedPlugIn(cls, inObj, inName, inParams):
        cls.plugIns[inName] = inParams
        # Store inObj only when we need to reregister plugins
        
    @classmethod
    def BuildRootMenu(cls, inParent):
        retVal = RootMenu(inParent)
        for entry in cls.plugIns.values():
            menuName = entry.get('menuname', None)
            if menuName is not None:
                choiceDef = ChoiceDef(entry['menutext'], entry.get('activatehandler', None), entry.get('statushandler', None))
                choiceDef.StatusUpdateHandlerSet(entry.get('statusupdatehandler', None))
                retVal.AddChoice(menuName, choiceDef, entry.get('menupriority', None))
        
        return retVal
        
    @classmethod
    def Dump(cls):
        print 'Contents of PlugIn registry:'
        pprint(cls.plugIns)
    
