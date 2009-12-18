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

class SRUtils:
    operationNames = {
        'forget' : Struct(name = Lang("Forget"), priority = 10),
        'plug' : Struct(name = Lang("Plug"), priority = 20),
        'unplug' : Struct(name = Lang("Unplug"), priority = 30),
        'xsconsole-detach': Struct(name = Lang('Detach'), warning=Lang('After Detaching this Storage Repository, Virtual Disks contained within it will become inaccessible.  To reattach it, the correct device configuration will be needed.'), priority = 100),
        'xsconsole-destroy': Struct(name = Lang('Destroy'), warning=Lang('Destroying this Storage Repository will permanently remove all associated Virtual Disks and the data contained on the Virtual Disks.  This operation cannot be undone.'), priority = 200),

        'none' : Struct(name = Lang("No Operation"), priority = 300),
    }
    
    @classmethod
    def AllowedOperations(cls):
        if Auth.Inst().IsTestMode():
            # Allow a lot more in test mode
            retVal = cls.operationNames.keys()
        else:
            retVal = ['forget', 'xsconsole-detach','xsconsole-destroy']
        return retVal
        
    @classmethod
    def AsyncOperation(cls, inOperation, inSRHandle, inParam0 = None):
        task = None
        if inOperation == 'xsconsole-detach': # This is a synthetic operation that unplugs then forgets
            cls.DoOperation('unplug', inSRHandle)

            sr = HotAccessor().sr[inSRHandle]
            storedError = None
            for pbd in sr.PBDs:
                try:
                    Task.Sync(lambda x: x.xenapi.PBD.destroy(pbd.HotOpaqueRef().OpaqueRef()))
                except Exception, e:
                    storedError = e
                    
            if storedError is not None:
                # Raise one exception, even if more than one occured
                raise storedError
                
        elif inOperation == 'xsconsole-destroy': # This is a synthetic operation that unplugs then destroys
            cls.DoOperation('unplug', inSRHandle)
            task = cls.AsyncOperation('destroy', inSRHandle)
        elif inOperation == 'destroy':
            task = Task.New(lambda x: x.xenapi.Async.SR.destroy(inSRHandle.OpaqueRef()))
        elif inOperation == 'forget':
            task = Task.New(lambda x: x.xenapi.Async.SR.forget(inSRHandle.OpaqueRef()))
        elif inOperation == 'plug':
            sr = HotAccessor().sr[inSRHandle]
            storedError = None
            for pbd in sr.PBDs:
                try:
                    Task.Sync(lambda x: x.xenapi.PBD.plug(pbd.HotOpaqueRef().OpaqueRef()))
                except Exception, e:
                    storedError = e
                    
            if storedError is not None:
                # Raise one exception, even if more than one occured
                raise storedError
                
        elif inOperation == 'unplug':
            unplugged = []
            try:
                sr = HotAccessor().sr[inSRHandle]
                for pbd in sr.PBDs:
                    if pbd.currently_attached(True):
                        unplugged.append(pbd)
                        Task.Sync(lambda x: x.xenapi.PBD.unplug(pbd.HotOpaqueRef().OpaqueRef()))
            except: # On failure, attempt to undo what we've done
                for pbd in unplugged:
                    try:
                        Task.Sync(lambda x: x.xenapi.PBD.plug(pbd.HotOpaqueRef().OpaqueRef()))
                    except Exception, e:
                        XSLogFailure('SR undo failed', e)
                raise # Reraise the original exception
                
                
        elif inOperation == 'none':
            pass
        else:
            raise Exception("Unknown SR operation "+str(inOperation))
        
        return task
        
    @classmethod
    def DoOperation(cls, inOperation, inSRHandle):
        task = cls.AsyncOperation(inOperation, inSRHandle)
        
        if task is not None:
            while task.IsPending():
                time.sleep(0.1)
            task.RaiseIfFailed()

    @classmethod
    def OperationStruct(cls, inOperation):
        retVal = cls.operationNames.get(inOperation, None)
        if retVal is None:
            raise Exception("Unknown SR operation "+str(inOperation))
        return retVal

    @classmethod
    def OperationName(cls, inOperation):
        return cls.OperationStruct(inOperation).name

    @classmethod
    def OperationPriority(cls, inOperation):
        return cls.OperationStruct(inOperation).priority

    @classmethod
    def OperationWarning(cls, inOperation):
        operation = cls.OperationStruct(inOperation)
        if hasattr(operation, 'warning'):
            retVal = operation.warning
        else:
            retVal = None
        return retVal

    @classmethod
    def SRFlags(cls, inSR):
        retVal = []
        if inSR.uuid() in [ pool.default_SR.uuid() for pool in HotAccessor().pool ]:
            retVal.append('default')
        if inSR.uuid() in [ pool.suspend_image_SR.uuid() for pool in HotAccessor().pool ]:
            retVal.append('suspend')
        if inSR.uuid() in [ pool.crash_dump_SR.uuid() for pool in HotAccessor().pool ]:
            retVal.append('crashdump')
        return retVal
        
    @classmethod
    def AnnotatedName(cls, inSR):
        retVal = inSR.name_label(Lang('<Unknown>'))
        flags = cls.SRFlags(inSR)
        if 'default' in flags:
            retVal += Lang(' (default)')
        return retVal

    @classmethod
    def TypeName(cls, inSRType):
        return LangFriendlyNames.Translate('Label-SR.SRTypes-'+inSRType)
    
    @classmethod
    def IsDetachable(cls, inSR):
        # Use same criteria as XenCenter for detach (from IsDetachable in SR.cs)
        if 'forget' in inSR.allowed_operations() and inSR.type() in ('iso', 'lvmoiscsi', 'nfs', 'netapp', 'lvmohba', 'equal'):
            retVal = True
        else:
            retVal = False
        return retVal

class SRControlDialogue(Dialogue):
    def __init__(self, inSRHandle):
        self.srHandle = inSRHandle
        Dialogue.__init__(self)
        self.operation = 'none'
        self.extraInfo = []
        self.opParams = []
        sr = HotAccessor().sr[self.srHandle]
        allowedOps = sr.allowed_operations([])[:]
        # Use same criteria as XenCenter for detach (from IsDetachable in SR.cs)
        if SRUtils.IsDetachable(sr):
            if len(sr.PBDs()) != 0:
                # Attached SR
                allowedOps += ['xsconsole-detach', 'xsconsole-destroy'] 
                if 'forget' in allowedOps:
                    allowedOps.remove('forget') # Allow forget for detached SRs only
        else:
            if 'forget' in allowedOps:
                allowedOps.remove('forget') # Don't allow forget for non-detachable SRs
            
        choiceList = [ name for name in allowedOps if name in SRUtils.AllowedOperations() ]
        
        choiceList.sort(lambda x, y: cmp(SRUtils.OperationPriority(x), SRUtils.OperationPriority(y)))
        
        self.controlMenu = Menu()
        for choice in choiceList:
            self.controlMenu.AddChoice(name = SRUtils.OperationName(choice),
                onAction = self.HandleControlChoice,
                handle = choice)
            
        if self.controlMenu.NumChoices() == 0:
            self.controlMenu.AddChoice(name = Lang('<No Operations Available>'))

        self.ChangeState('INITIAL')
        
    def BuildPane(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Storage Repository Control"))
        pane.AddBox()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()

        sr = HotAccessor().sr[self.srHandle]
        srName = sr.name_label(None)
        if srName is None:
            pane.AddTitleField(Lang("The Virtual Machine is no longer present"))
        else:
            pane.AddTitleField(Lang("Please select an operation to perform on '"+srName+"'"))
        pane.AddMenuField(self.controlMenu)
        if sr.type() == 'lvm':
            pane.AddWrappedTextField(Lang('Local Storage cannot be detached or destroyed because XenServer configuration information is also stored on the local disk.'))
        
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()

        sr = HotAccessor().sr[self.srHandle]
        srName = sr.name_label(None)
        if srName is None:
            pane.AddTitleField(Lang("The Storage Repository is no longer present"))
        else:
            warning = SRUtils.OperationWarning(self.operation)
            if warning is not None:
                pane.AddWarningField(Lang('WARNING'))
                pane.AddWrappedBoldTextField(warning)
                pane.NewLine()
            pane.AddWrappedBoldTextField(Lang('Press <F8> to confirm this operation'))
            pane.NewLine()
            pane.AddStatusField(Lang("Operation", 20), SRUtils.OperationName(self.operation))
            pane.AddStatusField(Lang("Storage Repository", 20), srName)
            for values in self.extraInfo:
                pane.AddStatusField(values[0], values[1])
                
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state

    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
        self.UpdateFields()
    
    def HandleKeyINITIAL(self, inKey):
        return self.controlMenu.HandleKey(inKey)

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
    
    def HandleControlChoice(self, inChoice):
        self.operation = inChoice
        self.ChangeState('CONFIRM')
        
    def Commit(self):
        Layout.Inst().PopDialogue()

        operationName = SRUtils.OperationName(self.operation)
        srName = HotAccessor().sr[self.srHandle].name_label(Lang('<Unknown>'))
        messagePrefix = operationName + Lang(' operation on ') + srName + ' '
        Layout.Inst().TransientBanner(messagePrefix+Lang('in progress...'))
        try:
            task = SRUtils.DoOperation(self.operation, self.srHandle, *self.opParams)
            Layout.Inst().PushDialogue(InfoDialogue(messagePrefix + Lang("successful"), ))

        except Exception, e:
            self.ChangeState('INITIAL')
            Layout.Inst().PushDialogue(InfoDialogue(messagePrefix + Lang("failed"), Lang(e)))

class XSFeatureSRCommon:
    def Register(self):
        Importer.RegisterResource(
            self,
            'SR_UTILS', # Name of this item for replacement, etc.
            {
                'SRUtils' : SRUtils
            }
        )
        Importer.RegisterResource(
            self,
            'SR_CONTROLDIALOGUE', # Name of this item for replacement, etc.
            {
                'SRControlDialogue' : SRControlDialogue
            }
        )

# Register this plugin when module is imported
XSFeatureSRCommon().Register()
