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
        Lang("Romanian") : 'ro',
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
        
        
