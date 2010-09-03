# Copyright (c) 2009 Citrix Systems Inc.
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

class EULADialogue(Dialogue):
    def __init__(self, inFilename):
        Dialogue.__init__(self)

        xSize = Layout.Inst().APP_XSIZE
        ySize = Layout.Inst().APP_YSIZE

        self.filename = inFilename
        try:
            file = open(inFilename)
            try:
                contents = ''.join(file.readlines())
            finally:
                file.close()
        except Exception, e:
            contents = str(e)
        
        self.maxLine = 0
        for line in contents.split('\n'):
            self.maxLine = max(self.maxLine, len(line))
        self.padding = ' ' * max(0, (xSize - 4 - self.maxLine) / 2)
        
        self.text = Lang("End User License Agreement")
        self.info = contents
        paneSizer = PaneSizerFixed(0, 1, xSize, ySize - 1)
        pane = self.NewPane(DialoguePane(self.parent, paneSizer))
        pane.AddBox()
        self.UpdateFields()
        
    def UpdateFields(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddWrappedCentredBoldTextField(self.text)

        if self.info is not None:
            pane.NewLine()
            # Add one field per line to preserve preformatting
            for line in self.info.split('\n'):
                pane.AddTextField(self.padding+line)
                pane.NewLine()

        helpKeys = { Lang("<Enter>") : Lang("Accept") , Lang("<Esc>") : Lang("Decline") }
        if pane.NeedsScroll():
            helpKeys.update({
                Lang("<Page Up/Down>") : Lang("Scroll")
            })

        pane.AddKeyHelpField( helpKeys )
        
    def HandleKey(self, inKey):
        handled = True
        if inKey == 'KEY_ESCAPE':
            Importer.ActivateNamedPlugIn('SHUTDOWN', Lang("You must accept the End User License Agreement to continue.  Would you like to shutdown?"))
        elif inKey == 'KEY_ENTER':
            XSLog("User accepted EULA '"+self.filename+"'")
            Layout.Inst().PopDialogue()
        elif inKey == 'KEY_PPAGE':
            for i in range(20):
                self.Pane().ScrollPageUp()
        elif inKey == 'KEY_NPAGE':
            for i in range(20):
                self.Pane().ScrollPageDown()
        elif inKey == 'KEY_UP':
            self.Pane().ScrollPageUp()
        elif inKey in ('KEY_DOWN', ' '):
            self.Pane().ScrollPageDown()
        else:
            handled = False
        return handled

class XSFeatureEULA:
    @classmethod
    def ActivateHandler(cls, *inParams):
        for eula in Config.Inst().FirstBootEULAs():
            Layout.Inst().PushDialogue(EULADialogue(eula, *inParams))
        
    def Register(self):
        Importer.RegisterNamedPlugIn(
            self,
            'EULA', # This key is referred to by name in XSConsoleTerm.py
            {
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureEULA().Register()
