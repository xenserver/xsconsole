
import curses, sys, commands

from XSConsoleBases import *

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
        # Set sensible defaults for non-colour terminals
        white = curses.COLOR_WHITE
        black = curses.COLOR_BLACK
        magenta = curses.COLOR_MAGENTA
        darkmagenta = curses.COLOR_MAGENTA
        lightgrey = curses.COLOR_WHITE
        darkgrey = curses.COLOR_BLACK
        
        if curses.can_change_color():
            curses.init_color(curses.COLOR_BLUE, 666, 666, 666) # Redefine COLOR_BLUE to use as light grey
            lightgrey = curses.COLOR_BLUE
            curses.init_color(curses.COLOR_GREEN, 333, 333, 333) # Redefine COLOR_GREEN to use as dark grey
            darkgrey = curses.COLOR_GREEN
            curses.init_color(curses.COLOR_RED, 500, 0, 500) # Redefine COLOR_RED to use as dark magenta
            darkmagenta = curses.COLOR_RED
            curses.init_color(curses.COLOR_MAGENTA, 666, 0, 666) # Tweak the colour of magenta
            curses.init_color(curses.COLOR_WHITE, 999, 999, 999) # Tweak the colour of white
            
        cls.colours['MAIN_BASE'] = cls.ColourCreate(lightgrey, darkmagenta)
        cls.colours['MENU_BASE'] = cls.ColourCreate(lightgrey, darkmagenta)
        cls.colours['MENU_BRIGHT'] = cls.ColourCreate(white, darkmagenta)
        cls.colours['MENU_HIGHLIGHT'] = cls.ColourCreate(black, white)
        cls.colours['MODAL_BASE'] = cls.ColourCreate(lightgrey, magenta)
        cls.colours['MODAL_BRIGHT'] = cls.ColourCreate(white, magenta)
        cls.colours['MODAL_HIGHLIGHT'] = cls.ColourCreate(black, magenta) | curses.A_DIM
        cls.colours['HELP_BASE'] = cls.ColourCreate(lightgrey, black)
        cls.colours['HELP_BRIGHT'] = cls.ColourCreate(white, black)
        cls.colours['STATUS_BASE'] = cls.ColourCreate(lightgrey, black)
        cls.colours['TEST'] = cls.ColourCreate(curses.COLOR_RED, white)
        
class CursesPane:
    debugBackground = 0
    
    def __init__(self, inXPos, inYPos, inXSize, inYSize):
        self.xPos = inXPos
        self.yPos = inYPos
        self.xSize = inXSize
        self.ySize = inYSize

    def HasBox(self):
        return self.hasBox

    def Win(self):
        return self.win

    def TitleSet(self, inTitle):
        self.title = inTitle
        
    def ClippedAddStr(self,  inString, inX,  inY,  inColour): # Internal use
        xPos = inX
        clippedStr = inString
        
        # Is text on the screen at all?
        if inY >=0 and inY < self.ySize and xPos < self.xSize:

            # Clip against left hand side
            if xPos < 0:
                clippedStr = clippedStr[-xPos:]
                xPos = 0

            # Clip against right hand side
            clippedStr = clippedStr[:self.xSize - xPos]
            
            if len(clippedStr) > 0:
                self.win.addstr(inY, xPos, inString, CursesPalette.ColourAttr(FirstValue(inColour, self.defaultColour)))
        
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
    def __init__(self, inXPos, inYPos, inXSize, inYSize, inParent = None):
        CursesPane.__init__(self, inXPos, inYPos, inXSize, inYSize)

        if inParent:
            self.win = inParent.Win().subwin(self.ySize, self.xSize, self.yPos, self.xPos)
        else:
            self.win = curses.newwin(self.ySize, self.xSize, self.yPos, self.xPos)
        self.win.keypad(1)
        self.title = ""
        self.hasBox = False
    
    def Delete(self):
        # We rely on the garbage collector to call delwin(self.win), in the binding for PyCursesWindow_Dealloc
        del self.win

class CursesScreen(CursesPane):
    def __init__(self):
        
        self.win = curses.initscr()

        (ySize, xSize) = self.win.getmaxyx();
        CursesPane.__init__(self, 0, 0, xSize, ySize)
        curses.noecho()
        curses.cbreak()
        if curses.has_colors():
            curses.start_color()
            CursesPalette.DefineColours()
        curses.curs_set(0) # Make cursor invisible
        self.win.keypad(1)
        
    def Exit(self):
        curses.nocbreak()
        self.win.keypad(0)
        curses.echo()
        curses.endwin()
            
    def UseColor():
        return curses.has_color()
