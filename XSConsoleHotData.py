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

class HotOpaqueRef:
    def __init__(self, inOpaqueRef, inType):
        self.opaqueRef = inOpaqueRef
        self.type = inType
        self.hash = hash(inOpaqueRef)
    
    def __repr__(self):
        retVal = "HotOpaqueRef:\n"
        retVal += "opaqueRef = "+str(self.opaqueRef)+"\n"
        retVal += "type = "+str(self.type)+"\n"
        retVal += "hash = "+str(self.hash)+"\n"
        return retVal
        
    # __hash__ and __cmp__ allow this object to be used as a dictionary key
    def __hash__(self):
        return self.hash
    
    def __cmp__(self, inOther):
        if not isinstance(inOther, HotOpaqueRef):
            return 1
        if self.opaqueRef == inOther.opaqueRef:
            return 0
        if self.opaqueRef < inOther.opaqueRef:
            return -1
        return 1
    
    def OpaqueRef(self): return self.opaqueRef
    def Type(self): return self.type
        
class HotAccessor:
    def __init__(self, inName = None, inRefs = None):
        self.name = FirstValue(inName, [])
        self.refs = FirstValue(inRefs, [])
        
    def __getattr__(self, inName):
        retVal = HotAccessor(self.name[:], self.refs[:]) # [:] copies the array
        retVal.name.append(inName)
        retVal.refs.append(None)
        return retVal

    def __call__(self, inParam = None):
        if isinstance(inParam, HotOpaqueRef):
            # Add a reference, selecting e.g. a key selecting a particular item from a dictionary
            self.refs[-1] = inParam
            retVal = self # Return this object for further operations
        else:
            # These are the brackets on the end of the statement, with optional default value.
            # That makes it a request to fetch the data
            retVal = HotData.Inst().GetData(self.name, inParam, self.refs)
        return retVal
    
    def __str__(self):
        return ",".join(zip(self.name, self.refs))
    
    def __repr__(self):
        return __str__(self)

class HotData:
    instance = None
    
    def __init__(self):
        self.data = {}
        self.timestamps = {}
        self.session = None
        self.InitialiseFetchers()

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
            
    def Fetch(self, inName, inRef):
        # Top-level object are cached by name, referenced objects by reference
        cacheName = FirstValue(inRef, inName)
        cacheEntry = self.data.get(cacheName, None)
        fetcher = self.fetchers[inName]
        timeNow = time.time()
        if cacheEntry is not None and timeNow - cacheEntry.timestamp < fetcher.lifetimeSecs:
            retVal = cacheEntry.value
        else:
            retVal = fetcher.fetcher(inRef)
            # Save in the cache
            self.data[cacheName] = Struct(timestamp = timeNow, value = retVal)
        return retVal    
    
    def GetData(self, inNames, inDefault, inRefs):
        itemRef = self.data # Start at the top level
        
        for i, name in enumerate(inNames):
            if name is '__repr__':
                raise Exception('HotData.' + '.'.join(inNames[:-1]) + ' must end with ()')
    
            dataValue = itemRef.get(name, None)
            fetcher = self.fetchers.get(name, None)
            if fetcher is None:
                # No fetcher for this item, so return it if it's there or fail
                if dataValue is not None:
                    itemRef = dataValue
                else:
                    return FirstValue(inDefault, None)
            else:
                if dataValue is not None and isinstance(dataValue, HotOpaqueRef):
                    # This is a subitem with an OpaqueRef supplied by xapi, so don't let the caller offer their own
                    if inRefs[i] is not None:
                        raise Exception("OpaqueRef given where not required, at '"+name+"' in '"+'.'.join(inNames[:-1])+"'")
                    itemRef = self.Fetch(name, dataValue)
                else:
                    # Use the caller-supplied OpaqueRef, or None
                    itemRef = self.Fetch(name, inRefs[i])
        return itemRef
    
    def __getattr__(self, inName):
        if inName[0].isupper():
            # Don't expect elements to start with upper case, so probably an unknown method name
            raise Exception("Unknown method HotData."+inName)
        return HotAccessor([inName], [None])

    def AddFetcher(self, inKey, inFetcher, inLifetimeSecs):
        self.fetchers[inKey] = Struct( fetcher = inFetcher, lifetimeSecs = inLifetimeSecs ) 

    def InitialiseFetchers(self):
        self.fetchers = {}
        self.AddFetcher('guest_metrics', self.FetchVMGuestMetrics, 5)
        self.AddFetcher('guest_vm', self.FetchGuestVM, 5)
        self.AddFetcher('guest_vm_derived', self.FetchGuestVMDerived, 5)
        self.AddFetcher('metrics', self.FetchVMMetrics, 5)
        self.AddFetcher('vm', self.FetchVM, 5)
    
    def FetchVMGuestMetrics(self, inOpaqueRef):
        retVal = self.Session().xenapi.VM_guest_metrics.get_record(inOpaqueRef.OpaqueRef())
        return retVal    

    def FetchGuestVM(self, inOpaqueRef):
        if inOpaqueRef is not None:
            # Don't need to filter, so can use the standard VM fetch
            retVal = self.FetchVM(inOpaqueRef)
        else:
            retVal = {}
            for key, value in self.vm().iteritems():
                if not value.get('is_a_template', False) and not value.get('is_control_domain', False):
                    retVal[key] = value
        return retVal

    def FetchGuestVMDerived(self, inOpaqueRef):
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

    def FetchVMMetrics(self, inOpaqueRef):
        if inOpaqueRef is None:
            raise Exception("Request for VM metrics requires an OpaqueRef")
        retVal = self.Session().xenapi.VM_metrics.get_record(inOpaqueRef.OpaqueRef())
        return retVal

    def FetchVM(self, inOpaqueRef):
        def LocalConverter(inVM):
            return HotData.ConvertOpaqueRefs(inVM,
                affinity='host',
                guest_metrics='guest_metrics',
                metrics='metrics',
                resident_on='host',
                suspend_VDI='vdi')
        
        if inOpaqueRef is not None:
            vm = self.Session().xenapi.VM.get_record(inOpaqueRef.OpaqueRef())
            retVal = LocalConverter(vm)
        else:
            vms = self.Session().xenapi.VM.get_all_records()
            retVal = {}
            for key, vm in vms.iteritems():
                vm = LocalConverter(vm)
                retVal[HotOpaqueRef(key, 'vm')] = vm
        return retVal

    @classmethod # classmethod so that other class's fetchers can use it easily
    def ConvertOpaqueRefs(cls, *inArgs, **inKeywords):
        if len(inArgs) != 1:
            raise Exception('ConvertOpaqueRef requires a dictionary object as the first argument')
        ioObj = inArgs[0]
        for keyword, value in inKeywords.iteritems():
            obj = ioObj.get(keyword, None)
            if obj is not None:
                ioObj[keyword] = HotOpaqueRef(obj, value)
                
        if Auth.Inst().IsTestMode(): # Tell the caller what they've missed, when in test mode
            for key,value in ioObj.iteritems():
                if isinstance(value, str) and value.startswith('OpaqueRef'):
                    print('Missed OpaqueRef in HotData item: '+key)
                    
        return ioObj

    def Session(self):
        if self.session is None:
            self.session = Auth.Inst().OpenSession()
        return self.session
        
    def Dump(self):
        print "Contents of HotData cache:"
        pprint(self.data)
