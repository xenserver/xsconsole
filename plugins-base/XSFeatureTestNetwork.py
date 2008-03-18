# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class TestNetworkDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Test Network Configuration"))
        pane.AddBox()
        
        gatewayName = Data.Inst().ManagementGateway()
        if gatewayName is None:
            gatewayName = Lang('Unknown')
        
        self.testMenu = Menu(self, None, Lang("Select Test Type"), [
            ChoiceDef(Lang("Ping local address 127.0.0.1"), lambda: self.HandleTestChoice('local') ), 
            ChoiceDef(Lang("Ping gateway address")+" ("+gatewayName+")", lambda: self.HandleTestChoice('gateway') ), 
            ChoiceDef(Lang("Ping citrixxenserver.com"), lambda: self.HandleTestChoice('xenserver') ), 
            ChoiceDef(Lang("Ping custom address"), lambda: self.HandleTestChoice('custom') ), 
            ])
    
        self.customIP = '0.0.0.0'
        self.state = 'INITIAL'
    
        self.UpdateFields()

    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select Test"))
        pane.AddMenuField(self.testMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFieldsCUSTOM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Enter hostname or IP address to ping"))
        pane.AddInputField(Lang("Address",  16), self.customIP, 'address')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Exit") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
            
    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = self.testMenu.HandleKey(inKey)
        if not handled and inKey == 'KEY_LEFT':
            Layout.Inst().PopDialogue()
            handled = True
        return handled
        
    def HandleKeyCUSTOM(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            self.customIP = inputValues['address']
            self.DoPing(self.customIP)
            self.state = 'INITIAL'
            
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled
        
    def HandleTestChoice(self,  inChoice):
        pingTarget = None
        custom = False
        if inChoice == 'local':
            pingTarget = '127.0.0.1'
        elif inChoice == 'gateway':
            pingTarget = Data.Inst().ManagementGateway()
        elif inChoice == 'xenserver':
            pingTarget = 'citrixxenserver.com'
        else:
            custom = True

        if custom:
            self.state = 'CUSTOM'
            self.UpdateFields()
            self.Pane().InputIndexSet(0)
        else:
            self.DoPing(pingTarget)

    def DoPing(self, inAddress):
        success = False
        output = 'Cannot determine address to ping'
            
        if inAddress is not None:
            try:
                (success,  output) = Data.Inst().Ping(inAddress)
            except Exception,  e:
                output = Lang(e)
            
        if success:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Ping successful"), output))
        else:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Ping failed"), output))
        

class XSFeatureTestNetwork:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        inPane.AddTitleField(Lang("Test Network"))
    
        inPane.AddWrappedTextField(Lang(
            "This option will test the configured network using ping."))
        
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Test Network") })
        
    @classmethod
    def ActivateHandler(cls):
        Layout.Inst().PushDialogue(TestNetworkDialogue())
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'TEST_NETWORK', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_NETWORK',
                'menupriority' : 400,
                'menutext' : Lang('Test Network') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureTestNetwork().Register()
