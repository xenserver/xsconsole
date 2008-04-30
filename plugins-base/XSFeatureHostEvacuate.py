# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureHostEvacuate:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        db = HotAccessor()
        inPane.AddTitleField("Evacuate This Host")
        
        inPane.AddWrappedTextField(Lang('This operation will migrate all Virtual Machines running on this host '
            'to other hosts in the Resource Pool.  It is typically used before shutting down a host for maintenance, '
            'and is only relevant for hosts in Resource Pools.'))
        inPane.NewLine()
        
        if len(db.host([])) <= 1:
            inPane.AddWrappedTextField(Lang('This host is not in a Resource Pool, so this option is disabled.'))
            inPane.NewLine()
        elif db.local_pool.master.uuid() == db.local_host.uuid():
            inPane.AddWrappedTextField(Lang('This host is a Pool Master, so it will be necessary to nominate a new Pool '
                'Master as part of this operation.'))
            inPane.NewLine()
        inPane.AddWrappedTextField(Lang('The ')+Data.Inst().derived.app_name('')+
            Lang(" 'Enter Maintenance Mode' feature provides an alternative way to do this."))
        if len(db.host([])) > 1:
            inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Evacuate Host") } )
    
    @classmethod
    def ActivateHandler(cls):
        pass
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'HOST_EVACUATE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_VM',
                'menupriority' : 400,
                'menutext' : Lang('Evacuate This Host') ,
                'activatehandler' : XSFeatureHostEvacuate.ActivateHandler,
                'statusupdatehandler' : XSFeatureHostEvacuate.StatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureHostEvacuate().Register()
