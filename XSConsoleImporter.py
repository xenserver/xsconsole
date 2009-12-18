#!/usr/bin/env python

# Copyright (c) 2007-2009 Citrix Systems Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import imp, os, re, sys, traceback

from XSConsoleLog import *
from XSConsoleMenus import *

class Importer:
    plugIns = {}
    menuEntries = {}
    menuRegenerators = {}
    resources = {}
    
    @classmethod
    def Reset(cls):
        cls.plugIns = {}
        cls.menuEntries = {}
        cls.menuRegenerators = {}
        cls.resources = {}

    @classmethod
    def ImportAbsDir(cls, inDir):
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
                                try: XSLogError(*traceback.format_tb(sys.exc_info()[2]))
                                except: pass
                                try: XSLogError("*** PlugIn '"+importName+"' failed to load: "+str(e))
                                except: pass
                        finally:
                            if fileObj is not None:
                                fileObj.close()
                            
    @classmethod
    def ImportRelativeDir(self, inDir):
        basePath = sys.path[0]
        if basePath == '' and len(sys.path) > 1:
            # Handle redundant empty string when running from IDE
            basePath = sys.path[1]
        self.ImportAbsDir(basePath+'/'+inDir)
            
    @classmethod
    def RegisterMenuEntry(cls, inObj, inName, inParams):
        if inName not in cls.menuEntries:
            cls.menuEntries[inName] = []
            
        cls.menuEntries[inName].append(inParams)
        menuName = inParams.get('menuname', None)
        menuRegenerator = inParams.get('menuregenerator', None)
        if menuName is not None and menuRegenerator is not None:
            cls.menuRegenerators[menuName] = menuRegenerator
        # Store inObj only when we need to reregister plugins
        
    @classmethod
    def UnregisterMenuEntry(cls, inName):
        del cls.menuEntries[inName]            
    
    @classmethod
    def RegisterNamedPlugIn(cls, inObj, inName, inParams):
        cls.plugIns[inName] = inParams
        # Store inObj only when we need to reregister plugins
        
    @classmethod
    def UnregisterNamedPlugIn(cls, inName):
        del cls.plugIns[inName]
        
    @classmethod
    def RegisterResource(cls, inObj, inName, inParams):
        cls.resources[inName] = inParams
        # Store inObj only when we need to reregister plugins
        
    @classmethod
    def UnregisterResource(cls, inName):
        del cls.resources[inName]
        
    @classmethod
    def ActivateNamedPlugIn(cls, inName, *inParams):
        plugIn = cls.plugIns.get(inName, None)
        if plugIn is None:
            raise Exception(Lang("PlugIn (for activation) named '")+inName+Lang("' does not exist"))
        handler = plugIn.get('activatehandler', None)
        
        if handler is None:
            raise Exception(Lang("PlugIn (for activation) named '")+inName+Lang("' has no activation handler"))
        
        handler(*inParams)
    
    @classmethod
    def GetResource(cls, inName): # Don't use this until all of the PlugIns have had a chance to register
        retVal = None
        for resource in cls.resources.values():
            item = resource.get(inName, None)
            if item is not None:
                retVal = item
                break

        return retVal
        
    def GetResourceOrThrow(cls, inName): # Don't use this until all of the PlugIns have had a chance to register
        retVal = cls.GetResource(inName)
        if retVal is None:
            raise Exception(Lang("Resource named '")+inName+Lang("' does not exist"))
        
        return retVal
        
    @classmethod
    def BuildRootMenu(cls, inParent):
        retVal = RootMenu(inParent)
        
        for name, entries in cls.menuEntries.iteritems():
            for entry in entries:
                # Create the menu that this item is in
                retVal.CreateMenuIfNotPresent(name)
                # Create the menu that this item leads to when you select it
                if entry['menuname'] is not None:
                    retVal.CreateMenuIfNotPresent(entry['menuname'], entry['menutext'], name)
                
                choiceDef = ChoiceDef(entry['menutext'], entry.get('activatehandler', None), entry.get('statushandler', None))
                choiceDef.StatusUpdateHandlerSet(entry.get('statusupdatehandler', None))
                retVal.AddChoice(name, choiceDef, entry.get('menupriority', None))
        
        for entry in cls.plugIns.values():
            menuName = entry.get('menuname', None)
            if menuName is not None:
                choiceDef = ChoiceDef(entry['menutext'], entry.get('activatehandler', None), entry.get('statushandler', None))
                choiceDef.StatusUpdateHandlerSet(entry.get('statusupdatehandler', None))
                retVal.AddChoice(menuName, choiceDef, entry.get('menupriority', None))
        
        return retVal
    
    @classmethod
    def RegenerateMenu(cls, inName, inMenu):
        retVal = inMenu
        regenerator = cls.menuRegenerators.get(inName, None)
        if regenerator is not None:
            retVal = regenerator(inName, inMenu)
        return retVal

    @classmethod
    def Dump(cls):
        print "Contents of PlugIn registry:"
        pprint(cls.plugIns)
        print "\nRegistered menu entries:"
        pprint(cls.menuEntries)
        print "\nRegistered resources:"
        pprint(cls.resources)
    
