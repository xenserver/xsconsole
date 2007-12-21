# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

import XenAPI # For XenAPI.Failure

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
        # Return an array of string that are at most inWidth characters long
        retArray = []
        text = inText+" "
        while len(text) > 0:
            spacePos = text.rfind(' ', 0, inWidth+1) # returns max (lastParam-1), i.e. 'aaaaa'.rfind('a', 0, 3) == 2
            retPos = text.find("\r", 0, inWidth+1)
            if retPos == -1:
                retPos = text.find("\n", 0, inWidth+1)
            if retPos != -1:
                spacePos = retPos
            if spacePos == -1:
                lineLength = inWidth
            else:
                lineLength = spacePos
            
            thisLine = text[:lineLength]
            thisLine = thisLine.replace("\t", " ") # Tab is used as a non-breaking space
            thisLine = thisLine.replace("\r", "RET") # Debugging
            retArray.append(thisLine)
            
            if spacePos == -1:
                text = text[lineLength:] # Split at non-space/return, so keep
            else:
                text = text[lineLength+1:] # Split at space or return so discard
            
        return retArray
