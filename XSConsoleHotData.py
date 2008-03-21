# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import XenAPI

import commands, re, shutil, sys
from pprint import pprint

from XSConsoleAuth import *
from XSConsoleLang import *
from XSConsoleState import *
from XSConsoleUtils import *

class HotDataMethod:
    def __init__(self, inSend, inName):
        self.send = inSend
        self.name = inName
        
    def __getattr__(self, inName):
        self.name.append(inName)
        return self

    def __call__(self,  inDefault = None):
        return self.send(self.name,  inDefault)

class HotData:
    DATA_TIMEOUT_SECONDS = 1
    instance = None
    
    def __init__(self):
        self.data = {}
        self.session = None
        self.fetchers = self.Fetchers()

    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = HotData()
        return cls.instance
    
    @classmethod
    def Reset(cls):
        if cls.instance is not None:
            del cls.instance
            cls.instance = None
            
    def Fetch(self, inRef, inName):
        retVal = self.fetchers[inName][0](inRef)
        return retVal    
    
    def GetData(self, inNames, inDefault = None):
        itemRef = self.data # Start at the top level
        for name in inNames:
            if name is '__repr__':
                raise Exception('HotData.' + '.'.join(inNames[:-1]) + ' must end with ()')
            # Always refetch for now
            #elif name in itemRef:
            #    itemRef = itemRef[name]
            else:
                if name in self.fetchers:
                    itemRef[name] = self.Fetch(itemRef, name)
                    itemRef = itemRef[name]
                else:
                    return FirstValue(inDefault, None)
        return itemRef
    
    def __getattr__(self, inName):
        if inName[0].isupper():
            # Don't expect elements to start with upper case, so probably an unknown method name
            raise Exception("Unknown method HotData."+inName)
        return HotDataMethod(self.GetData, [inName])
    
    def Fetchers(self):
        retVal = {
            'vm' : [ lambda x: self.Session().xenapi.VM.get_all_records(), 60 ],
            'guest_vm' : [ lambda x: self.GuestVM(), 60 ]
        }
        return retVal
    
    def GuestVM(self):
        retVal = {}
        for key, value in self.vm().iteritems():
            if not value.get('is_a_template', False) and not value.get('is_control_domain', False):
                retVal[key] = value
        return retVal
    
    def Session(self):
        if self.session is None:
            self.session = Auth.Inst().OpenSession()
        return self.session
        
    def Dump(self):
        print "Contents of HotData cache:"
        pprint(self.data)
