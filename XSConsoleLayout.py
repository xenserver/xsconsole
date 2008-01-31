# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

from XSConsoleBases import *
from XSConsoleCurses import *

class Layout:
    WIN_MAIN = 0
    WIN_TOPLINE = 1
    
    APP_XSIZE = 80
    APP_YSIZE = 24
    
    instance = None
    
    def __init__(self, inParent = None):
        self.parent = inParent
        self.windows = []
        self.exitCommand = None # Not layout, but keep with layout for convenience
        self.exitBanner = None # Not layout, but keep with layout for convenience
        self.exitCommandIsExec = True # Not layout, but keep with layout for convenience

    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = Layout()
        return cls.instance
    
    @classmethod
    def NewInst(cls):
        cls.instance = Layout()
        return cls.instance
        
    def ParentSet(self, inParent):
        self.parent = inParent

    def Parent(self):
        return self.parent

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
    
    def TransientBannerHandlerSet(self, inHandler):
        self.transientBannerHandler = inHandler
    
    def TransientBanner(self, inMessage):
        self.transientBannerHandler(inMessage)
    
    def WriteParentOffset(self, inParent):
        consoleXSize = inParent.XSize()
        consoleYSize = inParent.YSize()
        if consoleXSize < self.APP_XSIZE or consoleYSize < self.APP_YSIZE:
            raise Exception('Console size ('+str(consoleXSize)+', '+str(consoleYSize) +
                ') too small for application size ('+str(self.APP_XSIZE)+', '+str(self.APP_YSIZE) +')')
        
        # Centralise subsequent windows
        inParent.OffsetSet(
            (inParent.XSize() - self.APP_XSIZE) / 2,
            (inParent.YSize() - self.APP_YSIZE) / 2)
            
    def Create(self):
        self.windows.append(CursesWindow(0,1,self.APP_XSIZE, self.APP_YSIZE-1, self.parent)) # MainWindow
        self.windows.append(CursesWindow(0,0,self.APP_XSIZE,1, self.parent)) # Top line window
        self.windows[self.WIN_MAIN].DefaultColourSet('MAIN_BASE')
        self.windows[self.WIN_TOPLINE].DefaultColourSet('TOPLINE_BASE')
            
        self.Window(self.WIN_MAIN).AddBox()
        self.Window(self.WIN_MAIN).TitleSet("Configuration")
    
    def CreateRootDialogue(self, inRootDialogue):
        self.dialogues = [ inRootDialogue ]
        
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
    
