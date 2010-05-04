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

class PoolEjectDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)
        self.ChangeState('WARNING')

    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.ResetPosition()
        pane.TitleSet(Lang("Remove Host from Pool"))
        pane.AddBox()
        if hasattr(self, 'BuildPane'+self.state):
            handled = getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state

    def UpdateFieldsWARNING(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddWarningField(Lang('WARNING'))
        
        pane.AddWrappedBoldTextField(Lang('Removing this host from its Pool will permanently delete and reinitialize '
            'all local Storage Repositories on this host.  The data in local Storage Repositories will be lost, and '
           'this host will immediately reboot.')) 
        
        pane.NewLine()
        pane.AddWrappedBoldTextField(Lang('Press <F8> to continue.'))
        
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang('Press <Enter> to remove this host from the Pool.'))

        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()

    def HandleKeyWARNING(self, inKey):
        handled = False
        if inKey == 'KEY_F(8)':
            self.ChangeState('CONFIRM')
            handled = True
        return handled
    
    def HandleKeyCONFIRM(self, inKey):
        handled = False
        if inKey == 'KEY_ENTER':
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

    def Commit(self):
        hostUtils = Importer.GetResource('HostUtils')
        Layout.Inst().PopDialogue()

        try:
            Layout.Inst().TransientBanner(Lang('Removing This Host from the Pool...'))
            hostUtils.DoOperation('eject', HotAccessor().local_host_ref())
            Layout.Inst().ExitBannerSet(Lang('Removal Successful.  This Host Will Now Reboot...'))
            Layout.Inst().ExitCommandSet('/bin/sleep 120')
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Failed to Remove Host from Pool"), Lang(e)))
            
class XSFeaturePoolEject:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        db = HotAccessor()
        inPane.AddTitleField(Lang('Remove This Host from the Pool'))
        inPane.AddWrappedTextField(Lang('Removing this host from its Pool will permanently delete and reinitialize '
            'all local Storage Repositories on this host.  The data in local Storage Repositories will be lost, and '
            'this host will immediately reboot.'))
        inPane.NewLine()
        
        if db.host(None) is None:
            pass # Info not available, so print nothing
        elif len(db.host([])) > 1:
            if db.local_pool.master.uuid() == db.local_host.uuid():
                inPane.AddWrappedTextField(Lang('This host is the Master of the Pool and cannot be removed until '
                    'another host is designated as Master.'))
            else:
                inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Remove Host from Pool") } )
        else:
            inPane.AddWrappedTextField(Lang('This host is not a member of a Pool so cannot be removed.'))

    @classmethod
    def ActivateHandler(cls):
        db = HotAccessor()
        if len(db.host([])) <= 1:
            local_pool_name = db.local_pool.name_label("")
            if local_pool_name:
                Layout.Inst().PushDialogue(InfoDialogue(Lang('Option Unavailable'), Lang('This host is the Master of pool "%s", '
                'and cannot be removed until another host is designated as Master.' % local_pool_name)))
            else:
                Layout.Inst().PushDialogue(InfoDialogue(Lang('Option Unavailable'), Lang('This host is not a Pool member.')))
        elif db.local_pool.master.uuid() == db.local_host.uuid():
            Layout.Inst().PushDialogue(InfoDialogue(Lang('Option Unavailable'), Lang('This host is the Pool Master, '
                'and cannot be removed until another host is designated as Master.')))
        else:
            DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(PoolEjectDialogue()))
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'POOL_EJECT', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_POOL',
                'menupriority' : 300,
                'menutext' : Lang('Remove This Host from the Pool') ,
                'activatehandler' : XSFeaturePoolEject.ActivateHandler,
                'statusupdatehandler' : XSFeaturePoolEject.StatusUpdateHandler
            }
        )

# Register this plugin when module is imported
XSFeaturePoolEject().Register()
