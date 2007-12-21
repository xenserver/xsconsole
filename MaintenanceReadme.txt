There are a few gotchas in the xsconsole code.  This is a list of a few of them.

1.  UpdateFields generally recreates fields from scratch, so you can't just call it whenever you like because, e.g. values in text entry fields will be lost and cursors reset.  It's fine to update the root dialogue though.

2.  When building menus from a list of menu choices from an array it would sometimes be nice to do this

for i in range(len(choiceArray)):
    choices.append(ChoiceDef(choiceArray[i].name, lambda : self.HandleChoice(i)))
    
but you can't.  The lambda: self.HandleChoice(i) all refer to the same i so all selections have the same value - the final value of i.  Variations of the same have the same problem.

3.  There's reasonable separation between the data (XSConsoleData.py) and UI (XSConsole(Root)Dialogues.py) but no separation between the UI and control mechanisms.  The code that causes data changes, mounts and scans devices, etc. is spread amonst the dialogues.

4.  It's tricky to get the ncurses display to refresh without flicker.  Using the curses erase or clear methods on windows can lead to flickering redraws.  Currently only scrolling in the right hand pane of the root dialogue has this problem.  Since there's not much use of erase or clear the app does pretty minimal redraws, and things like spurious kernel message that scroll the screen can leave it in a mess for some time. 

5.  The vertical size limit on menu fields is hard-coded to 10, and that number is also used in some of the dialogues.  Menus with more than 10 entries, where the names of all entires aren't the same length, may have redraw problems because chracters are not overwritten.

6.  The Create VDB/Plug VBD/Mount VBD/Use VBD/Unmount VBD/Unplug VBD/Destroy VBD sequence isn't rock solid if it fails or if you Ctrl-C out or kill the process half way through.  The app attempts to tidy up by deleting dangling VBDs (identified by 'xsconsole_tmp' in their other_config) on startup, otherwise these would build up over time.  VBDs can also fail to unplug immediately after an umount because the kernel is still tidying up after the umount, so the app tries twice.

7.  Whilst operation like mount are done using the virtualised device /dev/xapi/whatever/whatever, fdisk and mkfs uses the device directly /dev/whatever.

8.  Circular imports can be a problem in this app.  XSConsoleData.py (or anything it imports) can't import XSConsoleDataUtils.py, for example, and if it does the app throws weird exceptions about missing names that don't make sense.  Similarly for the XSConsoleData.py/XSConsoleAuth.py/XSConsoleState.py trio.

9.  Data.Inst().Update() is a fairly expensive operation as it reloads and reprocesses almost everything.

10.  BannerDialogues shouldn't be left on the dialogue stack when you return to the main loop.  If they are the app will crash out as the BennerDialogue has no keypress handler.  If you want a dialogue box that persists you need an InfoDialogue, which is the same thing with an <Enter> OK help field and a keypress handler.

11.  In OEM builds xsconsole is started from inittab with a pretty minimal enviroment.  There's no PATH set up, and /usr/bin/xsconsole sets USER itself (since scripts like xen-bugtool require it).
