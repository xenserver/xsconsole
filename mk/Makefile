USE_BRANDING=yes
# makefile for xen component in build system
include $(B_BASE)/common.mk
include $(B_BASE)/rpmbuild.mk

REPO_NAME= xsconsole
RPM_BUILD_COOKIE= $(MY_OBJ_DIR)/.rpm_build_cookie

XSCONSOLE_VERSION := 0.1

-include $(MY_OBJ_DIR)/version.inc
$(MY_OBJ_DIR)/version.inc:
	rm -f $(MY_OBJ_DIR)/version.inc
	$(call version-makefile) >> $@
	awk -F. '{ print "REPO_VERSION=" $$0; }' \
		< $(call hg_req,xsconsole) >> $@
	$(call hg_cset_number,xsconsole) >> $@

XS_VERSION := $(XSCONSOLE_VERSION)
XS_RELEASE := $(CSET_NUMBER)

CHANGELOG_DATE    := $(shell LANG=C date +"%a %b %d %Y")
CHANGELOG_USER    := Citrix Inc. <citrix.com>
CHANGELOG_HEADER  := * $(CHANGELOG_DATE) $(CHANGELOG_USER) [$(XS_VERSION)-$(XS_RELEASE)]
CHANGELOG_MESSAGE := - Build XenServer Host Configuration Console.

.PHONY: build
build: $(RPM_BUILD_COOKIE) $(MY_SOURCES)/MANIFEST
	@ :

.PHONY: clean
clean: 
	rm -f $(RPM_BUILD_COOKIE)
	rm -f $(MY_OBJ_DIR)/version.inc

SOURCES = $(RPM_SOURCESDIR)/xsconsole-$(XS_VERSION).tar.bz2 \
          $(RPM_SPECSDIR)/xsconsole.spec

$(RPM_SOURCESDIR)/xsconsole-$(XS_VERSION).tar.bz2: $(RPM_SOURCESDIR)/.dirstamp $(call hg_loc,xsconsole)
	hg -R $(call hg_loc,xsconsole) archive -t tbz2 $@

$(RPM_SPECSDIR)/xsconsole.spec: xsconsole.spec.in $(RPM_SPECSDIR)/.dirstamp
# Use a temporary file because sed in rhel3 doesn't understand "\n"
	echo "$(CHANGELOG_HEADER)" > changelog.tmp
	echo "$(CHANGELOG_MESSAGE)" >> changelog.tmp
	echo "" >> changelog.tmp
	sed -e s\,@REPO_VERSION@,$(REPO_VERSION),g \
	    -e s\,@XS_VERSION@,$(XS_VERSION),g     \
	    -e s\,@XS_RELEASE@,$(XS_RELEASE),g     \
	    -e \\,%changelog,rchangelog.tmp        \
	    < xsconsole.spec.in                         \
	    > $(RPM_SPECSDIR)/xsconsole.spec
	-rm changelog.tmp

$(RPM_BUILD_COOKIE): $(RPM_DIRECTORIES) $(SOURCES)
	$(RPMBUILD) --target i686 -ba $(RPM_SPECSDIR)/xsconsole.spec
	@touch $@

$(MY_SOURCES)/MANIFEST: $(MY_SOURCES_DIRSTAMP)
	echo "xsconsole proprietary file $(MY_OUTPUT_DIR)/SRPMS/xsconsole-$(XS_VERSION)-$(XS_RELEASE).src.rpm" >$@

.PHONY: sources
sources: $(MY_SOURCES)/MANIFEST
	@ :
