# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

from XSConsoleBases import *
from XSConsoleLang import *

class Field:
    FLOW_INVALID=0
    FLOW_NONE=1
    FLOW_RIGHT=2
    FLOW_RETURN=3
    FLOW_DOUBLERETURN=4

    LAYOUT_MINWIDTH = 48 # Minimum width for dialogue

    def Flow(self):
        return self.flow

    def UpdateWidth(self, inWidth):
        pass

class SeparatorField(Field):
    def __init__(self, flow):
        ParamsToAttr()
        
    def Render(self, inPane, inX, inY):
        pass

    def Width(self):
        return 1

    def Height(self):
        return 1

class InputField(Field):
    def __init__(self, text, colour, flow):
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
        return max(40, len(self.text))
    
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

class TextField(Field):
    def __init__(self, text, colour, flow):
        ParamsToAttr()
        
    def Render(self, inPane, inX, inY):
        inPane.AddWrappedText(self.text, inX, inY, self.colour)

    def Width(self):
        return len(self.text)

    def Height(self):
        return 1
        
class WrappedTextField(Field):
    def __init__(self, text, colour, flow):
        ParamsToAttr()
        self.wrappedWidth = None
        self.wrappedText = []
        self.centred = False
        
    def SetCentred(self):
        self.centred = True
        
    def UpdateWidth(self, inWidth):
        if self.wrappedWidth is None or self.wrappedWidth != inWidth:
            self.wrappedWidth = inWidth
            self.wrappedText = Language.ReflowText(self.text, self.wrappedWidth)

    def Render(self, inPane, inXPos, inYPos):
        yPos = inYPos
        for line in self.wrappedText:
            if self.centred:
                offset = (self.wrappedWidth - len(line)) / 2
                inPane.AddText(line, inXPos+offset, yPos, self.colour)
            else:
                inPane.AddText(line, inXPos, yPos, self.colour)
                        
            yPos += 1

    def Width(self):
        retVal = 1
        for line in self.wrappedText:
            retVal = max(retVal, len(line))
        return retVal

    def Height(self):
        return len(self.wrappedText)

class MenuField(Field):
    def __init__(self, menu, colour, highlight, height, flow):
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

class FieldGroup:
    def __init__(self):
        self.Reset()
        
    def Reset(self):
        self.bodyFields = []
        self.bodyFieldNames = []
        self.staticFields = []
        self.staticFieldNames = []
        # Fields are ordered, so the order of field names is recorded here and the fields themselves are in bodyFields
        self.inputOrder = []
        self.inputTags = {}
        
    def NumStaticFields(self):
        return len(self.staticFields)

    def NumInputFields(self):
        return len(self.inputOrder)

    def BodyFields(self):
        return self.bodyFields

    def StaticFields(self):
        return self.staticFields

    def InputField(self, inIndex):
        return self.inputOrder[inIndex]
        
    def BodyFieldAdd(self, inTag, inField):
        self.bodyFields.append(inField)
        
    def StaticFieldAdd(self, inTag, inField):
        self.staticFields.append(inField)
    
    def InputFieldAdd(self, inTag, inField):
        # Three reference to the same field
        self.inputTags[inTag] = inField
        self.inputOrder.append(inField)
        self.bodyFields.append(inField)

    def GetFieldValues(self):
        retVal = {}
        for key, field in self.inputTags.iteritems():
            retVal[key] = field.Content()

        return retVal
        
class FieldArranger:
    BOXWIDTH = 1
    BORDER = 1
    
    def __init__(self, inFieldGroup, inXSize, inYSize):
        self.fieldGroup = inFieldGroup
        self.baseXSize = inXSize
        self.baseYSize = inYSize
        self.hasBox = False
        self.layoutXSize = None
        self.layoutYSize = None
    
    def XSizeSet(self, inXSize):
        self.baseXSize = inXSize
        self.layoutXSize = None
        self.layoutYSize = None
    
    def YSizeSet(self, inYSize):
        self.baseYSize = inYSize
        self.layoutXSize = None
        self.layoutYSize = None
    
    def XSize(self):
        if self.layoutXSize is None:
            self.layoutXSize = max(self.BodyLayout().pop().xpos, self.StaticLayout().pop().xpos)
        return max(self.layoutXSize, Field.LAYOUT_MINWIDTH)
    
    def YSize(self):
        if self.layoutYSize is None:
            self.layoutYSize = self.BodyLayout().pop().ypos # Static layout not included
        return self.layoutYSize
    
    def XBounds(self):
        if self.hasBox:
            retVal = self.XSize()+4
        else:
            retVal = self.XSize()+2
        return retVal
            
    def YBounds(self):
        if self.hasBox:
            retVal = self.YSize()+3
        else:
            retVal = self.YSize()+1
        return retVal
        
    def AddBox(self):
        self.hasBox = True

    def LayoutFields(self, inFields, inYStep):
        if self.hasBox:
            xOffset = self.BOXWIDTH
            yOffset = self.BOXWIDTH
            xSize = self.baseXSize - self.BOXWIDTH
            ySize = self.baseYSize - self.BOXWIDTH
        else:
            xOffset = 0
            yOffset = 0
            xSize = self.baseXSize
            ySize = self.baseYSize
    
        xStart = xOffset+self.BORDER
        if inYStep >= 0:
            yStart = yOffset+self.BORDER
        else:
            # If inYStep is negative, start from the bottom
            yStart = ySize - self.BORDER
        
        xPos = xStart
        yPos = yStart
        
        xMax = xPos
        
        retVal = []
        for field in inFields:
            flow = field.Flow()
            
            retVal.append(Struct(xpos = xPos, ypos = yPos))
            
            field.UpdateWidth((xSize - self.BORDER) - xPos)
            xMax = max(xMax, xPos + field.Width())
            
            if flow == Field.FLOW_RIGHT:
                xPos += field.Width() + 1
            elif flow == Field.FLOW_RETURN:
                xPos = xStart
                yPos += inYStep * field.Height()
            elif flow == Field.FLOW_DOUBLERETURN:
                xPos = xStart
                yPos += inYStep * (field.Height()+1)
            elif flow == Field.FLOW_NONE:
                pass # Leave xPos and yPos as they are
            else:
                raise Exception("Unknown flow type: "+str(flow))
        
        retVal.append(Struct(xpos = xMax, ypos = yPos)) # End marker

        return retVal

    def BodyLayout(self):
        return self.LayoutFields(self.fieldGroup.BodyFields(), 1)

    def StaticLayout(self):
        return self.LayoutFields(self.fieldGroup.StaticFields(), -1)

class FieldInputTracker:
    def __init__(self, inFieldGroup):
        self.fieldGroup = inFieldGroup
        self.inputIndex = None
    
    def ActivateNextInput(self): 
        self.InputIndexSet((self.inputIndex + 1) % self.fieldGroup.NumInputFields())
            
    def ActivatePreviousInput(self):
        numFields = self.fieldGroup.NumInputFields()
        self.InputIndexSet((self.inputIndex + numFields - 1) % numFields)
            
    def IsLastInput(self):
        return self.inputIndex + 1 == self.fieldGroup.NumInputFields()

    def CurrentInput(self):
        if self.inputIndex is not None:
            retVal = self.fieldGroup.InputField(self.inputIndex)
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
