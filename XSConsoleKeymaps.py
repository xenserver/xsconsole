# Copyright (c) Citrix Systems 2007. All rights reserved.
# xsconsole is proprietary software.
#
# Xen, the Xen logo, XenCenter, XenMotion are trademarks or registered
# trademarks of Citrix Systems, Inc., in the United States and other
# countries.

from XSConsoleBases import *
from XSConsoleLang import *

class Keymaps:
    # Map common keyboard layout names to their most common keymaps
    namesToMaps = {
        Lang("Belgian") : 'be-latin1',
        Lang("Bulgarian") : 'bg-cp1251',
        Lang("Brazilian") : 'br-abnt2',
        Lang("Canadian French") : 'cf',
        Lang("Croatian") : 'croat',
        Lang("Czech") : 'cz',
        Lang("German") : 'de-latin1',
        Lang("Danish") : 'dk-latin1',
        Lang("Spanish") : 'es',
        Lang("Finnish") : 'fi-latin1',
        Lang("French") : 'fr-latin9',
        Lang("Greek") : 'gr',
        Lang("Hungarian") : 'hu',
        Lang("Icelandic") : 'is-latin1',
        Lang("Hebrew") : 'il',
        Lang("Italian") : 'it',
        Lang("Japanese") : 'jp106',
        Lang("Latin American") : 'la-latin1',
        Lang("Lithuanian") : 'lt',
        Lang("Macedonian") : 'mk',
        Lang("Dutch") : 'nl',
        Lang("Norwegian") : 'no-latin1',
        Lang("Polish") : 'pl2',
        Lang("Portugese") : 'pt-latin1',
        Lang("Romanian") : 'ro_win',
        Lang("Russian") : 'ru',
        Lang("Slovakian") : 'sk-qwertz',
        Lang("Slovenian") : 'slovene',
        Lang("Serbian") : 'sr-cy',
        Lang("Swedish") : 'sv-latin1',
        Lang("Turkish") : 'trq',
        Lang("Ukrainian") : 'ua-utf',
        Lang("United Kingdom") : 'uk',
        Lang("US International") : 'us-acentos',
        Lang("US English") : 'us'
        }
        
    @classmethod
    def NamesToMaps(cls):
        return cls.namesToMaps
        
        
