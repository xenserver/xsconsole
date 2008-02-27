################################################################################
# Makefile for xsconsole
# Copyright (c) Citrix Systems 2007

PREFIX=$(DESTDIR)/usr
LIBDIR=$(DESTDIR)/usr/lib/

INSTALL=/usr/bin/install

BIN_MODE := 755
LIB_MODE := 644
DOC_MODE := 644


################################################################################
# List of python scripts:
SCRIPTS :=
SCRIPTS += XSConsole.py
SCRIPTS += XSConsoleAuth.py
SCRIPTS += XSConsoleBases.py
SCRIPTS += XSConsoleConfig.py
SCRIPTS += XSConsoleCurses.py
SCRIPTS += XSConsoleData.py
SCRIPTS += XSConsoleDataUtils.py
SCRIPTS += XSConsoleDialogueBases.py
SCRIPTS += XSConsoleDialoguePane.py
SCRIPTS += XSConsoleDialogues.py
SCRIPTS += XSConsoleFields.py
SCRIPTS += XSConsoleImporter.py
SCRIPTS += XSConsoleKeymaps.py
SCRIPTS += XSConsoleLang.py
SCRIPTS += XSConsoleLangErrors.py
SCRIPTS += XSConsoleLayout.py
SCRIPTS += XSConsoleMenus.py
SCRIPTS += XSConsolePlugIn.py
SCRIPTS += XSConsoleRemoteDB.py
SCRIPTS += XSConsoleRootDialogue.py
SCRIPTS += XSConsoleStandard.py
SCRIPTS += XSConsoleState.py
SCRIPTS += XSConsoleTerm.py
SCRIPTS += XSConsoleUtils.py

PLUGINS_BASE :=
PLUGINS_BASE += XSFeatureInterface.py
PLUGINS_BASE += XSFeatureManagementHelp.py

PLUGINS_OEM :=

PLUGINS_EXTRAS :=

################################################################################
# Executable:
COMMAND := xsconsole

################################################################################
# Documents

#DOCUMENTS :=
#DOCUMENTS += LICENSE

################################################################################
install:
	mkdir -p $(LIBDIR)/xsconsole/
	mkdir -p $(LIBDIR)/xsconsole/plugins-base
	mkdir -p $(LIBDIR)/xsconsole/plugins-oem
	mkdir -p $(LIBDIR)/xsconsole/plugins-extras

	$(foreach script,$(SCRIPTS),\
          $(INSTALL) -m $(LIB_MODE) $(script) $(LIBDIR)/xsconsole;)

	$(foreach script,$(PLUGINS_BASE),\
          $(INSTALL) -m $(LIB_MODE) plugins-base/$(script) $(LIBDIR)/xsconsole/plugins-base;)

	$(foreach script,$(PLUGINS_OEM),\
          $(INSTALL) -m $(LIB_MODE) plugins-oem/$(script) $(LIBDIR)/xsconsole/plugins-oem;)

	$(foreach script,$(PLUGINS_EXTRAS),\
          $(INSTALL) -m $(LIB_MODE) plugins-extras/$(script) $(LIBDIR)/xsconsole/plugins-extras;)

	$(INSTALL) -m $(BIN_MODE) $(COMMAND) $(PREFIX)/bin

#	$(foreach docfile,$(DOCUMENTS),\
#          $(INSTALL) -m $(DOC_MODE) $(docfile) $(DOCDIR);)

clean:

depend:

all:
