# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class RemoteDBDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        self.useMenu = Menu(self, None, Lang("Choose Option"), [
            ChoiceDef(Lang("Use existing database"), lambda: self.HandleUseChoice('USE')),
            ChoiceDef(Lang("Format disk and create new database"), lambda: self.HandleUseChoice('FORMAT')),
            ChoiceDef(Lang("Cancel"), lambda: self.HandleUseChoice('CANCEL'))
        ] )            

        self.ChangeState('WARNING')

    def IQNString(self, inIQN, inLUN = None):
        if inLUN is None or int(inLUN) > 999: # LUN not present or more than 3 characters
            retVal = "TGPT %-4.4s %-60.60s" % (inIQN.tgpt[:4], inIQN.name[:60])
        else:
            retVal = "TGPT %-4.4s %-52.52s LUN %-3.3s" % (inIQN.tgpt[:4], inIQN.name[:52], str(inLUN)[:3])
        
        return retVal

    def BuildPaneBase(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Remote Database Configuration"))
        pane.AddBox()
    
    def BuildPaneWARNING(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def BuildPaneINITIAL(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def BuildPaneREMOVECURRENT(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def BuildPaneCHOOSEIQN(self):
        self.BuildPaneBase()

        choiceDefs = []
        
        for iqn in self.probedIQNs:
            choiceDefs.append(ChoiceDef(self.IQNString(iqn), lambda: self.HandleIQNChoice(self.iqnMenu.ChoiceIndex())))

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef("<No IQNs discovered>", lambda: None))
            
        self.iqnMenu = Menu(self, None, Lang("Select IQN"), choiceDefs)

        self.UpdateFields()

    def BuildPaneCHOOSELUN(self):
        self.BuildPaneBase()

        choiceDefs = []
        
        for lun in self.probedLUNs:
            choiceDefs.append(ChoiceDef("LUN "+str(lun), lambda: self.HandleLUNChoice(self.lunMenu.ChoiceIndex())))

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef("<No LUNs discovered>", lambda: None))
            
        self.lunMenu = Menu(self, None, Lang("Select LUN"), choiceDefs)

        self.UpdateFields()

    def BuildPaneCREATEDB(self):
        self.BuildPaneBase()
        self.UpdateFields()
        
    def BuildPaneUSEDB(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def ChangeState(self, inState):
        self.state = inState
        getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
        
    def UpdateFieldsWARNING(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWarningField(Lang("WARNING"))
        pane.AddWrappedBoldTextField(Lang("Please ensure that no Virtual Machines are running on this host "
            "before continuing.  If this host is in a Pool, the remote database should be configured "
            "only on the Pool master.  The specified remote database iSCSI LUN must be configured on "
            "no more than one host at all times, must not be used for any other purpose, and will not be "
            "usable as a Storage Repository."
            ))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Continue"), Lang("<Esc>") : Lang("Cancel") } )        

    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        data = Data.Inst()
        pane.ResetFields()
        
        pane.AddWrappedTextField(Lang("Please enter the configuration details.  Leave the hostname blank to specify no remote database."))
        pane.NewLine()
        
        pane.AddInputField(Lang("Initiator IQN",  26), data.remotedb.defaultlocaliqn(''), 'localiqn')
        pane.AddInputField(Lang("Port number",  26), '3260', 'port')
        pane.AddInputField(Lang("Hostname of iSCSI target",  26), '', 'remotehost')
        pane.AddInputField(Lang("Username",  26), data.remotedb.username(''), 'username')
        pane.AddPasswordField(Lang("Password",  26), data.remotedb.password(''), 'password')
                
        pane.AddKeyHelpField( {
            Lang("<Esc>") : Lang("Cancel"),
            Lang("<Enter>") : Lang("Next/OK"),
            Lang("<Tab>") : Lang("Next")
        } )

        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
    
    def UpdateFieldsREMOVECURRENT(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("The current remote database must be removed before a new configuration "
            "can be entered.  Would you like to proceed?"))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Remove Current Remote Database"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCHOOSEIQN(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select from the list of discovered IQNs"))
        pane.AddMenuField(self.iqnMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsCHOOSELUN(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please select a LUN from the chosen IQN"))
        pane.AddMenuField(self.lunMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
            
    def UpdateFieldsCREATEDB(self):
        pane = self.Pane()
        pane.ResetFields()
        
        if self.dbPresent or self.dbPresent is None: # Database is present but the user has chosen not to use it
            pane.AddWrappedBoldTextField(Lang("Please confirm that you would like to format the following disk.  Data currently on this disk cannot be recovered after this step."))
        else:
            pane.AddWrappedBoldTextField(Lang("No database can be found on the remote disk.  Would you like to format it and prepare a new database?  Data currently on this disk cannot be recovered after this step."))
        pane.NewLine()
        pane.AddWrappedBoldTextField(Lang("Remote iSCSI disk"))
        pane.AddWrappedTextField(self.IQNString(self.chosenIQN, self.chosenLUN))

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Format and Create"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsUSEDB(self):
        pane = self.Pane()
        pane.ResetFields()
        
        if self.dbPresent is None: # i.e. we don't know
            pane.AddWrappedBoldTextField(Lang("Would you like to use a database already on the disk, or format it and create a new database?"))
        else:
            pane.AddWrappedBoldTextField(Lang("A database is already present on the remote disk.  Please select an option."))
        pane.NewLine()
        pane.AddWrappedBoldTextField(Lang("Remote iSCSI disk"))
        pane.AddWrappedTextField(self.IQNString(self.chosenIQN, self.chosenLUN))
        pane.NewLine()
        pane.AddMenuField(self.useMenu)
        
        pane.AddKeyHelpField( { Lang("<Up/Down>") : Lang("Select"), Lang("<Enter>") : Lang("OK") } )

    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def HandleKeyWARNING(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            if Data.Inst().remotedb.is_on_remote_storage(False):
                self.ChangeState('REMOVECURRENT')
            else:
                self.ChangeState('INITIAL')
            handled = True
            
        return handled
    
    def HandleKeyINITIAL(self, inKey):
        handled = True
        pane = self.Pane()

        if inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                self.newConf = pane.GetFieldValues()
                if self.newConf['remotehost'] == '':
                    self.HandleUseChoice('REMOVE')
                else:
                    try:
                        Layout.Inst().TransientBanner(Lang("Probing for IQNs..."))
                        self.probedIQNs = RemoteDB.Inst().ProbeIQNs(self.newConf)
                        self.ChangeState('CHOOSEIQN')
                    except Exception, e:
                        pane.InputIndexSet(None)
                        Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
                    
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled

    def HandleKeyREMOVECURRENT(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            Layout.Inst().TransientBanner(Lang("Removing current database..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    RemoteDB.Inst().ConfigureNoDB()
                    self.ChangeState('INITIAL')
                except Exception, e:
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
            finally:
                Data.Inst().StartXAPI()
                Data.Inst().Update()
            handled = True
            
        return handled

    def HandleKeyCHOOSEIQN(self, inKey):
        return self.iqnMenu.HandleKey(inKey)

    def HandleKeyCHOOSELUN(self, inKey):
        return self.lunMenu.HandleKey(inKey)
    
    def HandleKeyUSEDB(self, inKey):
        return self.useMenu.HandleKey(inKey)
        
    def HandleKeyCREATEDB(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            Layout.Inst().TransientBanner(Lang("Formatting..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    self.dbPresent = RemoteDB.Inst().FormatLUN(self.newConf, self.chosenIQN, self.chosenLUN)
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue(
                        Lang("Format, Creation, and Configuration Successful")))
                except Exception, e:
                    Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
            finally:
                Data.Inst().StartXAPI()
                Data.Inst().Update()
            handled = True
            
        return handled
    
    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
        
    def HandleIQNChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOMIQN')
        else:
            Layout.Inst().TransientBanner(Lang("Probing for LUNs..."))
            self.chosenIQN = self.probedIQNs[inChoice]
            try:
                self.probedLUNs = RemoteDB.Inst().ProbeLUNs(self.newConf, self.chosenIQN)
            except Exception, e:
                self.probedLUNs = []
        
            self.ChangeState('CHOOSELUN')

    def HandleLUNChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOMLUN')
        else:
            Layout.Inst().TransientBanner(Lang("Scanning target LUN..."))
            
            self.chosenLUN = self.probedLUNs[inChoice]

            self.dbPresent = RemoteDB.Inst().TestLUN(self.newConf, self.chosenIQN, self.chosenLUN)
            
            if self.dbPresent or self.dbPresent is None:
                self.ChangeState('USEDB')
            else:
                self.ChangeState('CREATEDB')

    def HandleUseChoice(self, inChoice):
        if inChoice == 'USE':
            Layout.Inst().TransientBanner(Lang("Configuring Remote Database..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    self.dbPresent = RemoteDB.Inst().ReadyForUse(self.newConf, self.chosenIQN, self.chosenLUN)
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue(
                        Lang("Configuration Successful")))
                except Exception, e:
                    Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
            finally:
                Data.Inst().StartXAPI()
                Data.Inst().Update()
        elif inChoice == 'REMOVE':
            Layout.Inst().TransientBanner(Lang("Configuring for Operation Without a Remote Database..."))
            Data.Inst().StopXAPI()
            try:
                try:
                    RemoteDB.Inst().ConfigureNoDB()
                    self.dbPresent = None
                    Layout.Inst().PopDialogue()
                    Layout.Inst().PushDialogue(InfoDialogue(
                        Lang("Configuration Successful")))
                except Exception, e:
                    Layout.Inst().PushDialogue(InfoDialogue( Lang("Failed: ")+Lang(e)))
            finally:
                Data.Inst().StartXAPI()
                Data.Inst().Update()
        elif inChoice == 'FORMAT':
            self.ChangeState('CREATEDB')
        else:
            Layout.Inst().PopDialogue()


class XSFeatureRemoteDB:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Setup Remote Database"))

        description = "A remote database, if configured, is used to store xapi configuration settings that are written frequently.  The copy of the xapi database on the FLASH media is updated less frequently as it is rate-limited to reduce writes to the device.  This setting is particularly useful for diskless servers."
            
        if not data.remotedb.is_on_remote_storage(False):
            inPane.AddWrappedTextField(Lang(description))
            inPane.NewLine()
            inPane.AddWrappedTextField(Lang("A remote database is not configured on this server."))
            inPane.AddKeyHelpField( {
                Lang("<Enter>") : Lang("Configure Remote DB")
            })
        else:
            inPane.AddWrappedTextField(Lang("A remote database is configured for this server on an iSCSI LUN."))
            inPane.NewLine()
            inPane.AddStatusField(Lang('Server', 10), data.remotedb.target()+":"+data.remotedb.port())
            inPane.AddStatusField(Lang('LUN',10), data.remotedb.lun())
            if data.remotedb.username('') != '':
                inPane.AddStatusField(Lang('Username', 10), data.remotedb.username())
            inPane.NewLine()
            inPane.AddTitleField(Lang("Initiator IQN"))
            inPane.AddWrappedTextField(data.remotedb.localiqn())
            inPane.NewLine()
            inPane.AddTitleField(Lang("Target IQN"))
            inPane.AddWrappedTextField(data.remotedb.remoteiqn())
            inPane.NewLine()
            inPane.AddWrappedTextField(Lang(description))

            inPane.AddKeyHelpField( {
                Lang("<Enter>") : Lang("Reconfigure"), 
                Lang("<PgUp/Dn>") : Lang("Scroll")
            })


        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(RemoteDBDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'REMOTE_DB', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_REMOTE',
                'menupriority' : 300,
                'menutext' : Lang('Setup Remote Database') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureRemoteDB().Register()
