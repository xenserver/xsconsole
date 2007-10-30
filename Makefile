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
SCRIPTS += XSConsoleAuth.py
SCRIPTS += XSConsoleBases.py
SCRIPTS += XSConsoleCurses.py
SCRIPTS += XSConsoleData.py
SCRIPTS += XSConsoleDialogues.py
SCRIPTS += XSConsoleFields.py
SCRIPTS += XSConsoleLang.py
SCRIPTS += XSConsoleMenus.py
SCRIPTS += XSConsole.py
SCRIPTS += XSConsoleStructure.py
SCRIPTS += XSConsoleTerm.py


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

	$(foreach script,$(SCRIPTS),\
          $(INSTALL) -m $(LIB_MODE) $(script) $(LIBDIR)/xsconsole;)

	$(INSTALL) -m $(BIN_MODE) $(COMMAND) $(PREFIX)/bin

#	$(foreach docfile,$(DOCUMENTS),\
#          $(INSTALL) -m $(DOC_MODE) $(docfile) $(DOCDIR);)

clean:

depend:

all:
