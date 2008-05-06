# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class HostUtils:
    operationNames = {
        'evacuate' : Struct(name = Lang("Evacuate Host"), priority = 10),
        'enable' : Struct(name = Lang("Enable"), priority = 20),
        'designate_new_master' : Struct(name = Lang("Designate as new Pool Master"), priority = 30)
    }
    
    @classmethod
    def AllowedOperations(cls):
        return cls.operationNames.keys()
        
    @classmethod
    def AsyncOperation(cls, inOperation, inHostHandle, inParam0 = None):
        if inOperation == 'evacuate':
            task = Task.New(lambda x: x.xenapi.Async.host.evacuate(inHostHandle.OpaqueRef()))
        elif inOperation == 'enable':
            task = Task.New(lambda x: x.xenapi.Async.host.enable(inHostHandle.OpaqueRef()))
        elif inOperation == 'designate_new_master': # FIXME: really a pool operation
            task = Task.New(lambda x: x.xenapi.Async.pool.designate_new_master(inHostHandle.OpaqueRef()))
        else:
            raise Exception("Unknown Host operation "+str(inOperation))
        
        return task
        
    @classmethod
    def DoOperation(cls, inOperation, inHostHandle):
        task = cls.AsyncOperation(inOperation, inHostHandle)
        
        if task is not None:
            while task.IsPending():
                time.sleep(0.1)
                task.RaiseIfFailed()

    @classmethod
    def OperationStruct(cls, inOperation):
        retVal = cls.operationNames.get(inOperation, None)
        if retVal is None:
            raise Exception("Unknown Host operation "+str(inOperation))
        return retVal

    @classmethod
    def OperationName(cls, inOperation):
        return cls.OperationStruct(inOperation).name

    @classmethod
    def OperationPriority(cls, inOperation):
        return cls.OperationStruct(inOperation).priority

class XSFeatureHostCommon:
    def Register(self):
        Importer.RegisterResource(
            self,
            'HOST_COMMON', # Name of this item for replacement, etc.
            {
                'HostUtils' : HostUtils
            }
        )

# Register this plugin when module is imported
XSFeatureHostCommon().Register()
