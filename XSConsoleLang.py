
import XenAPI

# Global function
def Lang(inLabel, inPad = 0):
    retStr = Language.ToString(inLabel)
    if inPad > 0:
        retStr = retStr.ljust(inPad, ' ')
    return retStr
    
class Language:
    @classmethod
    def Quantity(cls, inText, inNumber):
        if inNumber == 1:
            return Lang(inText)
        else:
            return Lang(inText+"s")

    @classmethod
    def ToString(cls, inLabel):
        if isinstance(inLabel, XenAPI.Failure):
            if inLabel.details[0] == 'INTERNAL_ERROR':
                retVal = str(inLabel) # Print everything for this one
            else:
                retVal = inLabel.details[0]
        elif isinstance(inLabel, Exception):
            retVal = str(inLabel)
        else:
            retVal = inLabel
                
        return retVal

    @classmethod
    def ReflowText(cls, inText, inWidth):
        retArray = []
        text = inText+" "
        while len(text) > 0:
            spacePos = text.rfind(' ', 0, inWidth)
            retPos = text.find("\r", 0, inWidth)
            if retPos == -1:
                retPos = text.find("\n", 0, inWidth)
            if retPos != -1:
                spacePos = retPos
            if spacePos == -1:
                lineLength = inWidth
            else:
                lineLength = spacePos
            
            thisLine = text[0:lineLength]
            thisLine = thisLine.replace("\t", " ") # Tab is used as a non-breaking space
            thisLine = thisLine.replace("\r", "RET")
            retArray.append(thisLine)
            text = text[lineLength+1:]
        
        return retArray
