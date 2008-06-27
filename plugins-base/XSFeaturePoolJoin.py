# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class PoolJoinDialogue(Dialogue):
    def __init__(self, inForce):
        Dialogue.__init__(self)
        self.force = inForce
        if self.force:
            self.ChangeState('FORCEWARNING')
        else:
            self.ChangeState('GATHER')

    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.ResetPosition()
        pane.TitleSet(Lang("Join A Resource Pool"))
        pane.AddBox()
        if hasattr(self, 'BuildPane'+self.state):
            handled = getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state

    def UpdateFieldsFORCEWARNING(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.AddWarningField(Lang('WARNING'))
        
        pane.AddWrappedBoldTextField(Lang('Forcing a host to join a Pool will ignore incompatibilities between '
            'hosts, which can result in serious problems.  In particular, Virtual Machine migration between incompatible hosts WILL cause crashes and data corruption.')) 
        
        pane.NewLine()
        pane.AddWrappedTextField(Lang('If you accept these consequences, press <F8> to continue.'))
        
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsGATHER(self):
        pane = self.Pane()
        pane.ResetFields()

        pane.AddWrappedBoldTextField(Lang("Please enter details for the Pool Master."))
        pane.NewLine()
        pane.AddInputField(Lang('Hostname', 16), '', 'hostname')
        pane.AddInputField(Lang('Username', 16), '', 'username')
        pane.AddPasswordField(Lang('Password', 16), '', 'password')
        
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("Next/OK"), Lang("<Esc>") : Lang("Cancel"), Lang("<Tab>") : Lang("Next") })
        if pane.InputIndex() is None:
            pane.InputIndexSet(0) # Activate first field for input
    
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang('Press <F8> to join the Pool with parameters listed below.'))
        pane.AddStatusField(Lang('Hostname', 16), self.params['hostname'])
        pane.AddStatusField(Lang('Username', 16), self.params['username'])
        pane.AddStatusField(Lang('Password', 16), '*'*len(self.params['password']))

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()

    def HandleKeyFORCEWARNING(self, inKey):
        handled = False
        if inKey == 'KEY_F(8)':
            self.ChangeState('GATHER')
            handled = True
        return handled

    def HandleKeyGATHER(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                self.params = pane.GetFieldValues()
                self.ChangeState('CONFIRM')
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return True
    
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

    def Commit(self):
        hostUtils = Importer.GetResource('HostUtils')
        Layout.Inst().PopDialogue()

        try:
            Layout.Inst().TransientBanner(Lang('Joining Pool...'))
            if self.force:
                op = 'join_force'
            else:
                op = 'join'
            task = hostUtils.AsyncOperation(op, HotAccessor().local_host_ref(),
                self.params['hostname'], self.params['username'], self.params['password'])
            Layout.Inst().PushDialogue(ProgressDialogue(task, Lang("Joining Pool with Master '")+self.params['hostname']+"'"))
    
        except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Host Failed To Join The Pool"), Lang(e)))
            
class XSFeaturePoolJoin:
    @classmethod
    def StatusUpdateHandler(cls, inPane, inForce = False):
        db = HotAccessor()
        if inForce:
            inPane.AddTitleField("Join a Resource Pool (forced)")
        else:
            inPane.AddTitleField("Join a Resource Pool")
            
        inPane.AddWrappedTextField(Lang('Joining a Resource Pool will allow this host to share '
            'Storage Repositories and migrate Virtual Machines between hosts in the Pool.'))
        inPane.NewLine()
        
        if db.host(None) is None:
            pass # Info not available, so print nothing
        elif len(db.host([])) > 1:
            numStr = str(len(db.host([]))) + Language.Quantity(' host', len(db.host([])))
            if db.local_pool.master.uuid() == db.local_host.uuid():
                inPane.AddWrappedTextField(Lang('This host is the Master of a Pool of ')+numStr+Lang(', and must leave the Pool before it can join another.'))
            else:
                try:
                    masterName = db.host[db.local_pool.master()].name_label(Lang('<Unknown>'))
                except:
                    masterName = Lang('<Unknown>')
                inPane.AddWrappedTextField(Lang("This host is already part of a Pool of ")+numStr+Lang(", and must leave the Pool before it can join another.  The Pool Master is '"+masterName+"'."))

            inPane.NewLine()
        else:
            inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Join Pool") } )
        if inForce:
            inPane.AddWarningField(Lang('Forcing a host to join a pool is a dangerous operation and may lead to '
                'ongoing Virtual Machine and data corruption.'))
                    
    @classmethod
    def ActivateHandler(cls):
        if len(HotAccessor().host([])) > 1:
            Layout.Inst().PushDialogue(InfoDialogue(Lang('Option Unavailable'),
                Lang('This host is already part of a Pool and cannot join another.')))
        else:
            DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(PoolJoinDialogue(False)))
    
    @classmethod
    def ForceActivateHandler(cls):
        if len(db.host([])) > 1:
            Layout.Inst().PushDialogue(InfoDialogue(Lang('Option Unavailable'),
                Lang('This host is already part of a Pool and cannot join another.')))
        else:
            DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(PoolJoinDialogue(True)))
    
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'POOL_JOIN', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_POOL',
                'menupriority' : 100,
                'menutext' : Lang('Join a Resource Pool') ,
                'activatehandler' : XSFeaturePoolJoin.ActivateHandler,
                'statusupdatehandler' : XSFeaturePoolJoin.StatusUpdateHandler
            }
        )

        Importer.RegisterNamedPlugIn(
            self,
            'POOL_JOINFORCE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_POOL',
                'menupriority' : 200,
                'menutext' : Lang('Join a Resource Pool (Forced)') ,
                'activatehandler' : XSFeaturePoolJoin.ForceActivateHandler,
                'statusupdatehandler' : lambda inPane: XSFeaturePoolJoin.StatusUpdateHandler(inPane, True)
            }
        )


# Register this plugin when module is imported
XSFeaturePoolJoin().Register()
