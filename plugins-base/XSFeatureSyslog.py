# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *
from XSConsolePlugIn import *

class SyslogDialogue(InputDialogue):
    def __init__(self):
        self.custom = {
            'title' : Lang("Change Logging Destination"),
            'info' : Lang("Please enter the hostname or IP address for remote logging (or blank for none)"), 
            'fields' : [ [Lang("Destination", 20), Data.Inst().host.logging.syslog_destination(''), 'destination'] ]
            }
        InputDialogue.__init__(self)

    def HandleCommit(self, inValues):
        Layout.Inst().PushDialogue(BannerDialogue( Lang("Setting Logging Destination...")))
        Layout.Inst().Refresh()
        Layout.Inst().DoUpdate()
        
        Data.Inst().LoggingDestinationSet(inValues['destination'])
        Data.Inst().Update()
        
        Layout.Inst().PopDialogue()
        
        if inValues['destination'] == '':
            message = Lang("Remote logging disabled.")
        else:
            message = Lang("Logging destination set to '")+inValues['destination'] + "'."
        return Lang('Logging Destination Change Successful'), message        


class XSFeatureSyslog(PlugIn):
    def __init__(self):
        PlugIn.__init__(self)
        
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Remote Logging (syslog)"))
    
        if data.host.logging.syslog_destination('') == '':
            inPane.AddWrappedTextField(Lang("Remote logging is not configured on this host.  Press <Enter> to activate and set a destination address."))
        else:
            inPane.AddWrappedTextField(Lang("The remote logging destination for this host is"))
            inPane.NewLine()
            inPane.AddWrappedTextField(data.host.logging.syslog_destination())
        
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure"),
            Lang("<F5>") : Lang("Refresh")
        })
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(SyslogDialogue()))
        
    def Register(self):
        data = Data.Inst()
        Importer.RegisterNamedPlugIn(
            self,
            'SYSLOG', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Remote Logging (syslog)'), # Name of this plugin for plugin list
                'menuname' : 'MENU_REMOTE',
                'menupriority' : 100,
                'menutext' : Lang('Remote Logging (syslog)') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureSyslog().Register()
