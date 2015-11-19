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

class PoolNewMasterDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)
        self.ChangeState('SELECT')

    def BuildPaneSELECT(self):
        self.hostMenu = Menu()
        db = HotAccessor()
        for host in [ host for host in db.host if host.uuid() != db.local_pool.master.uuid() ]:
            self.hostMenu.AddChoice(name = host.name_label(Lang('<Unknown>')),
                onAction = self.HandleHostChoice,
                handle = host)
        if self.hostMenu.NumChoices() == 0:
            self.hostMenu.AddChoice(name = Lang('<No Hosts Available>'))

    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.ResetPosition()
        pane.TitleSet(Lang("Designate New Pool Master"))
        pane.AddBox()
        if hasattr(self, 'BuildPane'+self.state):
            handled = getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state

    def UpdateFieldsSELECT(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.AddWrappedBoldTextField(Lang('Please select a new Master for the Pool.')) 
        pane.NewLine()
        pane.AddMenuField(self.hostMenu)

        pane.AddKeyHelpField( { Lang("<Up/Down>") : Lang("Select"), Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang('Press <F8> to confirm the new Pool Master.'))
        pane.AddStatusField(Lang('New Master', 16), self.newMaster.name_label())
        
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()

    def HandleKeySELECT(self, inKey):
        return self.hostMenu.HandleKey(inKey)
    
    def HandleKeyCONFIRM(self, inKey):
        handled = False
        if inKey == 'KEY_F(8)':
            self.Commit()
            handled = True
        return handled

    def HandleKey(self,  inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled

    def HandleHostChoice(self, inChoice):
        self.newMaster = inChoice
        self.ChangeState('CONFIRM')

    def Commit(self):
        hostUtils = Importer.GetResource('HostUtils')
        Layout.Inst().PopDialogue()

        try:
            Layout.Inst().TransientBanner(Lang('Designating New Pool Master...'))
            hostUtils.DoOperation('designate_new_master', self.newMaster.HotOpaqueRef())
            Layout.Inst().PushDialogue(InfoDialogue(Lang("The Pool Master Has Been Changed"), Lang('Please allow several seconds for the change to propagate throughout the Pool.')))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Failed to Designate New Pool Master"), Lang(e)))
            
class XSFeaturePoolNewMaster:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        db = HotAccessor()
        inPane.AddTitleField(Lang('Designate New Pool Master'))
        inPane.AddWrappedTextField(Lang('This option will designate a new host as Master of the Pool. ')+
            Data.Inst().derived.app_name('')+' will temporarily lose its connection to the Pool '
            'as the transition occurs.  The transition may take several seconds.')
        inPane.NewLine()
        
        if db.host(None) is None:
            pass # Info not available, so print nothing
        elif len(db.host([])) > 1:
            if db.local_pool.master.uuid() == db.local_host.uuid():
                inPane.AddWrappedTextField(Lang("This host is the current Pool Master."))
            else:
                masterName = db.host[db.local_pool.master()].name_label(Lang('<Unknown>'))
                inPane.AddWrappedTextField(Lang("The current Master of this Pool is '"+masterName+"'."))
                
            inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Designate New Pool Master") } )
        else:
            inPane.AddWrappedTextField(Lang('This host is not a member of a Pool so this function is not available.'))

    @classmethod
    def ActivateHandler(cls):
        db = HotAccessor()
        if len(db.host([])) <= 1:
            if db.local_pool.name_label(""):
                Layout.Inst().PushDialogue(InfoDialogue(Lang('Option Unavailable'), Lang('No other hosts in Pool.')))
            else:
                Layout.Inst().PushDialogue(InfoDialogue(Lang('Option Unavailable'), Lang('This host is not a Pool member.')))
        else:
            DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(PoolNewMasterDialogue()))
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'POOL_NEWMASTER', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_POOL',
                'menupriority' : 400,
                'menutext' : Lang('Designate a New Pool Master') ,
                'activatehandler' : XSFeaturePoolNewMaster.ActivateHandler,
                'statusupdatehandler' : XSFeaturePoolNewMaster.StatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeaturePoolNewMaster().Register()
