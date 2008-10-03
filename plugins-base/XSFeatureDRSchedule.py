# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class DRScheduleDialogue(Dialogue):

    def cronPath(self, freq):
        return "/etc/cron." + freq + "/backup-metadata"

    def findCurrent(self):
        found = 'never'
        for t in ['daily', 'weekly', 'monthly']:
            if os.path.exists(self.cronPath(t)):
                found=t
        return found

    def __init__(self):
        Dialogue.__init__(self)
   
        self.timeMenu = Menu(self, None, "", [
           ChoiceDef("Daily", lambda: self.HandleMethodChoice('daily')),
           ChoiceDef("Weekly", lambda: self.HandleMethodChoice('weekly')),
           ChoiceDef("Monthly", lambda: self.HandleMethodChoice('monthly')),
           ChoiceDef("Never", lambda: self.HandleMethodChoice('never')),
        ])

        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang('Schedule Regular Metadata Backup'))
        pane.AddBox()
        currentSetting = self.findCurrent()
        if currentSetting == 'never':
            title=Lang("Scheduled Metadata Backups are currently disabled.  Please select the desired frequency:")
        else:
            title=Lang("Scheduled Metadata Backups are currently set to occur ") + currentSetting + Lang(".  Please select the desired frequency:")
        pane.AddTitleField(title)
        pane.AddMenuField(self.timeMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def HandleMethodChoice(self, inChoice):
        currentSetting = self.findCurrent()
        Layout.Inst().PopDialogue()
        # remove current setting
        if currentSetting != 'never':
            try:
                os.unlink(self.cronPath(currentSetting))
            except:
                pass
        if inChoice != 'never':
            try:
                os.symlink("/opt/xensource/libexec/backup-metadata-cron", self.cronPath(inChoice))
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Metadata Backup Schedule successfully changed to occur ") + inChoice + "."))
            except:
                XSLogFailure('Failed to create metadata schedule link')
                Layout.Inst().PushDialogue(InfoDialogue(Lang("Failed to create metadata schedule link")))
        else:
            Layout.Inst().PushDialogue(InfoDialogue(Lang("Metadata Backup Schedule successfully disabled")))
        

    def HandleKey(self, inKey):
        handled = self.timeMenu.HandleKey(inKey)

        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled

class XSFeatureDRSchedule:
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Schedule Virtual Machine Metadata"))

        inPane.AddWrappedTextField(Lang(
            "Press <Enter> to select how to schedule regular Virtual Machine metadata backups."))  
        inPane.AddKeyHelpField( { Lang("<Enter>") : Lang("Change Schedule") } )  
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(DRScheduleDialogue()))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'DRSCHEDULE', # Key of this plugin for replacement, etc.
            {
                'menuname' : 'MENU_BUR',
                'menupriority' : 70,
                'menutext' : Lang('Schedule Virtual Machine Metadata') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureDRSchedule().Register()
