# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleData import *
from XSConsoleDataUtils import *
from XSConsoleDialoguePane import *
from XSConsoleFields import *
from XSConsoleLayout import *
from XSConsoleMenus import *
from XSConsoleLang import *
from XSConsoleUtils import *

class Dialogue:
    def __init__(self, inLayout = None, inParent = None):
        self.layout = FirstValue(inLayout, Layout.Inst())
        self.parent = FirstValue(inParent, self.layout.Parent())
        
        self.panes = {}

    def Pane(self, inName = None):
        return self.panes[FirstValue(inName, 0)]

    def NewPane(self,inPane, inName = None):
        self.panes[FirstValue(inName, 0)] = inPane
        return inPane

    def Title(self):
        return self.title
        
    def Destroy(self):
        for pane in self.panes.values():
            pane.Delete()
            
    def Render(self):
        for pane in self.panes.values():
            pane.Render()
            
    def UpdateFields(self):
        pass        
            
    def NeedsCursor(self):
        retVal = False
        for pane in self.panes.values():
            if pane.NeedsCursor():
                retVal = True
        return retVal
        
    def CursorOff(self):
        for pane in self.panes.values():
            pane.CursorOff()
        
    def Reset(self):
        # Reset to known state, e.g. first menu item selected
        pass

class InfoDialogue(Dialogue):
    def __init__(self, inText,  inInfo = None):
        Dialogue.__init__(self)
        self.text = inText
        self.info = inInfo
        
        pane = self.NewPane(DialoguePane(self.parent))
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedCentredBoldTextField(self.text)

        if self.info is not None:
            pane.NewLine()
            pane.AddWrappedTextField(self.info)

        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") } )
        
    def HandleKey(self, inKey):
        handled = True
        if inKey == 'KEY_ESCAPE' or inKey == 'KEY_ENTER':
            Layout.Inst().PopDialogue()
        else:
            handled = False
        return True

class BannerDialogue(Dialogue):
    def __init__(self, inText):
        Dialogue.__init__(self)
        self.text = inText
        pane = self.NewPane(DialoguePane(self.parent))
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedCentredBoldTextField(self.text)

class QuestionDialogue(Dialogue):
    def __init__(self, inText, inHandler):
        Dialogue.__init__(self,)
        self.text = inText
        self.handler = inHandler
        pane = self.NewPane(DialoguePane(self.parent))
        pane.AddBox()
        self.UpdateFields()

    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        pane.ResetPosition()
        
        pane.AddWrappedCentredBoldTextField(self.text)

        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Yes"),  Lang("<Esc>") : Lang("No")  } )
    
    def HandleKey(self, inKey):
        handled = True
        if inKey == 'y' or inKey == 'Y' or inKey == 'KEY_F(8)':
            Layout.Inst().PopDialogue()
            self.handler('y')
        elif inKey == 'n' or inKey == 'N' or inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            self.handler('n')
        else:
            handled = False
            
        return handled

class LoginDialogue(Dialogue):
    def __init__(self, inLayout, inParent,  inText = None,  inSuccessFunc = None):
        Dialogue.__init__(self, inLayout, inParent)
        self.text = inText
        self.successFunc = inSuccessFunc
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet("Login")
        pane.AddBox()
        self.UpdateFields()
        pane.InputIndexSet(0)
        
    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        if self.text is not None:
            pane.AddTitleField(self.text)
        pane.AddInputField(Lang("Username", 14), "root", 'username')
        pane.AddPasswordField(Lang("Password", 14), Auth.Inst().DefaultPassword(), 'password')
        pane.AddKeyHelpField( {
            Lang("<Esc>") : Lang("Cancel"),
            Lang("<Enter>") : Lang("Next/OK"),
            Lang("<Tab>") : Lang("Next")
        })
        
    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                inputValues = pane.GetFieldValues()
                Layout.Inst().PopDialogue()
                Layout.Inst().DoUpdate() # Redraw now as login can take a while
                try:
                    Auth.Inst().ProcessLogin(inputValues['username'], inputValues['password'])

                    if self.successFunc is not None:
                        self.successFunc()
                    else:
                        Layout.Inst().PushDialogue(InfoDialogue( Lang('Login Successful')))
                
                except Exception, e:
                    Layout.Inst().PushDialogue(InfoDialogue( Lang('Login Failed: ')+Lang(e)))

                Data.Inst().Update()
                
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB':
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled
        
class FileDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        self.vdiMount = None
        self.ChangeState('INITIAL')
    
    def Custom(self, inKey):
        return self.custom.get(inKey, None)
    
    def BuildPaneBase(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(self.Custom('title'))
        pane.AddBox()
    
    def BuildPaneINITIAL(self):
        if self.Custom('mode') == 'rw':
            self.deviceList = FileUtils.DeviceList(True) # Writable devices only
        else:
            self.deviceList = FileUtils.DeviceList(False) # Writable and read-only devices
        
        choiceDefs = []
        for device in self.deviceList:
            choiceDefs.append(ChoiceDef(device.name, lambda: self.HandleDeviceChoice(self.deviceMenu.ChoiceIndex()) ) )

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef('<No devices available>', lambda: None)) # Avoid empty menu

        self.deviceMenu = Menu(self, None, Lang("Select Device"), choiceDefs)

        self.BuildPaneBase()
        self.UpdateFields()
    
    def BuildPaneUSBNOTFORMATTED(self):
        self.BuildPaneBase()
        self.UpdateFields()
        
    def BuildPaneUSBNOTMOUNTABLE(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def BuildPaneFILES(self):
        self.BuildPaneBase()
        
        choiceDefs = []
        
        offset = 0
        if self.Custom('mode') == 'rw':
            choiceDefs.append(ChoiceDef(Lang('Enter New Filename'), lambda: self.HandleFileChoice(None)))
            offset=1
            
        for filename in self.fileList:
            displayName = "%-60.60s%10.10s" % (filename, self.vdiMount.SizeString(filename))
            choiceDefs.append(ChoiceDef(displayName, lambda: self.HandleFileChoice(self.fileMenu.ChoiceIndex() - offset) ) )

        if self.Custom('mode') != 'rw': # Read-only
            choiceDefs.append(ChoiceDef(Lang('Enter Custom Filename'), lambda: self.HandleFileChoice(None)))
        
        self.fileMenu = Menu(self, None, Lang("Select File"), choiceDefs)
        self.UpdateFields()
        
    def BuildPaneCONFIRM(self):
        self.BuildPaneBase()
        self.UpdateFields()

    def BuildPaneCUSTOM(self):
        self.BuildPaneBase()
        self.UpdateFields()
    
    def ChangeState(self, inState):
        self.state = inState
        getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(self.Custom('deviceprompt'))
        pane.AddMenuField(self.deviceMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel"), 
            "<F5>" : Lang("Rescan") } )

    def UpdateFieldsUSBNOTFORMATTED(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("This USB media is not formatted.  Would you like to format it now?"))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Format media"), Lang("<Esc>") : Lang("Exit") } )

    def UpdateFieldsUSBNOTMOUNTABLE(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedBoldTextField(Lang("This USB media contains data but this application cannot mount it.  Would you like to format the media?  This will erase all data on the media."))
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("Format Media"), Lang("<Esc>") : Lang("Exit") } )

    def UpdateFieldsFILES(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(self.Custom('fileprompt'))
        pane.AddMenuField(self.fileMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def UpdateFieldsCUSTOM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Enter Filename"))
        pane.AddInputField(Lang("Filename",  16), FirstValue(self.Custom('filename'), ''), 'filename')
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Exit") } )
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)

    def UpdateFieldsCONFIRM(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(self.Custom('confirmprompt'))
        pane.AddWrappedBoldTextField(Lang("Device"))
        pane.AddWrappedTextField(self.deviceName)
        pane.NewLine()
        
        if self.Custom('mode') == 'rw':
            fileSize = ' ('+self.vdiMount.SizeString(self.filename, Lang('New file'))+')'
        else:
            fileSize = ' ('+self.vdiMount.SizeString(self.filename, Lang('File not found'))+')'
        
        pane.AddWrappedBoldTextField(Lang("File"))
        pane.AddWrappedTextField(self.filename+fileSize)
        
        pane.NewLine()
        
        pane.AddKeyHelpField( { Lang("<F8>") : Lang("OK"), Lang("<Esc>") : Lang("Exit") } )

    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            self.PreExitActions()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = self.deviceMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_F(5)':
            Layout.Inst().PushDialogue(BannerDialogue( Lang("Rescanning...")))
            Layout.Inst().Refresh()
            Layout.Inst().DoUpdate()
            Layout.Inst().PopDialogue()
            self.BuildPaneINITIAL() # Updates self.deviceList
            time.sleep(0.5) # Display rescanning box for a reasonable time
            Layout.Inst().Refresh()
            handled = True
            
        return handled
    
    def HandleKeyUSBNOTFORMATTED(self, inKey):
        handled = False
        if inKey == 'KEY_F(8)':
            Layout.Inst().PushDialogue(BannerDialogue( Lang("Formatting...")))
            Layout.Inst().Refresh()
            Layout.Inst().DoUpdate()
            Layout.Inst().PopDialogue()

            try:
                FileUtils.USBFormat(self.vdi)
                self.HandleDevice()
            except Exception, e:
                Layout.Inst().PushDialogue(InfoDialogue( Lang("Formatting Failed"), Lang(e)))

            handled = True

        return handled
    
    def HandleKeyUSBNOTMOUNTABLE(self, inKey):
        return self.HandleKeyUSBNOTFORMATTED(inKey)
    
    def HandleKeyFILES(self, inKey):
        return self.fileMenu.HandleKey(inKey)
        
    def HandleKeyCUSTOM(self, inKey):
        handled = True
        pane = self.Pane()
        if pane.CurrentInput() is None:
            pane.InputIndexSet(0)
        if inKey == 'KEY_ENTER':
            inputValues = pane.GetFieldValues()
            try:
                FileUtils.AssertSafeLeafname(inputValues['filename'])
                self.filename = inputValues['filename']
                self.ChangeState('CONFIRM')
            except Exception, e:
                Layout.Inst().PopDialogue()
                Layout.Inst().PushDialogue(InfoDialogue(Lang(e)))
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return handled
    
    def HandleKeyCONFIRM(self, inKey):
        handled = False
        
        if inKey == 'KEY_F(8)':
            self.DoAction()
            handled = True
            
        return handled
    
    def HandleDeviceChoice(self, inChoice):
        self.deviceName = self.deviceList[inChoice].name
        self.vdi = self.deviceList[inChoice].vdi
        self.HandleDevice()
        
    def HandleDevice(self):
        try:

            self.vdiMount = None

            Layout.Inst().PushDialogue(BannerDialogue( Lang("Mounting device...")))
            Layout.Inst().Refresh()
            Layout.Inst().DoUpdate()

            self.vdiMount = MountVDIDirectly(self.vdi, self.Custom('mode'))

            
            Layout.Inst().PopDialogue()
            Layout.Inst().PushDialogue(BannerDialogue( Lang("Scanning device...")))
            Layout.Inst().Refresh()
            Layout.Inst().DoUpdate()
            
            self.fileList = self.vdiMount.Scan(self.Custom('searchregexp'), 500) # Limit number of files to avoid colossal menu
            
            Layout.Inst().PopDialogue()
            
            self.ChangeState('FILES')
        
        except USBNotFormatted:
            Layout.Inst().PopDialogue()
            self.ChangeState('USBNOTFORMATTED')
        except USBNotMountable:
            Layout.Inst().PopDialogue()
            self.ChangeState('USBNOTMOUNTABLE')
        except Exception, e:
            try:
                self.PreExitActions()
            except Exception:
                pass # Ignore failue
            Layout.Inst().PopDialogue()
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Operation Failed"), Lang(e)))

    def HandleFileChoice(self, inChoice):
        if inChoice is None:
            self.ChangeState('CUSTOM')
        else:
            FileUtils.AssertSafeLeafname(self.fileList[inChoice])
            self.filename = self.fileList[inChoice]
            self.ChangeState('CONFIRM')
    
    def PreExitActions(self):
        if self.vdiMount is not None:
            self.vdiMount.Unmount()
            self.vdiMount = None

class InputDialogue(Dialogue):
    def __init__(self, inLayout = None, inParent = None):
        Dialogue.__init__(self, inLayout, inParent)
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(self.Custom('title'))
        pane.AddBox()
        self.UpdateFields()
        pane.InputIndexSet(0)
    
    def Custom(self, inKey):
        return self.custom.get(inKey, None)
    
    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        if self.Custom('info') is not None:
            pane.AddWrappedTextField(self.Custom('info'))
            pane.NewLine()
            
        for field in self.Custom('fields'):
            pane.AddInputField(*field)
        
        pane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("OK"),
            Lang("<Esc>") : Lang("Cancel")
        })
    
    def HandleCommit(self, inValues): # Override this
        Layout.Inst().PopDialogue()
    
    def HandleKey(self, inKey):
        handled = True
        pane = self.Pane()
        if inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_ENTER':
            if not pane.IsLastInput():
                pane.ActivateNextInput()
            else:
                try:
                    Layout.Inst().PopDialogue()
                    Layout.Inst().DoUpdate()
                    title, info = self.HandleCommit(self.Pane().GetFieldValues())
                    Layout.Inst().PushDialogue(InfoDialogue( title, info))
                except Exception, e:
                    Layout.Inst().PushDialogue(InfoDialogue( Lang('Failed: ')+Lang(e)))
        elif inKey == 'KEY_TAB':
            pane.ActivateNextInput()
        elif inKey == 'KEY_BTAB': # BTAB not available on all platforms
            pane.ActivatePreviousInput()
        elif pane.CurrentInput().HandleKey(inKey):
            pass # Leave handled as True
        else:
            handled = False
        return True
        
class SRDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        self.ChangeState('INITIAL')
    
    def Custom(self, inKey):
        return self.custom.get(inKey, None)
    
    def BuildPaneBase(self):
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(self.Custom('title'))
        pane.AddBox()
    
    def BuildPaneINITIAL(self):
        data = Data.Inst()
        
        self.choices = SRUtils.SRList(self.Custom('mode'), self.Custom('capabilities'))
        choiceDefs = []
        for choice in self.choices:
            choiceDefs.append(ChoiceDef(choice.name, lambda: self.HandleSRChoice(self.srMenu.ChoiceIndex()) ) )

        if len(choiceDefs) == 0:
            choiceDefs.append(ChoiceDef(Lang('<No suitable SRs available>'), lambda: None)) # Avoid empty menu

        self.srMenu = Menu(self, None, Lang("Select SR"), choiceDefs)

        self.BuildPaneBase()
        self.UpdateFields()

    def ChangeState(self, inState):
        self.state = inState
        getattr(self, 'BuildPane'+self.state)() # Despatch method named 'BuildPane'+self.state
    
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(self.Custom('prompt'))
        pane.AddMenuField(self.srMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
        
    def HandleKeyINITIAL(self, inKey):
        handled = self.srMenu.HandleKey(inKey)
        
        if not handled and inKey == 'KEY_F(5)':
            Data.Inst().Update()
            self.BuildPaneINITIAL() # Updates menu
            Layout.Inst().Refresh()
            handled = True
        
        return handled

    def HandleSRChoice(self, inChoice):
        self.DoAction(self.choices[inChoice].sr)
        

class DialogueUtils:
    # Helper for activate
    @classmethod
    def AuthenticatedOnly(cls, inFunc):
        if not Auth.Inst().IsAuthenticated():
            Layout.Inst().PushDialogue(LoginDialogue(Layout.Inst(), Layout.Inst().Parent(),
                Lang('Please log in to perform this function'), inFunc))
        else:
            inFunc()
            
    @classmethod
    def AuthenticatedOrPasswordUnsetOnly(cls, inFunc):
        if Auth.Inst().IsPasswordSet():
            cls.AuthenticatedOnly(inFunc)
        else:
            inFunc()
