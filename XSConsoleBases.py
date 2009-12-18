# Copyright (c) 2007-2009 Citrix Systems Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

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
        
    def __repr__(self):
        return str(self.__dict__)
