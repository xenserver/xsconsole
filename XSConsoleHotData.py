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

class HotAccessor:
    def __init__(self):
        self.name = []
        self.refs = []
        
    def __getattr__(self, inName):
        self.name.append(inName)
        self.refs.append(None)
        return self

    def __call__(self, inRef = None):
        self.refs[-1] = inRef
        return self
        
    def Get(self, inName, inDefault = None):
        return HotData.Inst().GetData(self.name+[inName], inDefault, self.refs+[None])
        
class HotData:
    DATA_TIMEOUT_SECONDS = 1
    instance = None
    
    def __init__(self):
        self.data = {}
        self.timestamps = {}
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
        retVal = self.fetchers[inName][0](inRef, inName)
        return retVal    
    
    def GetData(self, inNames, inDefault = None, inRefs = None):
        itemRef = self.data # Start at the top level
        
        for i, name in enumerate(inNames):
            if name is '__repr__':
                raise Exception('HotData.' + '.'.join(inNames[:-1]) + ' must end with ()')
    
            fetcher = self.fetchers.get(name, None)
            if fetcher is None:
                # No fetcher for this item, so return it if it's there or fail
                if name in itemRef:
                    itemRef = itemRef[name]
                else:
                    return FirstValue(inDefault, None)
            else:
                timeNow = time.time()
                lastFetchTime = self.timestamps.get(id(itemRef), None)
                if lastFetchTime is None or timeNow - lastFetchTime > fetcher[1]:
                    itemRef[name] = self.Fetch(itemRef, name)
                    self.timestamps[id(itemRef)] = timeNow
                itemRef = itemRef[name]
                
            if inRefs is not None and inRefs[i] is not None:
                itemRef = itemRef[inRefs[i]]
        return itemRef
    
    def __getattr__(self, inName):
        if inName[0].isupper():
            # Don't expect elements to start with upper case, so probably an unknown method name
            raise Exception("Unknown method HotData."+inName)
        return HotDataMethod(self.GetData, [inName])

    def Fetchers(self):
        retVal = {
            'guest_metrics' : [ lambda x, y: self.GuestMetrics(x, y), 5, None ],
            'vm' : [ lambda x, y: self.Session().xenapi.VM.get_all_records(), 5, None ],
            'guest_vm' : [ lambda x, y: self.GuestVM(), 5, None ],
            'guest_vm_derived' : [ lambda x, y: self.GuestVMDerived(), 5, None ]
        }
        return retVal
    
    def GuestMetrics(self, inItemRef, inName):
        itemValue = inItemRef[inName]
        if isinstance(itemValue, str):
            opaqueRef = itemValue
            retVal = self.Session().xenapi.VM_guest_metrics.get_record(opaqueRef)
            retVal['opaqueref'] = opaqueRef
        else:
            retVal = self.Session().xenapi.VM_guest_metrics.get_record(itemValue['opaqueref'])
            
        return retVal
    
    def GuestVM(self):
        retVal = {}
        for key, value in self.vm().iteritems():
            if not value.get('is_a_template', False) and not value.get('is_control_domain', False):
                retVal[key] = value
        return retVal

    def GuestVMDerived(self):
        retVal = {}
        halted = 0
        paused = 0
        running = 0
        suspended = 0

        for key, vm in self.guest_vm().iteritems():
            powerState = vm.get('power_state', '').lower()
            if powerState.startswith('halted'):
                halted += 1
            elif powerState.startswith('paused'):
                paused += 1
            elif powerState.startswith('running'):
                running += 1
            elif powerState.startswith('suspended'):
                suspended += 1
            
        retVal['num_halted'] = halted
        retVal['num_paused'] = paused
        retVal['num_running'] = running
        retVal['num_suspended'] = suspended

        return retVal

    def Session(self):
        if self.session is None:
            self.session = Auth.Inst().OpenSession()
        return self.session
        
    def Dump(self):
        print "Contents of HotData cache:"
        pprint(self.data)
