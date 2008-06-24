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
from XSConsoleHotData import *
from XSConsoleImporter import *
from XSConsoleMenus import *
from XSConsoleLang import *
from XSConsoleLayout import *
from XSConsoleRootDialogue import *
from XSConsoleState import *

class App:
    def __init__(self):
        self.cursesScreen = None
    
    def Build(self, inDirs = None):
        # Search for the app plugins and include them
        Importer.Reset()
        for dir in inDirs:
            Importer.ImportRelativeDir(dir)
    
    def Enter(self):
        doQuit = False
        
        if '--dump' in sys.argv:
            # Testing - dump data and exit
            Data.Inst().Dump()
            Importer.Dump()
            for key, value in HotData.Inst().guest_vm().iteritems():
                localhost = HotAccessor().local_host()
                vm = HotData.Inst().vm[key]
                vm.metrics()
                try: vm.guest_metrics()
                except: pass # Not all VMs  have guest metrics
                HotAccessor().pool()
            HotData.Inst().Dump()
            doQuit = True
        
        # Purge leftover VBDs at startup
        # Removed following API change
        # Data.Inst().PurgeVBDs()
        
        # Reinstate keymap
        if State.Inst().Keymap() is not None:
            Data.Inst().KeymapSet(State.Inst().Keymap())
        
        while not doQuit:
            try:
                try:
                    sys.stdout.write("\033%@") # Select default character set, ISO 8859-1 (ISO 2022)
                    if os.path.isfile("/bin/setfont"): os.system("/bin/setfont") # Restore the default font
                    
                    os.environ["ESCDELAY"] = "50" # Speed up processing of the escape key
                    
                    self.cursesScreen = CursesScreen()
                    self.renderer = Renderer()
                    self.layout = Layout.NewInst()
                    self.layout.ParentSet(self.cursesScreen)
                    self.layout.WriteParentOffset(self.cursesScreen)
                    self.layout.Create()
                    self.layout.ParentSet(self.layout.Window(self.layout.WIN_MAIN))
                    self.layout.CreateRootDialogue(RootDialogue(self.layout, self.layout.Window(self.layout.WIN_MAIN)))
                    self.layout.TransientBannerHandlerSet(App.TransientBannerHandler)
                    
                    if State.Inst().WeStoppedXAPI():
                        # Restart XAPI if we crashed after stopping it
                        Data.Inst().StartXAPI()
                        Data.Inst().Update()
                        
                    if not Data.Inst().IsXAPIRunning() and State.Inst().RebootMessage() is None:
                        self.layout.PushDialogue(QuestionDialogue(
                            Lang("The underlying Xen API xapi is not running.  This console will have reduced functionality.  "
                                 "Would you like to attempt to restart xapi?"), lambda x: self.HandleRestartChoice(x)))

                    # Request password change on first boot, or if it isn't set
                    if not Auth.Inst().IsPasswordSet() :
                        Importer.ActivateNamedPlugIn('CHANGE_PASSWORD', Lang("Please specify a password for user 'root' before continuing"))
                    elif State.Inst().PasswordChangeRequired():
                        Importer.ActivateNamedPlugIn('CHANGE_PASSWORD', Lang("Please change the password for user 'root' before continuing"))
                    elif State.Inst().RebootMessage() is not None:
                        Importer.ActivateNamedPlugIn('REBOOT', State.Inst().RebootMessage())
                        State.Inst().RebootMessageSet(None)
                            
                    self.layout.Clear()
                    if not '--dryrun' in sys.argv:
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

                    if len(commandList) == 0:
                        doQuit = True
                    else:
                        if self.layout.ExitCommandIsExec():
                            os.execv(commandList[0], commandList)
                            # Does not return
                        else:
                            os.system(self.layout.ExitCommand())
                            Data.Inst().Update() # Pick up changes caused by the subshell command

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
                raise
        

    def MainLoop(self):

        doQuit= False
        startSeconds = time.time()
        lastDataUpdateSeconds = startSeconds
        lastScreenUpdateSeconds = startSeconds
        lastGarbageCollectSeconds = startSeconds
        resized = False
        data = Data.Inst()
        errorCount = 0
        
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
            if gotKey == '\xc2': gotKey = "KEY_F(5)" # Handle function key mistranslation on vncterm
            if gotKey == '\xc5': gotKey = "KEY_F(8)" # Handle function key mistranslation on vncterm
            
            if gotKey == 'KEY_RESIZE':
                resized = True
            elif resized and gotKey is not None:
                if os.path.isfile("/bin/setfont"): os.system("/bin/setfont") # Restore the default font
                resized = False
            
            # Screen out non-ASCII and unusual characters
            for char in FirstValue(gotKey, ''):
                if char >="\177": # Characters 128 and greater
                    gotKey = None
                    break
    
            needsRefresh = False
            secondsNow = time.time()
            secondsRunning = secondsNow - startSeconds

            if data.host.address('') == '':
                # If the host doesn't yet have an IP, reload data occasionally to pick up DHCP updates
                if secondsNow - lastDataUpdateSeconds >= 4:
                    lastDataUpdateSeconds = secondsNow
                    data.Update()
                    self.layout.UpdateRootFields()
                    needsRefresh = True
    
            if secondsNow - lastScreenUpdateSeconds >= 4:
                lastScreenUpdateSeconds = secondsNow
                self.layout.UpdateRootFields()
                needsRefresh = True
                
            if gotKey is not None:
                try:
                    Auth.Inst().KeepAlive()
                    if self.layout.TopDialogue().HandleKey(gotKey):
                        State.Inst().SaveIfRequired()
                        needsRefresh = True
                    elif gotKey == 'KEY_ESCAPE':
                        # Set root menu choice to the first, to give a fixed start state after lots of escapes
                        self.layout.TopDialogue().Reset()
                        needsRefresh = True
                    elif gotKey == 'KEY_F(5)':
                        data.Update()
                        self.layout.UpdateRootFields()
                        needsRefresh = True
                    elif gotKey == '\014': # Ctrl-L
                        Layout.Inst().Clear() # Full redraw
                        needsRefresh = True
                        
                except Exception, e:
                    if Auth.Inst().IsTestMode():
                        raise
                    if errorCount <= 10:
                        message = Lang(e)
                        if errorCount == 10:
                            message += Lang('\n\n(No more errors will be reported)')
                        errorCount += 1
                        Layout.Inst().PushDialogue(InfoDialogue(Lang("Error"), message))

            if self.layout.ExitCommand() is not None:
                doQuit = True
            
            bannerStr = Language.Inst().Branding(data.host.software_version.product_brand('')) + ' ' + data.host.software_version.product_version('')
            
            if Auth.Inst().IsAuthenticated():
                hostStr = Auth.Inst().LoggedInUsername()+'@'+data.host.hostname('')
            else:
                hostStr = data.host.hostname('')
                
            # Testing
            # if gotKey is not None:
            #     bannerStr = gotKey
            
            timeStr = time.strftime(" %H:%M:%S ", time.localtime())
            statusLine = ("%-35s%10.10s%35.35s" % (bannerStr[:35], timeStr[:10], hostStr[:35]))
            self.renderer.RenderStatus(self.layout.Window(Layout.WIN_TOPLINE), statusLine)

            if needsRefresh:
                self.layout.Refresh()
            elif self.layout.LiveUpdateFields():
                self.layout.Refresh()
                
            self.layout.DoUpdate()
            
            if secondsNow - lastGarbageCollectSeconds >= 60:
                lastGarbageCollectSeconds = secondsNow
                Task.Inst().GarbageCollect()

    def HandleRestartChoice(self, inChoice):
        if inChoice == 'y':
            try:
                self.layout.TransientBanner(Lang("Restarting xapi...."))
                Data.Inst().StartXAPI()
            except Exception, e:
                self.layout.PushDialogue(InfoDialogue(Lang('Restart Failed'), Lang('Xapi did not restart successfully.  More information may be available in the file /var/log/messages.')))

    @classmethod
    def TransientBannerHandler(self, inMessage):
        layout = Layout.Inst()
        layout.PushDialogue(BannerDialogue(inMessage))
        layout.Refresh()
        layout.DoUpdate()
        layout.PopDialogue()

class Renderer:        
    def RenderStatus(self, inWindow, inText):
        (cursY, cursX) = curses.getsyx() # Store cursor position
        inWindow.Win().erase()
        inWindow.AddText(inText, 0, 0)
        inWindow.Refresh()
        if cursX != -1 and cursY != -1:
            curses.setsyx(cursY, cursX) # Restore cursor position
        
