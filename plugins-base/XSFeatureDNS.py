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

class DNSDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)
        data=Data.Inst()
        
        choiceDefs = [
            ChoiceDef(Lang("Add a Nameserver"), lambda: self.HandleAddRemoveChoice('ADD') ) ]
        
        if len(data.dns.nameservers([])) > 0:
            choiceDefs.append(ChoiceDef(Lang("Remove a Single Nameserver"), lambda: self.HandleAddRemoveChoice('REMOVE') ))
            choiceDefs.append(ChoiceDef(Lang("Remove All Nameservers"), lambda: self.HandleAddRemoveChoice('REMOVEALL') ))
        
        self.addRemoveMenu = Menu(self, None, Lang("Add or Remove Nameserver Entries"), choiceDefs)
        
        choiceDefs = []
        
        for server in Data.Inst().dns.nameservers([]):
            choiceDefs.append(ChoiceDef(server, lambda: self.HandleRemoveChoice(self.removeMenu.ChoiceIndex())))
        
        self.removeMenu = Menu(self, None, Lang("Remove Nameserver Entry"), choiceDefs)
        
        self.ChangeState('INITIAL')

    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("DNS Configuration"))
        pane.AddBox()

    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Add or Remove Nameserver Entries"))
        pane.AddMenuField(self.addRemoveMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsADD(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Enter the Nameserver IP Address"))
        pane.AddInputField(Lang("IP Address", 16),'0.0.0.0', 'address')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)

    def UpdateFieldsREMOVE(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Select Nameserver Entry to Remove"))
        pane.AddMenuField(self.removeMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()
        
    def HandleKeyINITIAL(self, inKey):
        return self.addRemoveMenu.HandleKey(inKey)
     
    def HandleKeyADD(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            Layout.Inst().PopDialogue()
            data=Data.Inst()
            ipaddr = inputValues['address']
            if not IPUtils.ValidateIP(ipaddr):
                Layout.Inst().PushDialogue(InfoDialogue(Lang('Configuration Failed: Invalid IP address')))
            else:
                servers = data.dns.nameservers([])
                servers.append(ipaddr)
                data.NameserversSet(servers)
                self.Commit(Lang("Nameserver")+" "+ ipaddr +" "+Lang("added"))

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
            
    def HandleAddRemoveChoice(self,  inChoice):
        if inChoice == 'ADD':
            self.ChangeState('ADD')
        elif inChoice == 'REMOVE':
            self.ChangeState('REMOVE')
        elif inChoice == 'REMOVEALL':
            Layout.Inst().PopDialogue()
            Data.Inst().NameserversSet([])
            self.Commit(Lang("All nameserver entries deleted"))

    def HandleRemoveChoice(self,  inChoice):
        Layout.Inst().PopDialogue()
        data=Data.Inst()
        servers = data.dns.nameservers([])
        thisServer = servers[inChoice]
        del servers[inChoice]
        data.NameserversSet(servers)
        self.Commit(Lang("Nameserver")+" "+thisServer+" "+Lang("deleted"))
    
    def Commit(self, inMessage):
        try:
            Data.Inst().SaveToResolvConf()
            Layout.Inst().PushDialogue(InfoDialogue( inMessage))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Update failed: ")+Lang(e)))


class XSFeatureDNS:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("DNS Servers"))
    
        inPane.AddTitleField(Lang("Current Nameservers"))
        if len(data.dns.nameservers([])) == 0:
            inPane.AddWrappedTextField(Lang("<No nameservers are configured>"))
        for dns in data.dns.nameservers([]):
            inPane.AddWrappedTextField(str(dns))
        inPane.NewLine()
        inPane.AddWrappedTextField(Lang("Changes to this configuration may be overwritten if any "
                                        "interfaces are configured to use DHCP."))
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Reconfigure DNS"),
            Lang("<F5>") : Lang("Refresh")
        })
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(DNSDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'DNS', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_NETWORK',
                'menupriority' : 200,
                'menutext' : Lang('Add/Remove DNS Servers') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureDNS().Register()
