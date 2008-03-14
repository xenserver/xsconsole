# Copyright (c) Citrix Systems 2008. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")
    
from XSConsoleStandard import *
from XSConsolePlugIn import *

class TimezoneDialogue(Dialogue):
    def __init__(self):
        Dialogue.__init__(self)

        data=Data.Inst()
            
        choiceDefs = []
        
        continents = data.timezones.continents({})
        keys = sorted(continents.keys())
        
        for key in keys:
            choiceDefs.append(ChoiceDef(key, lambda: self.HandleContinentChoice(continents[keys[self.continentMenu.ChoiceIndex()]]) ))
        
        self.continentMenu = Menu(self, None, Lang("Select Continent"), choiceDefs)
    
        self.ChangeState('INITIAL')
        
    def BuildPane(self):
        if self.state == 'CITY':
            self.cityList = []
            choiceDefs = []
            cityExp = re.compile(self.continentChoice)
            keys = Data.Inst().timezones.cities({}).keys()
            keys.sort()
            for city in keys:
                if cityExp.match(city):
                    self.cityList.append(city)
                    choiceDefs.append(ChoiceDef(city, lambda: self.HandleCityChoice(self.cityMenu.ChoiceIndex())))
        
            if len(choiceDefs) == 0:
                choiceDefs.append(Lang('<None available>'), None)
        
            self.cityMenu = Menu(self, None, Lang("Select City"), choiceDefs)
            
        pane = self.NewPane(DialoguePane(self.parent))
        pane.TitleSet(Lang("Set Timezone"))
        pane.AddBox()
        self.UpdateFields()
        
    def UpdateFieldsINITIAL(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Select Your Region"))
        pane.AddMenuField(self.continentMenu, 11) # There are 11 'continents' so make this menu 11 high
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
    
    def UpdateFieldsCITY(self):
        pane = self.Pane()
        pane.ResetFields()
        
        pane.AddTitleField(Lang("Please Choose a City Within Your Timezone"))
        pane.AddMenuField(self.cityMenu)
        pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK") , Lang("<Esc>") : Lang("Cancel") } )
        
    def UpdateFields(self):
        self.Pane().ResetPosition()
        getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
    
    def ChangeState(self, inState):
        self.state = inState
        self.BuildPane()
    
    def HandleKeyINITIAL(self, inKey):
        return self.continentMenu.HandleKey(inKey)
     
    def HandleKeyCITY(self, inKey):
        return self.cityMenu.HandleKey(inKey)
        
    def HandleKey(self, inKey):
        handled = False
        if hasattr(self, 'HandleKey'+self.state):
            handled = getattr(self, 'HandleKey'+self.state)(inKey)
        
        if not handled and inKey == 'KEY_ESCAPE':
            Layout.Inst().PopDialogue()
            handled = True

        return handled
            
    def HandleContinentChoice(self,  inChoice):
        self.continentChoice = inChoice
        self.ChangeState('CITY')

    def HandleCityChoice(self,  inChoice):
        city = self.cityList[inChoice]
        data=Data.Inst()
        Layout.Inst().PopDialogue()
        try:
            data.TimezoneSet(city)
            message = Lang('The timezone has been set to ')+city +".\n\nLocal time is now "+data.CurrentTimeString()
            Layout.Inst().PushDialogue(InfoDialogue( Lang('Timezone Set'), message))
        except Exception, e:
            Layout.Inst().PushDialogue(InfoDialogue( Lang("Configuration failed: ")+Lang(e)))

        data.Update()


class XSFeatureTimezone(PlugIn):
    def __init__(self):
        PlugIn.__init__(self)
        
    @classmethod
    def StatusUpdateHandler(cls, inPane):
        data = Data.Inst()
        inPane.AddTitleField(Lang("Set Timezone"))
        
        inPane.AddWrappedTextField(Lang("Use this option to set the timezone for this server."))
        inPane.NewLine()
        if data.timezones.current('') != '':
            inPane.AddWrappedTextField(Lang("The current timezone is"))
            inPane.NewLine()
            inPane.AddWrappedTextField(data.timezones.current(Lang('<Unknown>')))
            inPane.NewLine()
        
        inPane.AddKeyHelpField( {
            Lang("<Enter>") : Lang("Set Timezone")
        })
        
    @classmethod
    def ActivateHandler(cls):
        DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(TimezoneDialogue()))
        
    def Register(self):
        data = Data.Inst()
        Importer.RegisterNamedPlugIn(
            self,
            'TIMEZONE', # Key of this plugin for replacement, etc.
            {
                'title' : Lang('Set Timezone'), # Name of this plugin for plugin list
                'menuname' : 'MENU_MANAGEMENT',
                'menupriority' : 200,
                'menutext' : Lang('Set Timezone') ,
                'statusupdatehandler' : self.StatusUpdateHandler,
                'activatehandler' : self.ActivateHandler
            }
        )

# Register this plugin when module is imported
XSFeatureTimezone().Register()
