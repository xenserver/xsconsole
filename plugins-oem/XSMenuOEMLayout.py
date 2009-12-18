# Copyright (c) 2008-2009 Citrix Systems Inc.
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

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *

class XSMenuOEMLayout:
            
    def ActivateHandler(self, inName):
        Layout.Inst().TopDialogue().ChangeMenu(inName)

    def Register(self):
        data = Data.Inst()
        
        rootMenuDefs = [
        ]
        
        priority = 850
        for menuDef in rootMenuDefs:

            Importer.RegisterMenuEntry(
                self,
                'MENU_ROOT', # Name of the menu this item is part of
                {
                    'menuname' : menuDef[0], # Name of the menu this item leads to when selected
                    'menutext' : menuDef[1],
                    'menupriority' : priority,
                    'activatehandler' : menuDef[2],
                    'statusupdatehandler' : menuDef[3]
                }
            )
            priority += 100

# Register this plugin when module is imported
XSMenuOEMLayout().Register()
