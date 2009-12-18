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

class XSFeatureHostInfo:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField("Host Performance Information")
        try:
            localHostMetrics = HotMetrics.Inst().LocalHostMetrics()
        except Exception, e:
            XSLogFailure('LocalHostMetrics failed', e)
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
