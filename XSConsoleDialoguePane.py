
from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleFields import *
from XSConsoleLang import *

class DialoguePane:
    LEFT_XSTART = 1
    TITLE_XSTART = LEFT_XSTART
    TITLE_YSTART = 1
    
    def __init__(self, inXPos, inYPos, inXSize, inYSize, inParent = None):
        self.window = CursesWindow(inXPos, inYPos, inXSize, inYSize, inParent)
        self.xSize = inXSize
        self.ySize = inYSize
        self.xOffset = 0
        self.yOffset = 0
        self.ResetFields()
        self.ResetPosition()
    
    def ResetFields(self):
        self.fields = {}
        self.inputFields = []
        self.inputIndex = None

    def Win(self):
        return self.window

    def AddBox(self):
        if not self.window.HasBox():
            self.window.AddBox()
            self.xSize -= 2
            self.ySize -= 2
            self.xOffset += 1
            self.yOffset += 1
            self.ResetPosition()

    def ActivateNextInput(self): 
        self.InputIndexSet((self.inputIndex + 1) % len(self.inputFields))
            
    def ActivatePreviousInput(self): 
        self.InputIndexSet((self.inputIndex + len(self.inputFields) - 1) % len(self.inputFields))
            
    def IsLastInput(self):
        return self.inputIndex + 1 == len(self.inputFields)

    def CurrentInput(self):
        if self.inputIndex is not None:
            fieldName = self.inputFields[self.inputIndex]
            retVal = self.fields[fieldName].fieldObj
        else:
            retVal = None
        return retVal

    def InputIndexSet(self, inIndex):
        if self.inputIndex is not None:
            self.CurrentInput().Deactivate()
        
        self.inputIndex = inIndex
        
        if self.inputIndex is not None:
            self.CurrentInput().Activate()

    def NeedsCursor(self):
        if self.inputIndex is not None:
            retVal = True
        else:
            retVal = False
        return retVal

    def CursorOff(self):
        self.window.CursorOff()
        
    def GetFieldValues(self):
        retVal = {}
        for fieldName in self.inputFields:
            retVal[fieldName] = self.fields[fieldName].fieldObj.Content()
        return retVal

    def Refresh(self):
        self.Win().Refresh();

    def ColoursSet(self, inBase, inBright, inHighlight = None, inTitle = None):
        self.baseColour = inBase
        self.brightColour = inBright
        self.highlightColour = inHighlight or inBright
        self.titleColour = inTitle or inBright
        self.window.DefaultColourSet(self.baseColour)
        self.window.Redraw()

    def ResetPosition(self, inXPos = None, inYPos = None):
        self.xPos = self.xOffset + FirstValue(inXPos, self.TITLE_XSTART)
        self.yPos = self.yOffset + FirstValue(inYPos, self.TITLE_YSTART)
        self.xStart = self.xPos

    def MakeLabel(self, inLabel = None):
        if inLabel:
            retVal = inLabel
        else:
            # Generate unique but repeatable label
            retVal = str(self.xPos) + ',' +str(self.yPos)
        return retVal

    def AddField(self, inObj, inTag = None):
        self.fields[inTag or self.MakeLabel()] = Struct(xpos = self.xPos, ypos = self.yPos, fieldObj = inObj)
        self.xPos += inObj.Width()
        return inObj

    def NewLine(self, inNumLines = None):
        self.xPos = self.xStart
        self.yPos += inNumLines or 1

    def AddTitleField(self, inTitle):
        self.AddField(TextField(inTitle, self.titleColour))
        self.NewLine(2)
        
    def AddTextField(self, inText):
        self.AddField(TextField(inText, self.baseColour))
        self.NewLine()
    
    def AddWrappedTextField(self, inText):
        width = self.window.xSize - self.xPos - 1
        field = self.AddField(WrappedTextField(str(inText), width, self.baseColour))
        self.NewLine(field.Height())

    def AddWrappedBoldTextField(self, inText):
        width = self.window.xSize - self.xPos - 1
        field = self.AddField(WrappedTextField(str(inText), width, self.brightColour))
        self.NewLine(field.Height())

    def AddStatusField(self, inName, inValue):
        self.AddField(TextField(str(inName), self.brightColour))
        width = self.window.xSize - self.xPos - 1
        field = self.AddField(WrappedTextField(str(inValue), width, self.baseColour))
        self.NewLine(field.Height())
    
    def AddInputField(self, inName, inValue, inLabel):
        self.AddField(TextField(str(inName), self.brightColour))
        self.AddField(InputField(str(inValue), self.highlightColour), inLabel)
        self.inputFields.append(inLabel)
        self.NewLine()
    
    def AddPasswordField(self, inName, inValue, inLabel):
        self.AddField(TextField(str(inName), self.brightColour))
        passwordField = InputField(str(inValue), self.highlightColour)
        passwordField.HideText()
        self.AddField(passwordField, inLabel)        
        self.inputFields.append(inLabel)
        self.NewLine()
    
    def AddMenuField(self, inMenu):
        field = self.AddField(MenuField(inMenu, self.baseColour, self.highlightColour))
        self.NewLine(field.Height() + 1)
    
    def AddKeyHelpField(self, inKeys):
        (oldXPos, oldYPos) = (self.xPos, self.yPos)
        self.xPos = self.xOffset + 1
        self.yPos = self.yOffset + self.ySize - 1
        for name in sorted(inKeys):
            self.AddField(TextField(str(name), self.brightColour))
            self.xPos += 1
            self.AddField(TextField(str(inKeys[name]), self.baseColour))
            self.xPos += 1

        (self.xPos, self.yPos) = (oldXPos, oldYPos)
    
    def Render(self):
        self.window.Erase()
        for field in self.fields.values():
            field.fieldObj.Render(self.window, field.xpos, field.ypos)
        self.window.Refresh()
            
    def Delete(self):
        self.window.Delete()
