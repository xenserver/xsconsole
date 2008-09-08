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
        try:
            localHostMetrics = HotMetrics.Inst().LocalHostMetrics()
        except Exception, e:
            XSLogOnce('LocalHostMetrics failed', e)
            localHostMetrics = {}
        
        try:
            cpuUsage = localHostMetrics['cpuusage']
            cpuUsage = max(0.0, min(1.0, cpuUsage))
            cpuUsageStr = "%d%% of %d CPUs" % (int(cpuUsage * 100), localHostMetrics['numcpus'])
        except Exception, e:
            cpuUsageStr = Lang('<Unavailable>')

        try:
            totalMemory = localHostMetrics['memory_total']
            freeMemory = localHostMetrics['memory_free']
            memoryUsage = (totalMemory - freeMemory) / totalMemory # Allow divide-by-zero to throw
            memoryUsage = max(0.0, min(1.0, memoryUsage))
            # Increase memory slightly to counteract metrics error
            totalMemory *= 1.001
            memoryUsageStr = "%d%% of %s" % (int(memoryUsage * 100), SizeUtils.MemorySizeString(totalMemory))
        except Exception, e:
            memoryUsageStr = Lang('<Unavailable>')

        inPane.AddStatusField(Lang("CPU Usage", 16), cpuUsageStr)
        inPane.AddStatusField(Lang("Memory Usage", 16), memoryUsageStr)
    
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
