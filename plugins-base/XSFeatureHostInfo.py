# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureHostInfo:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField("Host Performance Information")
        
        host = HotAccessor().local_host
        numCPUs = len(host.host_CPUs({}))
        try:
            cpuUsage = sum( [cpu.utilisation() for cpu in host.host_CPUs] ) / numCPUs # Allow divide-by-zero to throw
            cpuUsage = max(0.0, min(1.0, cpuUsage))
            cpuUsageStr = "%d%% of %d CPUs" % (int(cpuUsage * 100), numCPUs)
        except Exception, e:
            cpuUsageStr = Lang('<Unavailable>')

        try:
            totalMemory = float(host.metrics.memory_total(0))
            freeMemory = float(host.metrics.memory_free(0))
            memoryUsage = (totalMemory - freeMemory) / totalMemory # Allow divide-by-zero to throw
            memoryUsage = max(0.0, min(1.0, memoryUsage))
            memoryUsageStr = "%d%% of %s" % (int(memoryUsage * 100), SizeUtils.MemorySizeString(totalMemory))
        except Exception, e:
            memoryUsageStr = Lang('<Unavailable>')

        inPane.AddStatusField(Lang("CPU Usage", 16), cpuUsageStr)
        inPane.AddStatusField(Lang("Memory Usage", 16), memoryUsageStr)

        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Control This Host") } )
    
    @classmethod
    def ActivateHandler(cls):
        pass
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'HOST_INFO', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_VM',
                'menupriority' : 200,
                'menutext' : Lang('Host Performance Information') ,
                'activatehandler' : XSFeatureHostInfo.ActivateHandler,
                'statusupdatehandler' : XSFeatureHostInfo.StatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureHostInfo().Register()
