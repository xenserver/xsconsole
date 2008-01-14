# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

from XSConsoleBases import *
from XSConsoleCurses import *
from XSConsoleFields import *
from XSConsoleLang import *

class PaneSizer:
    def __init__(self):
        pass
        
    def Update(self, inSource):
        pass
    
    def XPos(self):
        return self.xPos

    def YPos(self):
        return self.yPos

    def XSize(self):
        return self.xSize

    def YSize(self):
        return self.ySize
        
class PaneSizerFixed(PaneSizer):
    def __init__(self, inXPos, inYPos, inXSize, inYSize):
        self.xPos = inXPos
        self.yPos = inYPos
        self.xSize = inXSize
        self.ySize = inYSize

class PaneSizerCentre(PaneSizer):
    def __init__(self, inParent):
        self.parent = inParent
        self.xSize = self.parent.XSize()
        self.ySize = self.parent.YSize()
        self.xPos = 0
        self.yPos = 0
    
    def Update(self, inArranger):
        self.xSize = min(inArranger.XBounds(), self.parent.XSize() - 4)
        self.ySize = min(inArranger.YBounds(), self.parent.YSize() - 4)
        self.xPos = (self.parent.XSize() - self.xSize) / 2
        self.yPos = (self.parent.YSize() - self.ySize) / 2

class DialoguePane:    
    def __init__(self, inParent = None, inSizer = None):
        self.parent = inParent
        self.sizer = FirstValue(inSizer, PaneSizerCentre(self.parent))
        self.window = None
        self.fieldGroup = FieldGroup()
        self.arranger = FieldArranger(self.fieldGroup, self.sizer.XSize(), self.sizer.YSize())
        self.inputTracker = FieldInputTracker(self.fieldGroup)
        self.yScrollPos = 0
        self.title = None
        self.hasBox = False
        
    def ResetPosition(self):
        self.arranger.Reset()

    # Delegations to FieldGroup
    def ResetFields(self): self.fieldGroup.Reset()
    def NumStaticFields(self): return self.fieldGroup.NumStaticFields()
    def GetFieldValues(self): return self.fieldGroup.GetFieldValues()

    # Delegations to FieldInputTracker
    def ActivateNextInput(self): return self.inputTracker.ActivateNextInput()
    def ActivatePreviousInput(self): return self.inputTracker.ActivatePreviousInput()
    def IsLastInput(self): return self.inputTracker.IsLastInput()
    def CurrentInput(self): return self.inputTracker.CurrentInput()
    def InputIndexSet(self, inIndex): return self.inputTracker.InputIndexSet(inIndex)
    def NeedsCursor(self): return self.inputTracker.NeedsCursor()

    def RemakeWindow(self):
        if self.window is not None:
            self.window.Delete()
        self.sizer.Update(self.arranger)
        self.arranger.XSizeSet(self.sizer.XSize())
        self.arranger.YSizeSet(self.sizer.YSize())

        self.window = CursesWindow(self.sizer.XPos(), self.sizer.YPos(), self.sizer.XSize(), self.sizer.YSize(), self.parent)
        if self.title is not None:
            self.window.TitleSet(self.title)
        if self.hasBox:
            self.window.AddBox()

    def CursorOff(self):
        self.Win().CursorOff()
        
    def Refresh(self):
        self.Win().Refresh()

    def Win(self):
        if self.window is None:
            self.RemakeWindow()
        return self.window

    def AddBox(self):
        self.hasBox = True
        if self.window is not None:
            self.window.AddBox()
        self.arranger.AddBox()
    
    def TitleSet(self, inTitle):
        self.title = inTitle
    
    def NeedsScroll(self):
        return self.arranger.YSize() >= self.Win().YSize()

    def ScrollPageUp(self):
        if self.yScrollPos > 0:
            self.yScrollPos -= 1
        
    def ScrollPageDown(self):
        if self.yScrollPos + self.Win().YSize() <= self.arranger.YSize():
            self.yScrollPos += 1

    def ResetScroll(self):
        self.yScrollPos =0

    def ColoursSet(self, inBase, inBright, inHighlight = None, inTitle = None):
        self.baseColour = inBase
        self.brightColour = inBright
        self.highlightColour = inHighlight or inBright
        self.titleColour = inTitle or inBright

    def MakeLabel(self, inLabel = None):
        return inLabel

    def AddBodyFieldObj(self, inObj, inTag = None):
        self.fieldGroup.BodyFieldAdd(inTag or self.MakeLabel(), inObj)
        return inObj

    def AddStaticFieldObj(self, inObj, inTag = None):
        self.fieldGroup.StaticFieldAdd(inTag or self.MakeLabel(), inObj)
        return inObj

    def AddInputFieldObj(self, inObj, inTag = None):
        self.fieldGroup.InputFieldAdd(inTag or self.MakeLabel(), inObj)
        return inObj

    def NewLine(self, inNumLines = None):
        self.AddBodyFieldObj(SeparatorField(Field.FLOW_RETURN))

    def AddTitleField(self, inTitle):
        self.AddBodyFieldObj(TextField(inTitle, self.titleColour, Field.FLOW_DOUBLERETURN))
        
    def AddTextField(self, inText, inFlow = None):
        self.AddBodyFieldObj(TextField(inText, self.baseColour, FirstValue(inFlow, Field.FLOW_RIGHT)))
    
    def AddWrappedTextField(self, inText, inFlow = None):
        field = self.AddBodyFieldObj(WrappedTextField(str(inText), self.baseColour, FirstValue(inFlow, Field.FLOW_RETURN)))

    def AddWrappedBoldTextField(self, inText, inFlow = None):
        field = self.AddBodyFieldObj(WrappedTextField(str(inText), self.brightColour, FirstValue(inFlow, Field.FLOW_RETURN)))

    def AddWrappedCentredTextField(self, inText, inFlow = None):
        field = self.AddBodyFieldObj(WrappedTextField(str(inText), self.baseColour, FirstValue(inFlow, Field.FLOW_RETURN)))
        field.SetCentred()

    def AddWrappedCentredBoldTextField(self, inText, inFlow = None):
        field = self.AddBodyFieldObj(WrappedTextField(str(inText), self.brightColour, FirstValue(inFlow, Field.FLOW_RETURN)))
        field.SetCentred()

    def AddStatusField(self, inName, inValue):
        self.AddBodyFieldObj(TextField(str(inName), self.brightColour, Field.FLOW_RIGHT))
        self.AddBodyFieldObj(WrappedTextField(str(inValue), self.baseColour, Field.FLOW_RETURN))
    
    def AddInputField(self, inName, inValue, inLabel):
        self.AddBodyFieldObj(TextField(str(inName), self.brightColour, Field.FLOW_RIGHT))
        self.AddInputFieldObj(InputField(str(inValue), self.highlightColour, Field.FLOW_RETURN), inLabel)
    
    def AddPasswordField(self, inName, inValue, inLabel):
        self.AddBodyFieldObj(TextField(str(inName), self.brightColour, Field.FLOW_RIGHT))
        passwordField = InputField(str(inValue), self.highlightColour, Field.FLOW_RETURN)
        passwordField.HideText()
        self.AddInputFieldObj(passwordField, inLabel)
    
    def AddMenuField(self, inMenu, inHeight = None):
        # Arbitrarily limit menu size to 10 lines
        field = self.AddBodyFieldObj(MenuField(inMenu, self.baseColour, self.highlightColour, FirstValue(inHeight, 10), Field.FLOW_RETURN))
    
    def AddKeyHelpField(self, inKeys):
        for name in sorted(inKeys):
            self.AddStaticFieldObj(TextField(str(name), self.brightColour, Field.FLOW_RIGHT))
            self.AddStaticFieldObj(TextField(str(inKeys[name]), self.baseColour, Field.FLOW_RIGHT))

    def Render(self):
        win = self.Win()
        win.DefaultColourSet(self.baseColour)
        win.Erase()
        
        # Shrink the clip window to allow space for the static fields
        ySize = win.YSize() - 1
        win.YClipMaxSet(ySize)
        
        bodyLayout = self.arranger.BodyLayout()
        
        for field in self.fieldGroup.BodyFields():
            layout = bodyLayout.pop(0)
            # Check whether visible - first whether off the top, then whether off the bottom
            if layout.ypos + field.Height() > self.yScrollPos and layout.ypos <= self.yScrollPos + ySize:

                field.Render(win, layout.xpos, layout.ypos - self.yScrollPos)
        
        win.YClipMaxSet(win.YSize())
        
        staticLayout = self.arranger.StaticLayout()
        
        for field in self.fieldGroup.StaticFields():
            # Static fields aren't affected by the scroll position, and get a larger clip window
            # so then can fill the bottom line
            layout = staticLayout.pop(0)
            field.Render(win, layout.xpos, layout.ypos)

        win.Refresh()
            
    def Delete(self):
        self.Win().Delete()
        self.window = None
