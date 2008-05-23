Info for writing new plugins:
(Last updated 2008-05-22)

1.  Single menu items register themselves with Importer.RegisterNamedPlugIn, whereas dynamic menus register using Importer.RegisterMenuEntry.

2.  Use HotAccessor to access XAPI data, and not the older Data class.  Direct access to the xapi session is also possible.  You may need to add a Fetcher to XSConsoleHotData if you need to use model objects where no fetcher has been implemented in xsconsole.

Guidelines for using HotAccessor are:

(i) Expressions ending with an attribute, e.g. HotAccessor().local_host, return another accessor.

(ii) Square brackets, e.g. HotAccessor().host[hostRef] take a HotOpaqueRef to select a particular object.  HotOpaqueRefs just combine the XAPI OpaqueRef and the object type ('sr', 'vm', 'vdi', etc.).  Fetcher functions use HotData.ConvertOpaqueRefs to convert XAPI OpaqueRef strings to HotOpaqueRef objects when they fetch any object.

(iii) Empty brackets, e.g. HotAccessor().local_host().  Brackets are always needed when you want a final value and not antoher accessor.  If the element doesn't exists, None is returned, so mispelled element names won't raise exceptions.

(iv) Brackets with a parameter, e.g. HotAccessor().local_host.name_label('Unknown') will return the parameter iff the requested database item does not exist.

>>> HotAccessor().local_host.name_label('Unknown')
'vos1'
>>> HotAccessor().local_host.not_a_db_item('Unknown')
'Unknown'

(v) Iteration over accessors is generally better than iteration over results, e.g. These print the same thing:

for sr in HotAccessor().sr: # Iterate over HotAccessors
  print sr.name_label()

for value in HotAccessor().sr().values(): # Iterate over the returned dict of all SRs
  print value['name_label']

(vi) List comprehensions also work

>>> [ sr.name_label() for sr in HotAccessor().sr if sr.content_type() == 'iso' ]
['DVD drives', 'DVD drives', 'XenServer Tools']

HotAccessor currently re-fetches data once its cached versions expire, usually after 5 seconds.  There will be an invalidate-cache scheme later on.

HotAccessors can be used interactively for experimentation:

[root@vos1 ~]# python
Python 2.4.3 (#1, Mar 14 2007, 18:51:08)
[GCC 4.1.1 20070105 (Red Hat 4.1.1-52)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from XSConsole import *
>>> HotAccessor().local_host.name_label()
'vos1'
>>>

(vii) HotAccessors can raise exceptions.

3.  XAPI access can be wrapped in the Task class, e.g.

# Synchronous task (returns the result)
result = Task.Sync(lambda x: x.xenapi.VM.get_possible_hosts(opaqueRef))
# Asynchronous task (returns a TaskEntry object)
task = Task.New(lambda x: x.xenapi.Async.VM.clean_shutdown(opaqueRef))

4.  Try not to 'include' other plugin files, unless you can handle the case when they're not there.  The Importer.RegisterResource method used in e.g. XSFeatureSRCommon.py shows a way to use common files.

5.  Add all new python files to the Makefile in xsconsole.hg.

6.  A packager should be able to delete any PlugIn file (except Common files) and cleanly remove that feature.  OEM-specific features live in plugins-oem.

7.  PlugIns run with root privileges.

There are a few gotchas in the xsconsole code.  This is a list of a few of them.

1.  All of the XSConsolexxxx.py files are in the same namespace (as they're imported using 'from <file> import *').  When adding functions try to keep them within objects to prevent clashes.

2.  The app evolved a number of ways to execute shell commands.  For new code ShellPipe in XSConsoleUtils.py is the preferred option.

3.  New features (e.g. menu items) should be implemented as plugins.

4.  The field layout code in in FieldArranger is a bit hairy as it interacts with the automatic pane sizer PaneSizerCentre.  The code attempts to:

  (i)   Determine the size of the dialogue required by looking at the fields within it
  (ii)  Set the window to that size
  (iii) Arrange the fields again using that window size

Very rarely this gives a pane height one line to short, probably because the reflowed text in (i) is slightly different to that in (iii).

5.  If you display a dialogue with input fields, display another box (e.g. InfoDialogue) in front of it, and go back to the first dialogue, you'll probably lose the cursor.  ChangePasswordDialogue shows one way around this, setting CurrentInputIndex to None.

6.  UpdateFields generally recreates fields from scratch, so you can't just call it whenever you like because, e.g. values in text entry fields will be lost and cursors reset.  It's fine to update the root dialogue though.

7.  It's tricky to get the ncurses display to refresh without flicker.  Using the curses erase or clear methods on windows can lead to flickering redraws.  Currently only scrolling in the right hand pane of the root dialogue has this problem.  Since there's not much use of erase or clear the app does pretty minimal redraws, and things like spurious kernel message that scroll the screen can leave it in a mess for some time. 

8.  MountVDI's Create VDB/Plug VBD/Mount VBD/Use VBD/Unmount VBD/Unplug VBD/Destroy VBD sequence failed when trying to mount empty CD drives.  Now only MountVDIDirectly is used.

9.  Circular imports can be a problem in this app.  XSConsoleData.py (or anything it imports) can't import XSConsoleDataUtils.py, for example, and if it does the app throws weird exceptions about missing names that don't make sense.  Similarly for the XSConsoleData.py/XSConsoleAuth.py/XSConsoleState.py trio.

10.  Data.Inst().Update() is a fairly expensive operation as it reloads and reprocesses almost everything.

11.  BannerDialogues shouldn't be left on the dialogue stack when you return to the main loop.  Use TransientBanner instead.  If you want a dialogue box that persists you need an InfoDialogue, which is the same thing with an <Enter> OK help field and a keypress handler.

12.  In OEM builds xsconsole is started from inittab with a pretty minimal enviroment.  There's no PATH set up, and /usr/bin/xsconsole sets USER itself (since scripts like xen-bugtool require it).

13.  Use the BuildPane/UpdateFields structure in PlugIns to get the right Dialogue box sizes.  A pane's size is determined once only, when it's first drawn, so BuildPane creates a new pane each time, but it doesn't change size when you update it.

14.  Wrap translatable text and exceptions with Lang() to aid future multi-language support.
