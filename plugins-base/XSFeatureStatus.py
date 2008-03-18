# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureStatus:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()

        inPane.AddWrappedTextField(data.dmi.system_manufacturer())
        inPane.AddWrappedTextField(data.dmi.system_product_name())
        inPane.NewLine()
        inPane.AddWrappedTextField(Language.Inst().Branding(data.host.software_version.product_brand()) + ' ' +
            data.derived.fullversion())
        inPane.NewLine()
        inPane.AddTitleField(Lang("Management Network Parameters"))
        
        if len(data.derived.managementpifs([])) == 0:
            inPane.AddWrappedTextField(Lang("<No network configured>"))
        else:
            inPane.AddStatusField(Lang('Device', 16), data.derived.managementpifs()[0]['device'])
            inPane.AddStatusField(Lang('IP address', 16), data.ManagementIP(''))
            inPane.AddStatusField(Lang('Netmask', 16),  data.ManagementNetmask(''))
            inPane.AddStatusField(Lang('Gateway', 16),  data.ManagementGateway(''))
    
        inPane.AddKeyHelpField( { Lang("<F5>") : Lang("Refresh")})

    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'STATUS', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_ROOT',
                'menupriority' : 50,
                'menutext' : Lang('Status Display'),
                'statusupdatehandler' : XSFeatureStatus.StatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureStatus().Register()
