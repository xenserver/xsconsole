
# Global function
def Lang(inLabel, inPad = 0):
    retStr = Language.ToString(inLabel)
    if inPad > 0:
        retStr = retStr.ljust(inPad, ' ')
    return retStr
    
class Language:
    @classmethod
    def ToString(cls, inLabel):
        return inLabel

    @classmethod
    def ReflowText(cls, inText, inWidth):
        retArray = []
        text = inText+" "
        while len(text) > 0:
            spacePos = text.rfind(' ', 0, inWidth)
            retPos = text.find("\r", 0, inWidth)
            if retPos is -1:
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
