
from XSConsoleBases import *
from XSConsoleLang import *

class InputField:
    def __init__(self, text, colour):
        ParamsToAttr()
        self.activated = False
        self.cursorPos = len(self.text)
        self.hideText = False
        
    def HideText(self):
        self.hideText = True
        
    def Activate(self):
        self.activated = True
        
    def Deactivate(self):
        self.activated = False
    
    def Content(self):
        return self.text
    
    def Render(self, inPane, inX, inY):
        if self.hideText:
            inPane.AddWrappedText("*" * len(self.text), inX, inY, self.colour)
        else:
            inPane.AddWrappedText(self.text, inX, inY, self.colour)
        if self.activated:
            inPane.CursorOn(inX+self.cursorPos, inY)

    def Width(self):
        return len(self.text)
    
    def Height(self):
        return 1
        
    def HandleKey(self, inKey):
        handled = True
        if inKey == 'KEY_LEFT':
            self.cursorPos = max(0, self.cursorPos - 1)
        elif inKey == 'KEY_RIGHT':
            self.cursorPos = min(len(self.text), self.cursorPos + 1)
        elif inKey == 'KEY_DC':
            self.text = self.text[:self.cursorPos] + self.text[self.cursorPos+1:]
        elif inKey == 'KEY_BACKSPACE':
            if (self.cursorPos > 0):
                self.cursorPos -= 1
                self.text = self.text[:self.cursorPos] + self.text[self.cursorPos+1:]
        elif len(inKey) == 1 and inKey[0] >= ' ':
            self.text = self.text[:self.cursorPos] + inKey[0] + self.text[self.cursorPos:]
            self.cursorPos += 1
        else:
            handled = False
        return handled

class TextField:
    def __init__(self, text, colour):
        ParamsToAttr()
        
    def Render(self, inPane, inX, inY):
        inPane.AddWrappedText(self.text, inX, inY, self.colour)

    def Width(self):
        return len(self.text)

    def Height(self):
        return 1
        
class WrappedTextField:
    def __init__(self, text, width, colour):
        ParamsToAttr()
        self.wrappedText = Language.ReflowText(self.text, width)
        
    def Render(self, inPane, inXPos, inYPos):
        yPos = inYPos
        for line in self.wrappedText:
            inPane.AddText(line, inXPos, yPos, self.colour)
            yPos += 1

    def Width(self):
        return max ( len(line) for line in self.wrappedText )

    def Height(self):
        return len(self.wrappedText)

class MenuField:
    def __init__(self, menu, colour, highlight, height):
        ParamsToAttr()
        self.scrollPoint = 0
        self.height = min(self.height, len(self.menu.ChoiceDefs()))
    
    def Width(self):
        if len(self.menu.ChoiceDefs()) == 0:
            return 0
        return max(len(choice.name) for choice in self.menu.ChoiceDefs() )

    def Height(self):
        return self.height
        
    def Render(self, inPane, inXPos, inYPos):
        # This rendering doesn't necessarily deal with scrolling menus where the choice names
        # are of different lengths.  More erase/overwrite operations may be required to do that.
        
        # Move the scroll point if the selected option would otherwise be off the screen
        choiceIndex = self.menu.ChoiceIndex()
        if self.scrollPoint > choiceIndex:
            # Move so the choiceIndex is at the top
            self.scrollPoint = choiceIndex
        elif self.scrollPoint + self.height <= choiceIndex:
            # Move so the choiceIndex is at the bottom
            self.scrollPoint = choiceIndex - self.height + 1

        choiceDefs = self.menu.ChoiceDefs()
        for i in range(min(self.height, len(choiceDefs) - self.scrollPoint)):
            choiceNum = self.scrollPoint + i
            if choiceNum == choiceIndex:
                colour = self.highlight
            else:
                colour = self.colour
                
            inPane.AddText(choiceDefs[choiceNum].name, inXPos, inYPos + i, colour)
