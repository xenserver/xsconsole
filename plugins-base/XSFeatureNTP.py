# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class NTPDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        data=Data.Inst()
            
        choiceDefs = [
            ChoiceDef(Lang("Enable NTP time synchronization"), lambda: self.HandleInitialChoice('ENABLE') ), 
            ChoiceDef(Lang("Disable NTP time synchronization"), lambda: self.HandleInitialChoice('DISABLE') ),
            ChoiceDef(Lang("Add an NTP server"), lambda: self.HandleInitialChoice('ADD') ) ]
        
        if len(data.ntp.servers([])) > 0:
            choiceDefs.append(ChoiceDef(Lang("Remove a single NTP server"), lambda: self.HandleInitialChoice('REMOVE') ))
            choiceDefs.append(ChoiceDef(Lang("Remove all NTP servers"), lambda: self.HandleInitialChoice('REMOVEALL') ))
            
        if Auth.Inst().IsTestMode():
            # Show Status is a testing-only function
            choiceDefs.append(ChoiceDef(Lang("Show Status (ntpstat)"), lambda: self.HandleInitialChoice('STATUS') ))
            
        self.ntpMenu = Menu(self, None, Lang("Configure Network Time"), choiceDefs)
    
        self.ChangeState('INITIAL')
        
    def BuildPane(self):
        if self.state == 'REMOVE':
            choiceDefs = []
            for server in Data.Inst().ntp.servers([]):
                choiceDefs.append(ChoiceDef(server, lambda: self.HandleRemoveChoice(self.removeMenu.ChoiceIndex())))
        
            self.removeMenu = Menu(self, None, Lang("Remove NTP Server"), choiceDefs)
            
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Configure Network Time"))
        pane.AddBox()
        self.UpdateFields()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Select an Option"))
        pane.AddMenuField(self.ntpMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsADD(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Enter the NTP Server Name or Address"))
        pane.AddWrappedTextField(Lang("NTP servers supplied by DHCP may overwrite values configured here."))
        pane.NewLine()
        pane.AddInputField(Lang("Server", 16), '', 'name')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)

    def UpdateFieldsREMOVE(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select Server Entry To Remove"))
        pane.AddWrappedTextField(Lang("NTP servers supplied by DHCP may overwrite values configured here."))
        pane.NewLine()
        
        pane.AddMenuField(self.removeMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
    
    def HandleKeyINITIAL(self, inKey):
        return self.ntpMenu.HandleKey(inKey)
     
    def HandleKeyADD(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            Layout.Inst().PopDialogue()
            try:
                IPUtils.AssertValidNetworkName(inputValues['name'])
                data=Data.Inst()
                servers = data.ntp.servers([])
                servers.append(inputValues['name'])
                data.NTPServersSet(servers)
                self.Commit(Lang("NTP server")+" "+inputValues['name']+" "+Lang("added"))
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang(e)))
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyREMOVE(self, inKey):
        return self.removeMenu.HandleKey(inKey)
        
    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
            
    def HandleInitialChoice(self,  inChoice):
        data = Data.Inst()
        try:
            if inChoice == 'ENABLE':
                Layout.Inst().TransientBanner(Lang("Enabling..."))
                data.EnableNTP()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("NTP Time Synchronization Enabled")))
            elif inChoice == 'DISABLE':
                Layout.Inst().TransientBanner(Lang("Disabling..."))
                data.DisableNTP()
                Layout.Inst().PushDialogue(InfoDialogue( Lang("NTP Time Synchronization Disabled")))
            elif inChoice == 'ADD':
                self.ChangeState('ADD')
            elif inChoice == 'REMOVE':
                self.ChangeState('REMOVE')
            elif inChoice == 'REMOVEALL':
                Layout.Inst().PopDialogue()
                data.NTPServersSet([])
                self.Commit(Lang("All server entries deleted"))
            elif inChoice == 'STATUS':
                message = data.NTPStatus()+Lang("\n\n(Initial synchronization may take several minutes)")
                Layout.Inst().PushDialogue(InfoDialogue( Lang("NTP Status"), message))

        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Operation Failed"), Lang(e)))
            
        data.Update()

    def HandleRemoveChoice(self,  inChoice):
        Layout.Inst().PopDialogue()
        data=Data.Inst()
        servers = data.ntp.servers([])
        thisServer = servers[inChoice]
        del servers[inChoice]
        data.NTPServersSet(servers)
        self.Commit(Lang("NTP server")+" "+thisServer+" "+Lang("deleted"))
        data.Update()

    def Commit(self, inMessage):
        data=Data.Inst()
        try:
            data.SaveToNTPConf()
            if data.chkconfig.ntpd(False):
                Layout.Inst().TransientBanner(Lang("Restarting NTP daemon with new configuration..."))
                data.RestartNTP()
            Layout.Inst().PushDialogue(InfoDialogue( inMessage))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Update failed: ")+Lang(e)))

        data.Update()

class XSFeatureNTP:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Network Time (NTP)"))
        
        inPane.AddWrappedTextField(Lang("One or more network time servers can be configured to synchronize time between servers.  This is especially important for pooled servers."))
        inPane.NewLine()
        
        if not data.chkconfig.ntpd(False):
            inPane.AddWrappedTextField(Lang("Currently NTP is disabled, and the following servers are configured."))
        else:
            inPane.AddWrappedTextField(Lang("Currently NTP is enabled, and the following servers are configured."))
        
        inPane.NewLine()
        
        servers = data.ntp.servers([])        
        if len(servers) == 0:
            inPane.AddWrappedTextField(Lang("<No servers configured>"))
        else:
            for server in servers:
                inPane.AddWrappedTextField(server)
        
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure"),
            Lang("<F5>") : Lang("Refresh")
        })
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(NTPDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'NTP', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_NETWORK',
                'menupriority' : 300,
                'menutext' : Lang('Network Time (NTP)') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureNTP().Register()
