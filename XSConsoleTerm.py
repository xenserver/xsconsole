#!/usr/bin/env python

import sys, os, time, string
import curses

from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleData import *
from XSConsoleDialogues import *
from XSConsoleMenus import *
from XSConsoleLang import *

class App:
    def __init__(self):
        self.cursesScreen = None
    
    def Enter(self):
        # Data.Inst().Dump() # Testing

        try:
            try:
                sys.stdout.write("\033%@") # Select default character set, ISO 8859-1 (ISO 2022)
                if os.path.isfile("/bin/setfont"): os.system("/bin/setfont") # Restore the default font
                if os.path.isfile("/bin/dmesg"): os.system("/bin/dmesg -n 1") # Suppress console messages
                
                os.environ["ESCDELAY"] = "50" # Speed up processing of the escape key
                
                self.cursesScreen = CursesScreen()
                self.renderer = Renderer()
                self.layout = Layout(self.cursesScreen)
                self.layout.Create()
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
                    # print no longer works here
                    reflowed = Language.ReflowText(self.layout.ExitBanner(),  80)
                    for line in reflowed:
                        print(line)
                    sys.stdout.flush()
                commandList = self.layout.ExitCommand().split()
                # Double-check authentication
                if not Auth.Inst().IsAuthenticated():
                    raise Exception("Failed to execute command - not authenticated")
                os.execv(commandList[0],  commandList)
                # Does not return
                
        except Exception, e:
            sys.stderr.write(str(e)+"\n")
            doQuit = True

    def MainLoop(self):
        
        doQuit= False
        startSeconds = time.time()
        lastDataUpdateSeconds = startSeconds
        
        self.layout.DoUpdate()
        while not doQuit:
            
            try:
                gotKey = self.layout.Window(Layout.WIN_MAIN).GetKey()
            except Exception, e:
                gotKey = None

            if gotKey == "\011": gotKey = "KEY_TAB"
            if gotKey == "\012": gotKey = "KEY_ENTER"
            if gotKey == "\033": gotKey = "KEY_ESCAPE"
            if gotKey == "\177": gotKey = "KEY_BACKSPACE"
            
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
    
            if gotKey is not None and self.layout.TopDialogue().HandleKey(gotKey):
                needsRefresh = True
                
            if self.layout.ExitCommand() is not None:
                doQuit = True
            
            if Auth.Inst().IsAuthenticated():
                bannerStr = Lang('User')+': '+Auth.Inst().LoggedInUsername()
            else:
                data = Data.Inst()
                bannerStr = data.host.software_version.product_brand('') + ' ' + data.host.software_version.product_version('')
                
            # Testing
            #if gotKey is not None:
            #    bannerStr = gotKey
            
            timeStr = time.strftime("%H:%M:%S", time.localtime())
            statusLine = "%-70s%10.10s" % (bannerStr ,timeStr)
            self.renderer.RenderStatus(self.layout.Window(Layout.WIN_TOPLINE), statusLine)

            if needsRefresh:
                self.layout.Refresh()
            
            self.layout.DoUpdate()

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
    
    def __init__(self, inParent = None):
        self.parent = inParent
        self.windows = []
        self.exitCommand = None # Not layout, but keep with layout for convinience
        self.exitBanner = None # Not layout, but keep with layout for convinience

    def ExitBanner(self):
        return self.exitBanner;
        
    def ExitBannerSet(self,  inBanner):
        self.exitBanner = inBanner
        
    def ExitCommand(self):
        return self.exitCommand;
        
    def ExitCommandSet(self,  inCommand):
        self.exitCommand = inCommand

    def Window(self, inNum):
        return self.windows[inNum]
    
    def TopDialogue(self):
        return self.dialogues[-1]
    
    def PushDialogue(self, inDialogue):
        self.dialogues.append(inDialogue)
        
    def PopDialogue(self):
        self.TopDialogue().Destroy()
        self.dialogues.pop()
        self.TopDialogue().UpdateFields()
        self.Refresh()
    
    def UpdateRootFields(self):
        if len(self.dialogues) > 0:
            self.dialogues[0].UpdateFields()
    
    def Create(self):
        self.windows.append(CursesWindow(0,1,80,23, self.parent)) # MainWindow
        self.windows.append(CursesWindow(0,0,80,1, self.parent)) # Top line window
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
    
