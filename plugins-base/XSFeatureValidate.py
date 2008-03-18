# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class ValidateDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        data = Data.Inst()

        pane = self.NewPane(DialoguePane(self.parent))
        
        pane.TitleSet(Lang("Validate Server Configuration"))
        pane.AddBox()
    
        if 'vmx' not in data.cpuinfo.flags([]) and 'svm' not in data.cpuinfo.flags([]):
            self.vtResult = Lang("Not Present on CPU")
        else:
            self.vtResult = Lang("Disabled in BIOS")
            for capability in data.host.capabilities([]):
                if re.match(r'hvm', capability):
                    self.vtResult = Lang("OK")
        
        # If there is an SR that allows vdi_create, signal SR OK
        self.srResult = "Not Present"
        for pbd in data.host.PBDs([]):
            sr = pbd.get('SR', {})
            if 'vdi_create' in sr['allowed_operations']:
                self.srResult = 'OK'
        
        self.netResult = "Not OK"
        if len(data.derived.managementpifs([])) > 0:
            managementPIF = data.derived.managementpifs()[0]
            if managementPIF['currently_attached']:
                self.netResult = "OK"
            else:
                self.netResult = "Not connected"

        self.UpdateFields()
        
    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Validation Results"))
        pane.AddStatusField(Lang("VT enabled on CPU", 50), self.vtResult)
        pane.AddStatusField(Lang("Local default Storage Repository", 50), self.srResult)
        pane.AddStatusField(Lang("Management network interface", 50), self.netResult)
        
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )

    def HandleKey(self, inKey):
        handled = False
        if inKey == 'KEY_ENTER':
            Layout.Inst().PopDialogue()
            handled = True

        return handled


class XSFeatureValidate:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Validate Server Configration"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to check the basic configuration of this server."))
 
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Validate")
        } )

    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(ValidateDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'VALIDATE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_TECHNICAL',
                'menupriority' : 100,
                'menutext' : Lang('Validate Server Configuration') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureValidate().Register()
