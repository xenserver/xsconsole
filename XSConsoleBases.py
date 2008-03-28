# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

# App-wide imports
import copy, inspect, re
from pprint import pprint


# Global functions
def ParamsToAttr():
        d = inspect.currentframe().f_back.f_locals
        obj = d.pop("self")
        for name, value in d.iteritems():
            setattr(obj, name,value)

def FirstValue(*inArgs):
    for arg in inArgs:
        if arg != None:
            return arg
    return None

class Struct:
    def __init__(self, *inArgs, **inKeywords):
        for k, v in inKeywords.items():
            setattr(self, k, v)
        
