#!/usr/bin/env python

import sys, os
import curses

from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleData import *
from XSConsoleDialogues import *
from XSConsoleMenus import *

class App:
    def __init__(self):
        self.cursesScreen = None
    
    def Enter(self):
        Data.Inst().Dump() # Testing
        
        try:
            sys.stdout.write("\033%@") # Select default character set, ISO 8859-1 (ISO 2022)
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
        
    def MainLoop(self):
        
        doQuit= False
                
        while not doQuit:
            self.layout.DoUpdate()
            
            gotKey = self.layout.Window(Layout.WIN_MAIN).GetKey()

            if gotKey == "\011": gotKey = "KEY_TAB"
            if gotKey == "\012": gotKey = "KEY_ENTER"
            if gotKey == "\033": gotKey = "KEY_ESCAPE"
            if gotKey == "\177": gotKey = "KEY_BACKSPACE"
            
            # self.renderer.RenderStatus(self.layout.Window(Layout.WIN_STATUS), "Status: Got "+gotKey)

            if self.layout.TopDialogue().HandleKey(gotKey):
                self.layout.Refresh()
            else:
                # Key not handled by dialogue, so handle the exit case
                if gotKey == "KEY_ESCAPE": doQuit = True # Escape

class Renderer:        
    def RenderStatus(self, inWindow, inText):
        inWindow.Win().erase()
        inWindow.AddText(inText, 0, 0)
        inWindow.Refresh()
        
class Layout:
    WIN_MAIN = 0
    WIN_STATUS = 1
    
    def __init__(self, inParent = None):
        self.parent = inParent
        self.windows = []

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
    
    def Create(self):
        self.windows.append(CursesWindow(0,1,80,22, self.parent)) # MainWindow
        self.windows.append(CursesWindow(0,23,80,1, self.parent)) # Status window
        self.windows[self.WIN_MAIN].DefaultColourSet('MAIN_BASE')
        self.windows[self.WIN_STATUS].DefaultColourSet('STATUS_BASE')
            
        self.Window(self.WIN_MAIN).AddBox()
        self.Window(self.WIN_MAIN).TitleSet("Configuration")

        self.dialogues = [ RootDialogue(self, self.Window(self.WIN_MAIN)) ]
        
    def Refresh(self):
        self.Window(self.WIN_MAIN).Erase() # Unknown why main won't redraw without this
        for window in self.windows:
            window.Refresh()
    
        for dialogue in self.dialogues:
            dialogue.Render()
            
    
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
        
