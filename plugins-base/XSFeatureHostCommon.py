# Copyright (c) 2008-2009 Citrix Systems Inc.
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
    def OtherConfigRemove(cls, inHostHandle, inName):
        Task.Sync(lambda x: x.xenapi.host.remove_from_other_config(inHostHandle.OpaqueRef(), inName))
    
    @classmethod
    def OtherConfigReplace(cls, inHostHandle, inName, inValue):
        cls.OtherConfigRemove(inHostHandle, inName)
        Task.Sync(lambda x: x.xenapi.host.add_to_other_config(inHostHandle.OpaqueRef(), inName, inValue))
    
    @classmethod
    def AsyncOperation(cls, inOperation, inHostHandle, *inParams):
        if inOperation == 'evacuate':
            # Gather the list of VMs to restart on exit of maintenance mode
            runningVMs = [ vm.HotOpaqueRef().OpaqueRef() for vm in HotAccessor().local_host.resident_VMs if not vm.is_control_domain() ]
            task = Task.New(lambda x: x.xenapi.Async.host.evacuate(inHostHandle.OpaqueRef()))
            cls.OtherConfigReplace(inHostHandle, 'MAINTENANCE_MODE_EVACUATED_VMS', ','.join(runningVMs))
            cls.OtherConfigReplace(inHostHandle, 'MAINTENANCE_MODE', 'true')
        elif inOperation == 'disable':
            task = Task.New(lambda x: x.xenapi.Async.host.disable(inHostHandle.OpaqueRef()))
        elif inOperation == 'enable':
            cls.OtherConfigRemove(inHostHandle, 'MAINTENANCE_MODE')
            cls.OtherConfigRemove(inHostHandle, 'MAINTENANCE_MODE_EVACUATED_VMS')
            task = Task.New(lambda x: x.xenapi.Async.host.enable(inHostHandle.OpaqueRef()))
        elif inOperation == 'designate_new_master':
            task = Task.New(lambda x: x.xenapi.Async.pool.designate_new_master(inHostHandle.OpaqueRef()))
        elif inOperation == 'join':
            task = Task.New(lambda x: x.xenapi.Async.pool.join(*inParams))
        elif inOperation == 'join_force':
            task = Task.New(lambda x: x.xenapi.Async.pool.join_force(*inParams))
        elif inOperation == 'eject':
            task = Task.New(lambda x: x.xenapi.Async.pool.eject(inHostHandle.OpaqueRef()))
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
