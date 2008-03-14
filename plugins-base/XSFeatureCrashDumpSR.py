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

class CrashDumpSRDialogue(SRDialogue):
    def __init__(self):

        self.custom = {
            'title' : Lang("Select Storage Repository for Crash Dumps"),
            'prompt' : Lang("Please select a Storage Repository"),
            'mode' : 'rw',
            'capabilities' : 'vdi_create'
        }
        SRDialogue.__init__(self) # Must fill in self.custom before calling __init__
        
    def DoAction(self, inSR):
        success = False
        
        Layout.Inst().PopDialogue()
        try:
            Data.Inst().CrashDumpSRSet(inSR)
            Layout.Inst().PushDialogue(InfoDialogue( Lang('Configuration Successful'),
                Lang("Crash Dump SR set to '"+inSR['name_label']+"'")))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration failed: ")+str(e)))
        Data.Inst().Update()

class XSFeatureCrashDumpSR(PlugIn):
    def __init__(self):
        PlugIn.__init__(self)
        
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Specify Crash Dump SR"))
    
        inPane.AddWrappedTextField(Lang("This server can be configured to use a Storage Repository to store Crash Dumps."))
        inPane.NewLine()
    
        if not data.host.crash_dump_sr(False):
            inPane.AddWrappedTextField(Lang("A Crash Dump SR is not configured on this server."))
        else:
            inPane.AddWrappedTextField(Lang("The SR named '")+data.host.crash_dump_sr.name_label()+Lang("' is configured as the Crash Dump SR for this server."))
            
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Specify Crash Dump SR")
        })
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(CrashDumpSRDialogue()))
        
    def Register(self):
        data = Data.Inst()
        Importer.RegisterNamedPlugIn(
            self,
            'CRASH_DUMP_SR', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Specify Crash Dump SR'), # Name of this plugin for plugin list
                'menuname' : 'MENU_DISK',
                'menupriority' : 300,
                'menutext' : Lang('Specify Crash Dump SR') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureCrashDumpSR().Register()
