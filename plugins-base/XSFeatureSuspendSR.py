# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class SuspendSRDialogue(SRDialogue):
    def __init__(self):

        self.custom = {
            'title' : Lang("Select Storage Repository for Suspend"),
            'prompt' : Lang("Please select a Storage Repository"),
            'mode' : 'rw',
            'capabilities' : 'vdi_create'
        }
        SRDialogue.__init__(self) # Must fill in self.custom before calling __init__
        
    def DoAction(self, inSR):
        success = False
        
        Layout.Inst().PopDialogue()
        try:
            Data.Inst().SuspendSRSet(inSR)
            Layout.Inst().PushDialogue(InfoDialogue( Lang('Configuration Successful'),
                Lang("Suspend SR set to '"+inSR['name_label']+"'")))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration failed: ")+str(e)))
        Data.Inst().Update()


class XSFeatureSuspendSR:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Specify Suspend SR"))
    
        inPane.AddWrappedTextField(Lang("This server can be configured to use a Storage Repository for suspend images."))
        inPane.NewLine()
    
        if not data.host.suspend_image_sr(False):
            inPane.AddWrappedTextField(Lang("A Suspend Image SR is not configured on this server."))
        else:
            inPane.AddWrappedTextField(Lang("The SR named '")+data.host.suspend_image_sr.name_label()+Lang("' is configured as the Suspend Image SR for this server."))
            
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Specify Suspend SR")
        })
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(SuspendSRDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'SUSPEND_SR', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_DISK',
                'menupriority' : 200,
                'menutext' : Lang('Specify Suspend SR') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureSuspendSR().Register()
