# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import curses, sys, commands

from XSConsoleBases import *
from XSConsoleConfig import *
from XSConsoleLang import *
from XSConsoleState import *

class CursesPalette:
    pairIndex = 1
    colours = {}

    @classmethod
    def ColourAttr(cls, inName, inDefault = None):
        return cls.colours[inName or inDefault]

    @classmethod
    def ColourCreate(cls, inForeground, inBackground):
        thisIndex = cls.pairIndex
        curses.init_pair(thisIndex, inForeground, inBackground)
        cls.pairIndex += 1
        return curses.color_pair(thisIndex)
    
    @classmethod
    def DefineColours(cls):
        cls.pairIndex = 1
        config = Config.Inst()

        if curses.can_change_color():
            # Define colours on colour-changing terminals - these are terminals with the ccc
            # flag in their capabilities in terminfo
            prefix = ''
                
            # Some terminals advertise that they can change colours but don't,
            # so the following keeps things at least legible in that case
            fgBright = curses.COLOR_WHITE
            fgNormal = curses.COLOR_YELLOW
            fgDark = curses.COLOR_GREEN
            bgBright = curses.COLOR_MAGENTA
            bgNormal = curses.COLOR_BLUE
            bgDark = curses.COLOR_BLACK
            
            curses.init_color(fgBright, *config.Colour(prefix+'fg_bright'))
            curses.init_color(fgNormal, *config.Colour(prefix+'fg_normal'))
            curses.init_color(fgDark, *config.Colour(prefix+'fg_dark'))
            curses.init_color(bgBright, *config.Colour(prefix+'bg_bright'))
            curses.init_color(bgNormal, *config.Colour(prefix+'bg_normal'))
            curses.init_color(bgDark, *config.Colour(prefix+'bg_dark'))
            
        else:
            # Set sensible defaults for non-colour-changing terminals
            fgBright = curses.COLOR_WHITE
            fgNormal = curses.COLOR_WHITE
            fgDark = curses.COLOR_WHITE
            bgDark = curses.COLOR_BLACK # Ensure bgDark != bgBright for MODAL_HIGHLIGHT colour
            
            bgNormal = curses.COLOR_RED
            bgBright = curses.COLOR_RED

        cls.colours['MAIN_BASE'] = cls.ColourCreate(fgNormal, bgNormal)
        cls.colours['MENU_BASE'] = cls.ColourCreate(fgNormal, bgNormal)
        cls.colours['MENU_BRIGHT'] = cls.ColourCreate(fgBright, bgNormal)
        cls.colours['MENU_HIGHLIGHT'] = cls.ColourCreate(bgDark, fgBright)
        cls.colours['MODAL_BASE'] = cls.ColourCreate(fgNormal, bgBright)
        cls.colours['MODAL_BRIGHT'] = cls.ColourCreate(fgBright, bgBright)
        cls.colours['MODAL_HIGHLIGHT'] = cls.ColourCreate(bgDark, bgBright) # Text entry
        cls.colours['MODAL_MENU_HIGHLIGHT'] = cls.ColourCreate(bgDark, fgBright)
        cls.colours['MODAL_FLASH'] = cls.ColourCreate(fgBright, bgBright) | curses.A_BLINK
        cls.colours['HELP_BASE'] = cls.ColourCreate(fgNormal, bgDark)
        cls.colours['HELP_BRIGHT'] = cls.ColourCreate(fgBright, bgDark)
        cls.colours['TOPLINE_BASE'] = cls.ColourCreate(fgDark, bgDark)
        
class CursesPane:
    debugBackground = 0
    
    def __init__(self, inXPos, inYPos, inXSize, inYSize, inXOffset, inYOffset):
        self.xPos = inXPos
        self.yPos = inYPos
        self.xSize = inXSize
        self.ySize = inYSize
        self.xOffset = inXOffset
        self.yOffset = inYOffset
        self.yClipMax = self.ySize

    def HasBox(self):
        return self.hasBox

    def Win(self):
        return self.win

    def XSize(self):
        return self.xSize
        
    def YSize(self):
        return self.ySize
        
    def XOffset(self):
        return self.xOffset
        
    def YOffset(self):
        return self.yOffset
        
    def OffsetSet(self,  inXOffset, inYOffset):
        self.xOffset = inXOffset
        self.yOffset = inYOffset

    def YClipMaxSet(self, inYClipMax):
        if inYClipMax > self.ySize:
            raise Exception("Bad YClipMax "+str(inYClipMax))
        self.yClipMax = inYClipMax

    def TitleSet(self, inTitle):
        self.title = inTitle
        
    def ClippedAddStr(self,  inString, inX,  inY,  inColour): # Internal use
        xPos = inX
        clippedStr = inString
        
        # Is text on the screen at all?
        if inY >=0 and inY < self.yClipMax and xPos < self.xSize:

            # Clip against left hand side
            if xPos < 0:
                clippedStr = clippedStr[-xPos:]
                xPos = 0

            # Clip against right hand side
            clippedStr = clippedStr[:self.xSize - xPos]
            
            if len(clippedStr) > 0:
                try:
                    self.win.addstr(inY, xPos, inString, CursesPalette.ColourAttr(FirstValue(inColour, self.defaultColour)))
                except Exception,  e:
                    if xPos + len(inString) == self.xSize and inY + 1 == self.ySize:
                        # Curses incorrectely raises an exception when writing the bottom right
                        # character in a window, but still completes the write, so ignore it
                        pass
                    else:
                        raise Exception("addstr failed with "+Lang(e)+" for '"+inString+"' at "+str(xPos)+', '+str(inY))
        
    def AddBox(self):
        self.hasBox = True
 
    def AddText(self, inString, inX, inY, inColour = None):
        self.ClippedAddStr(inString, inX, inY, inColour)
    
    def AddWrappedText(self, inString, inX, inY, inColour = None):
        yPos = inY
        width = self.xSize - inX - 1
        if width < 1 : raise "Text outside of window"
        
        text = inString+" "
        while len(text) > 0 and yPos < self.ySize:
            spacePos = text.rfind(' ', 0, width)
            if spacePos == -1:
                lineLength = width
            else:
                lineLength = spacePos
            
            thisLine = text[0:lineLength]
            text = text[lineLength+1:]
            self.ClippedAddStr(thisLine, inX, inY, inColour)
            yPos += 1
    
    def AddHCentredText(self, inString, inY, inColour = None):
        xStart = self.xSize / 2 - len(inString) / 2
        self.ClippedAddStr(inString, xStart, inY, inColour)
    
    def Decorate(self):
        if self.hasBox:
            self.Box()
        if self.title != "":
            self.AddHCentredText(" "+self.title+" ", 0)
    
    def Erase(self):
        self.win.erase()
        self.Decorate()

    def Clear(self):
        self.win.clear()
        self.Decorate()
        
    def Box(self):
        self.win.box(0, 0)
        
    def Refresh(self):
        self.win.noutrefresh()
    
    def Redraw(self):
        self.win.redrawwin()
        self.Decorate()
        self.win.noutrefresh()
    
    def GetCh(self):
        return self.win.getch()
    
    def GetKey(self):
        return self.win.getkey()
    
    def DefaultColourSet(self, inName):
        self.defaultColour = inName
        self.win.bkgdset(ord(' '), CursesPalette.ColourAttr(self.defaultColour))

    def CursorOn(self, inXPos = None, inYPos = None):
        curses.curs_set(2)
        if inXPos is not None and inYPos is not None:
            clippedXPos = max(min(inXPos,  self.xSize-1),  0)
            clippedYPos = max(min(inYPos,  self.ySize-1),  0)
            self.win.move(clippedYPos, clippedXPos)
            self.win.cursyncup()
            
    def CursorOff(self):
        curses.curs_set(0)
        self.win.cursyncup()

class CursesWindow(CursesPane):
    def __init__(self, inXPos, inYPos, inXSize, inYSize, inParent):
        CursesPane.__init__(self, inXPos, inYPos, inXSize, inYSize, inParent.xOffset, inParent.yOffset)

        if inParent:
            self.win = inParent.Win().subwin(self.ySize, self.xSize, self.yPos+inParent.YOffset(), self.xPos+inParent.XOffset())
        else:
            raise Exception("Orphan windows not supported - supply parent")
            self.win = curses.newwin(self.ySize, self.xSize, self.yPos, self.xPos) # Old behaviour
        self.win.keypad(1)
        self.title = ""
        self.hasBox = False
        self.win.timeout(1000) # Return from getkey after x milliseconds if no key pressed
        
    def Delete(self):
        # We rely on the garbage collector to call delwin(self.win), in the binding for PyCursesWindow_Dealloc
        del self.win

class CursesScreen(CursesPane):
    def __init__(self):
        
        self.win = curses.initscr()

        (ySize, xSize) = self.win.getmaxyx()
        CursesPane.__init__(self, 0, 0, xSize, ySize, 0, 0)
        curses.noecho()
        curses.cbreak()
        if curses.has_colors():
            curses.start_color()
            CursesPalette.DefineColours()
        curses.curs_set(0) # Make cursor invisible
        self.win.keypad(1)
        self.win.timeout(1000) # Return from getkey after x milliseconds if no key pressed
                
    def Exit(self):
        curses.nocbreak()
        self.win.keypad(0)
        curses.echo()
        curses.endwin()
            
    def UseColor():
        return curses.has_color()
