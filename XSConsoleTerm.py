# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import sys, os, time, string
import curses

from XSConsoleAuth import *
from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleData import *
from XSConsoleDialogues import *
from XSConsoleMenus import *
from XSConsoleLang import *
from XSConsoleRootDialogue import *
from XSConsoleState import *

class App:
    def __init__(self):
        self.cursesScreen = None
    
    def Enter(self):
        doQuit = False

        if '--dump' in sys.argv:
            # Testing - dump data and exit
            Data.Inst().Dump()
            doQuit = True
        
        # Purge leftover VBDs at startup
        Data.Inst().PurgeVBDs()
        
        while not doQuit:
            try:
                try:
                    sys.stdout.write("\033%@") # Select default character set, ISO 8859-1 (ISO 2022)
                    if os.path.isfile("/bin/setfont"): os.system("/bin/setfont") # Restore the default font
                    if os.path.isfile("/bin/dmesg"): os.system("/bin/dmesg -n 1") # Suppress console messages
                    
                    os.environ["ESCDELAY"] = "50" # Speed up processing of the escape key
                    
                    self.cursesScreen = CursesScreen()
                    self.renderer = Renderer()
                    self.layout = Layout(self.cursesScreen)
                    self.layout.WriteParentOffset(self.cursesScreen)
                    self.layout.Create()

                    if State.Inst().WeStoppedXAPI():
                        # Restart XAPI if we crashes after stopping it
                        Data.Inst().StartXAPI()
                        Data.Inst().Update()
                        
                    if not Data.Inst().IsXAPIRunning():
                        self.layout.PushDialogue(QuestionDialogue(self.layout, self.layout.Window(Layout.WIN_MAIN),
                            Lang("The underlying Xen API xapi is not running.  This console will have reduced functionality.  "
                                 "Would you like to attempt to restart xapi?"), lambda x: self.HandleRestartChoice(x)))

                    # Request password change on first boot, or if it isn't set
                    if not State.Inst().IsRecoveryMode(): # No password activity in recovery mode
                        if not Auth.Inst().IsPasswordSet() :
                            self.layout.PushDialogue(ChangePasswordDialogue(self.layout,
                                self.layout.Window(Layout.WIN_MAIN), Lang("Please specify a password for user 'root' before continuing")))
                        elif State.Inst().PasswordChangeRequired():
                            self.layout.PushDialogue(ChangePasswordDialogue(self.layout,
                                self.layout.Window(Layout.WIN_MAIN), Lang("Please change the password for user 'root' before continuing")))
                        elif State.Inst().RebootMessage() is not None:
                            self.layout.PushDialogue(QuestionDialogue(
                                self.layout,
                                self.layout.Window(Layout.WIN_MAIN),
                                State.Inst().RebootMessage(), lambda x: self.layout.TopDialogue().RebootDialogueHandler(x)
                                )
                            )
                            State.Inst().RebootMessageSet(None)
                            
                    self.layout.Clear()
                    self.MainLoop()
                    
                finally:
                    if self.cursesScreen is not None:
                        self.cursesScreen.Exit()
            
                if self.layout.ExitCommand() is None:
                    doQuit = True
                else:
                    os.system('/usr/bin/reset') # Reset terminal
                    if self.layout.ExitBanner() is not None:
                        reflowed = Language.ReflowText(self.layout.ExitBanner(),  80)
                        for line in reflowed:
                            print(line)
                        sys.stdout.flush()
                    commandList = self.layout.ExitCommand().split()
                    # Double-check authentication
                    Auth.Inst().AssertAuthenticated()

                    if self.layout.ExitCommandIsExec():
                        os.execv(commandList[0], commandList)
                        # Does not return
                    else:
                        os.system(self.layout.ExitCommand())

            except KeyboardInterrupt, e: # Catch Ctrl-C
                Data.Reset()
                sys.stderr.write("\033[H\033[J"+Lang("Resetting...")) # Clear screen and print banner
                try:
                    time.sleep(0.5) # Prevent flicker
                except Exception, e:
                    pass # Catch repeated Ctrl-C
            
            except Exception, e:
                sys.stderr.write(Lang(e)+"\n")
                doQuit = True
        

    def MainLoop(self):
        
        doQuit= False
        startSeconds = time.time()
        lastDataUpdateSeconds = startSeconds
        resized = False
        
        self.layout.DoUpdate()
        while not doQuit:
            try:
                gotKey = self.layout.Window(Layout.WIN_MAIN).GetKey()
            except Exception, e:
                gotKey = None # Catch timeout

            if gotKey == "\011": gotKey = "KEY_TAB"
            if gotKey == "\012": gotKey = "KEY_ENTER"
            if gotKey == "\033": gotKey = "KEY_ESCAPE"
            if gotKey == "\177": gotKey = "KEY_BACKSPACE"
            
            if gotKey == 'KEY_RESIZE':
                resized = True
            elif resized and gotKey is not None:
                if os.path.isfile("/bin/setfont"): os.system("/bin/setfont") # Restore the default font
                resized = False
                
            needsRefresh = False
            secondsNow = time.time()
            secondsRunning = secondsNow - startSeconds

            if Data.Inst().host.address('') == '':
                # If the host doesn't yet have an IP, reload data occasionally to pick up DHCP updates
                if secondsNow - lastDataUpdateSeconds >= 4:
                    lastDataUpdateSeconds = secondsNow
                    Data.Inst().Update()
                    self.layout.UpdateRootFields()
                    needsRefresh = True
    
            if gotKey is not None:
                Auth.Inst().KeepAlive()
                if self.layout.TopDialogue().HandleKey(gotKey):
                    State.Inst().SaveIfRequired()
                    needsRefresh = True
                elif gotKey == 'KEY_ESCAPE':
                    # Set root menu choice to the first, to give a fixed start state after lots of escapes
                    self.layout.TopDialogue().Reset()
                    needsRefresh = True
                elif gotKey == 'KEY_F(5)':
                    Data.Inst().Update()
                    self.layout.UpdateRootFields()
                    needsRefresh = True
                    
            if self.layout.ExitCommand() is not None:
                doQuit = True
            
            if State.Inst().IsRecoveryMode():
                bannerStr = Lang("Recovery Mode")
            elif Auth.Inst().IsAuthenticated():
                bannerStr = Lang('User')+': '+Auth.Inst().LoggedInUsername()
                # Testing: bannerStr += ' ('+str(int(Auth.Inst().AuthAge()))+')'
            else:
                data = Data.Inst()
                bannerStr = data.host.software_version.product_brand('') + ' ' + data.host.software_version.product_version('')
                
            # Testing
            # if gotKey is not None:
            #     bannerStr = gotKey
            
            timeStr = time.strftime("%H:%M:%S", time.localtime())
            statusLine = "%-70s%10.10s" % (bannerStr ,timeStr)
            self.renderer.RenderStatus(self.layout.Window(Layout.WIN_TOPLINE), statusLine)

            if needsRefresh:
                self.layout.Refresh()
            
            self.layout.DoUpdate()

    def HandleRestartChoice(self, inChoice):
        if inChoice == 'y':
            try:
                self.layout.TransientBanner(Lang("Restarting xapi...."))
                Data.Inst().StartXAPI()
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(self.layout, self.layout.Window(Layout.WIN_MAIN), Lang("Failed: ")+Lang(e)))

class Renderer:        
    def RenderStatus(self, inWindow, inText):
        (cursY, cursX) = curses.getsyx() # Store cursor position
        inWindow.Win().erase()
        inWindow.AddText(inText, 0, 0)
        inWindow.Refresh()
        if cursX != -1 and cursY != -1:
            curses.setsyx(cursY, cursX) # Restore cursor position
        
class Layout:
    WIN_MAIN = 0
    WIN_TOPLINE = 1
    
    APP_XSIZE = 80
    APP_YSIZE = 24
    
    def __init__(self, inParent = None):
        self.parent = inParent
        self.windows = []
        self.exitCommand = None # Not layout, but keep with layout for convenience
        self.exitBanner = None # Not layout, but keep with layout for convenience
        self.exitCommandIsExec = True # Not layout, but keep with layout for convenience

    def ExitBanner(self):
        return self.exitBanner
        
    def ExitBannerSet(self,  inBanner):
        self.exitBanner = inBanner
        
    def ExitCommand(self):
        return self.exitCommand
        
    def ExitCommandSet(self,  inCommand):
        self.exitCommand = inCommand
        self.exitCommandIsExec = True

    def SubshellCommandSet(self, inCommand):
        self.exitCommand = inCommand
        self.exitCommandIsExec = False

    def ExitCommandIsExec(self):
        return self.exitCommandIsExec

    def Window(self, inNum):
        return self.windows[inNum]
    
    def TopDialogue(self):
        return self.dialogues[-1]
    
    def PushDialogue(self, inDialogue):
        self.dialogues.append(inDialogue)
        
    def PopDialogue(self):
        if len(self.dialogues) < 1:
            raise Exception("Stack underflow in PopDialogue")
        self.TopDialogue().Destroy()
        self.dialogues.pop()
        self.TopDialogue().UpdateFields()
        self.Refresh()
    
    def UpdateRootFields(self):
        if len(self.dialogues) > 0:
            self.dialogues[0].UpdateFields()
    
    def TransientBanner(self, inMessage):
        self.PushDialogue(BannerDialogue(self, self.parent, inMessage))
        self.Refresh()
        self.DoUpdate()
        self.PopDialogue()
    
    def WriteParentOffset(self, inParent):
        consoleXSize = inParent.XSize()
        consoleYSize = inParent.YSize()
        if consoleXSize < self.APP_XSIZE or consoleYSize < self.APP_YSIZE:
            raise Exception('Console size ('+str(consoleXSize)+', '+str(consoleYSize) +
                ') too small for application size ('+str(self.APP_XSIZE)+', '+str(self.APP_YSIZE) +')')
        
        # Centralise subsequent windows
        self.parent.OffsetSet(
            (inParent.XSize() - self.APP_XSIZE) / 2,
            (inParent.YSize() - self.APP_YSIZE) / 2)
            
    def Create(self):
        self.windows.append(CursesWindow(0,1,self.APP_XSIZE, self.APP_YSIZE-1, self.parent)) # MainWindow
        self.windows.append(CursesWindow(0,0,self.APP_XSIZE,1, self.parent)) # Top line window
        self.windows[self.WIN_MAIN].DefaultColourSet('MAIN_BASE')
        self.windows[self.WIN_TOPLINE].DefaultColourSet('TOPLINE_BASE')
            
        self.Window(self.WIN_MAIN).AddBox()
        self.Window(self.WIN_MAIN).TitleSet("Configuration")
        
        self.dialogues = [ RootDialogue(self, self.Window(self.WIN_MAIN)) ]
        
    def Refresh(self):
        self.Window(self.WIN_MAIN).Erase() # Unknown why main won't redraw without this
        for window in self.windows:
            window.Refresh()

        for dialogue in self.dialogues:
            dialogue.Render()
            
        if not self.TopDialogue().NeedsCursor():
            self.TopDialogue().CursorOff()

    def Redraw(self):
        for window in self.windows:
            window.Win().redrawwin()
            window.Win().refresh()
    
    def Clear(self):
        for window in self.windows:
            window.Clear()
        self.Refresh()
    
    def DoUpdate(self):
        curses.doupdate()
    
