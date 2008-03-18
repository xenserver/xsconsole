# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSFeatureManagementHelp:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        appName = data.derived.app_name('')
        fullAppName = data.derived.full_app_name('')
        xenServerName = Language.Inst().Branding(data.host.software_version.product_brand('XenServer'))
        inPane.AddTitleField(Lang("Manage Server Using ")+appName)
        
        inPane.AddWrappedTextField(fullAppName+Lang(" is the ")+xenServerName+
            Lang(' administration interface for the Windows(R) operating system.'))
        
        inPane.NewLine()

        inPane.AddWrappedTextField(Lang('Press <Enter> for details of how to download and use ')+appName+
            Lang( " with this server."))

        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("View ")+appName+Lang(" Info")
        } )
    
    @classmethod
    def ActivateHandler(cls):
        data = Data.Inst()
        appName = data.derived.app_name('')
        fullAppName = data.derived.full_app_name('')

        if len(data.derived.managementpifs([])) == 0:
            message = (fullAppName+Lang(' can be downloaded directly from this server once a Management Interface is configured.\r\r')+
            Lang('Please configure a Management Interface using the Network and Management Interface menu item, and then return to this item.'))
        else:
            for pif in data.derived.managementpifs([]):
                message = (Lang('Visit this server at http://') + data.ManagementIP('') +
                    Lang('/ from a web browser on your Windows(R) desktop to download the ')+appName+
                    Lang(' installer.\r\rOnce installed, the same IP address ')+data.ManagementIP('')+
                    Lang(' can be used to connect to this server from the ')+appName+' application.')
            
        Layout.Inst().PushDialogue(InfoDialogue(Lang("Download and Use ")+appName, message))
        
    def Register(self):
        data = Data.Inst()
        appName = data.derived.app_name('')
        fullAppName = data.derived.full_app_name('')
        Importer.RegisterNamedPlugIn(
            self,
            'MANAGEMENT_HELP', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_ROOT',
                'menupriority' : 75,
                'menutext' : Lang('Manage Server Using ')+appName ,
                'statusupdatehandler' : XSFeatureManagementHelp.StatusUpdateHandler,
                'activatehandler' : XSFeatureManagementHelp.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureManagementHelp().Register()
