
class Config:
    instance = None
    
    def __init__(self):
        self.colours = {
            # Colours specified as name : (red, green, blue), value range 0..999
            'fg_dark' : (444, 444, 333),
            'fg_normal' : (666, 666, 500),
            'fg_bright' : (999, 999, 750),
            'bg_dark' : (0, 0, 0), 
            'bg_normal' : (333, 0, 0), 
            'bg_bright' : (500, 0, 0), 
            
            # Recovery mode colours
            'recovery_fg_dark' : (444, 444, 333),
            'recovery_fg_normal' : (666, 666, 500),
            'recovery_fg_bright' : (999, 999, 750),
            'recovery_bg_dark' : (0, 0, 0), 
            'recovery_bg_normal' : (0, 150, 200), 
            'recovery_bg_bright' : (0, 200, 266)
            
        }
    
    @classmethod
    def Inst(cls):
        if cls.instance is None:
            cls.instance = Config()
        return cls.instance
    
    def Colour(self,  inName):
        return self.colours[inName]
    
