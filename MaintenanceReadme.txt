There are a few gotchas in the xsconsole code.  This is a list of a few of them.

1.  All of the XSConsolexxxx.py files are in the same namespace (as they're imported using 'from <file> import *').  When adding functions try to keep them within objects to prevent clashes.

2.  The app evelved a number of ways to execute shell commands.  For new code ShellPipe in XSConsoleUtils.py is the preferred option.

3.  New features (e.g. menu items) should be implemented as plugins.  The app moved to plugins fairly late on, so older features are in XSConsoleDialogues.py, with their status panes in XSConsoleRootDialogue.py, but this is deprecated.

4.  The field layout code in in FieldArranger is a bit hairy as it interacts with the automatic pane sizer PaneSizerCentre.  The code attempts to:

  (i)   Determine the size of the dialogue required by looking at the fields within it
  (ii)  Set the window to that size
  (iii) Arrange the fields again using that window size

Occasionally this gives a pane height one line to short, probably because the reflowed text in (i) is slightly different to that in (iii).

5.  If you display a dialogue with input fields, display another box (e.g. InfoDialogue) in front of it, and go back to the first dialogue, you'll probably lose the cursor.  ChangePasswordDialogue shows one way around this.

6.  UpdateFields generally recreates fields from scratch, so you can't just call it whenever you like because, e.g. values in text entry fields will be lost and cursors reset.  It's fine to update the root dialogue though.

7.  When building menus from a list of menu choices from an array it would sometimes be nice to do this

for i in range(len(choiceArray)):
    choices.append(ChoiceDef(choiceArray[i].name, lambda : self.HandleChoice(i)))
    
but you can't.  The lambda: self.HandleChoice(i) all refer to the same i so all selections have the same value - the final value of i.  Variations of the same have the same problem.

8.  It's tricky to get the ncurses display to refresh without flicker.  Using the curses erase or clear methods on windows can lead to flickering redraws.  Currently only scrolling in the right hand pane of the root dialogue has this problem.  Since there's not much use of erase or clear the app does pretty minimal redraws, and things like spurious kernel message that scroll the screen can leave it in a mess for some time. 

9.  MountVDI's Create VDB/Plug VBD/Mount VBD/Use VBD/Unmount VBD/Unplug VBD/Destroy VBD sequence failed when trying to mount empty CD drives.  Now only MountVDIDirectly is used.

10.  Circular imports can be a problem in this app.  XSConsoleData.py (or anything it imports) can't import XSConsoleDataUtils.py, for example, and if it does the app throws weird exceptions about missing names that don't make sense.  Similarly for the XSConsoleData.py/XSConsoleAuth.py/XSConsoleState.py trio.

11.  Data.Inst().Update() is a fairly expensive operation as it reloads and reprocesses almost everything.

12.  BannerDialogues shouldn't be left on the dialogue stack when you return to the main loop.  Use TransientBanner instead.  If you want a dialogue box that persists you need an InfoDialogue, which is the same thing with an <Enter> OK help field and a keypress handler.

13.  In OEM builds xsconsole is started from inittab with a pretty minimal enviroment.  There's no PATH set up, and /usr/bin/xsconsole sets USER itself (since scripts like xen-bugtool require it).
