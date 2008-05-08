# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class SRUtils:
    operationNames = {
        #'evacuate' : Struct(name = Lang("Evacuate SR"), priority = 10),
        #'enable' : Struct(name = Lang("Enable"), priority = 20),
        #'designate_new_master' : Struct(name = Lang("Designate as new Pool Master"), priority = 30)
    }
    
    @classmethod
    def AllowedOperations(cls):
        return cls.operationNames.keys()
        
    @classmethod
    def AsyncOperation(cls, inOperation, inSRHandle, inParam0 = None):
        if False:
            pass
        #if inOperation == 'evacuate':
            #task = Task.New(lambda x: x.xenapi.Async.host.evacuate(inSRHandle.OpaqueRef()))
        else:
            raise Exception("Unknown SR operation "+str(inOperation))
        
        return task
        
    @classmethod
    def DoOperation(cls, inOperation, inSRHandle):
        task = cls.AsyncOperation(inOperation, inSRHandle)
        
        if task is not None:
            while task.IsPending():
                time.sleep(0.1)
                task.RaiseIfFailed()

    @classmethod
    def OperationStruct(cls, inOperation):
        retVal = cls.operationNames.get(inOperation, None)
        if retVal is None:
            raise Exception("Unknown SR operation "+str(inOperation))
        return retVal

    @classmethod
    def OperationName(cls, inOperation):
        return cls.OperationStruct(inOperation).name

    @classmethod
    def OperationPriority(cls, inOperation):
        return cls.OperationStruct(inOperation).priority

    @classmethod
    def SRFlags(cls, inSR):
        defaultUUIDs = [ pool.default_SR.uuid() for pool in HotAccessor().pool ]
        retVal = []
        if inSR.uuid() in defaultUUIDs:
            retVal.append('default')
        return retVal
        
    @classmethod
    def AnnotatedName(cls, inSR):
        retVal = inSR.name_label(Lang('<Unknown>'))
        flags = cls.SRFlags(inSR)
        if len(flags) > 0:
            retVal += ' ('+', '.join( [ Lang(x) for x in flags ] ) + ')'
        return retVal

    @classmethod
    def TypeName(cls, inSRType):
        return LangFriendlyNames.Translate('Label-SR.SRTypes-'+inSRType)
        
class XSFeatureSRCommon:
    def Register(self):
        Importer.RegisterResource(
            self,
            'SR_COMMON', # Name of this item for replacement, etc.
            {
                'SRUtils' : SRUtils
            }
        )

# Register this plugin when module is imported
XSFeatureSRCommon().Register()
