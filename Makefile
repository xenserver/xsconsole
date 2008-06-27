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
SCRIPTS += XSConsoleFields.py
SCRIPTS += XSConsoleHotData.py
SCRIPTS += XSConsoleImporter.py
SCRIPTS += XSConsoleKeymaps.py
SCRIPTS += XSConsoleLang.py
SCRIPTS += XSConsoleLangErrors.py
SCRIPTS += XSConsoleLangFriendlyNames.py
SCRIPTS += XSConsoleLayout.py
SCRIPTS += XSConsoleMenus.py
SCRIPTS += XSConsoleRemoteDB.py
SCRIPTS += XSConsoleRootDialogue.py
SCRIPTS += XSConsoleStandard.py
SCRIPTS += XSConsoleState.py
SCRIPTS += XSConsoleTask.py
SCRIPTS += XSConsoleTerm.py
SCRIPTS += XSConsoleUtils.py

PLUGINS_BASE :=
PLUGINS_BASE += XSFeatureChangePassword.py
PLUGINS_BASE += XSFeatureChangeTimeout.py
PLUGINS_BASE += XSFeatureCrashDumpSR.py
PLUGINS_BASE += XSFeatureDRBackup.py
PLUGINS_BASE += XSFeatureDRRestore.py
PLUGINS_BASE += XSFeatureDNS.py
PLUGINS_BASE += XSFeatureDisplayNICs.py
PLUGINS_BASE += XSFeatureHostCommon.py
PLUGINS_BASE += XSFeatureHostEvacuate.py
PLUGINS_BASE += XSFeatureHostInfo.py
PLUGINS_BASE += XSFeatureInstallLicence.py
PLUGINS_BASE += XSFeatureInterface.py
PLUGINS_BASE += XSFeatureKeyboard.py
PLUGINS_BASE += XSFeatureLocalShell.py
PLUGINS_BASE += XSFeatureLogInOut.py
PLUGINS_BASE += XSFeatureNTP.py
PLUGINS_BASE += XSFeatureQuit.py
PLUGINS_BASE += XSFeaturePoolEject.py
PLUGINS_BASE += XSFeaturePoolJoin.py
PLUGINS_BASE += XSFeatureReboot.py
PLUGINS_BASE += XSFeatureRemoteShell.py
PLUGINS_BASE += XSFeatureSRCommon.py
PLUGINS_BASE += XSFeatureSRCreate.py
PLUGINS_BASE += XSFeatureSRInfo.py
PLUGINS_BASE += XSFeatureSaveBugReport.py
PLUGINS_BASE += XSFeatureShutdown.py
PLUGINS_BASE += XSFeatureStatus.py
PLUGINS_BASE += XSFeatureSuspendSR.py
PLUGINS_BASE += XSFeatureSyslog.py
PLUGINS_BASE += XSFeatureSystem.py
PLUGINS_BASE += XSFeatureTestNetwork.py
PLUGINS_BASE += XSFeatureTimezone.py
PLUGINS_BASE += XSFeatureUploadBugReport.py
PLUGINS_BASE += XSFeatureValidate.py
PLUGINS_BASE += XSFeatureVMCommon.py
PLUGINS_BASE += XSFeatureVMInfo.py
PLUGINS_BASE += XSMenuLayout.py

PLUGINS_OEM :=
PLUGINS_OEM += XSFeatureClaimSR.py
PLUGINS_OEM += XSFeatureManagementHelp.py
PLUGINS_OEM += XSFeatureOEMBackup.py
PLUGINS_OEM += XSFeatureOEMRestore.py
PLUGINS_OEM += XSFeatureOEMRevert.py
PLUGINS_OEM += XSFeatureRemoteDB.py
PLUGINS_OEM += XSFeatureReset.py
PLUGINS_OEM += XSFeatureUpdate.py
PLUGINS_OEM += XSFeatureVerboseBoot.py
PLUGINS_OEM += XSMenuOEMLayout.py

PLUGINS_EXTRAS :=

ALL_SCRIPTS := $(SCRIPTS)
ALL_SCRIPTS += $(addprefix plugins-base/, $(PLUGINS_BASE))
ALL_SCRIPTS += $(addprefix plugins-oem/, $(PLUGINS_OEM))
ALL_SCRIPTS += $(addprefix plugins-extras/, $(PLUGINS_EXTRAS))

################################################################################
# Executable:
COMMAND := xsconsole

################################################################################
# Documents

#DOCUMENTS :=
#DOCUMENTS += LICENSE

################################################################################
install-base:
	mkdir -p $(LIBDIR)/xsconsole/
	mkdir -p $(LIBDIR)/xsconsole/plugins-base
	mkdir -p $(LIBDIR)/xsconsole/plugins-extras

	$(foreach script,$(SCRIPTS),\
          $(INSTALL) -m $(LIB_MODE) $(script) $(LIBDIR)/xsconsole;)

	$(foreach script,$(PLUGINS_BASE),\
          $(INSTALL) -m $(LIB_MODE) plugins-base/$(script) $(LIBDIR)/xsconsole/plugins-base;)

	$(foreach script,$(PLUGINS_EXTRAS),\
          $(INSTALL) -m $(LIB_MODE) plugins-extras/$(script) $(LIBDIR)/xsconsole/plugins-extras;)

	$(INSTALL) -m $(BIN_MODE) $(COMMAND) $(PREFIX)/bin

#	$(foreach docfile,$(DOCUMENTS),\
#          $(INSTALL) -m $(DOC_MODE) $(docfile) $(DOCDIR);)

install-oem:
	mkdir -p $(LIBDIR)/xsconsole/plugins-oem

	$(foreach script,$(PLUGINS_OEM),\
          $(INSTALL) -m $(LIB_MODE) plugins-oem/$(script) $(LIBDIR)/xsconsole/plugins-oem;)

clean:

depend:

all:

# Convenience targets for pylint output
pylint.html: pylint.rc $(ALL_SCRIPTS)
	pylint --rcfile pylint.rc --output-format html $(ALL_SCRIPTS) > $@

pylint.txt: pylint.rc $(ALL_SCRIPTS)
	if [ -f $@ ]; then mv $@ $@.tmp; fi
	pylint --rcfile pylint.rc --output-format text $(ALL_SCRIPTS) > $@
	# Show new/different warnings in stdout
	if [ -f $@.tmp ]; then diff $@.tmp $@ | grep -E '^[<>]\s*[CRWE]' | cat ; fi
	rm -f $@.tmp
