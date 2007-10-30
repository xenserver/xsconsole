
import inspect

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
        
class Dialogue:
    def __init__(self, layout = None, parent = None):
        ParamsToAttr();
        self.panes = {}

    def Pane(self, inName):
        return self.panes[inName]

    def NewPane(self, inName, inPane):
        self.panes[inName] = inPane
        return inPane

    def Title(self):
        return self.title
        
    def Destroy(self):
        for pane in self.panes.values():
            pane.Delete()
            
    def Render(self):
        for pane in self.panes.values():
            pane.Render()
            
    def UpdateFields(self):
        pass        
            
