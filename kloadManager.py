# kload Manager
# Version 1.0.3
# by Juce.
#
# simple GUI-tool for editing kload.cfg file

import wx
import string, math, re
import sys, os, cStringIO

VERSION, DATE = "1.0.3", "01/2007"
DEFAULT_LOGO_PNG = os.getcwd() + "/logo.png"
CONFIG_FILE = os.getcwd() + "/klm.cfg"
WINDOW_TITLE = "kload.cfg & Options File Manager"
FRAME_WIDTH = 380
FRAME_HEIGHT = 520

####################################################

def getDLLinfo(cwd, kitserverBase):
    dlls, desc = [], []
    infoFile = open("%s/dllinfo.txt" % cwd)
    for line in infoFile:
        try: 
            tok = line.strip().split('-',2)
            if len(tok)==2 and os.path.exists(kitserverBase + "/" + tok[0].strip()):
                dlls.append(tok[0].strip())
                desc.append(tok[1].strip())
        except:
            pass
    infoFile.close()
    return dlls, desc

"""
Utility method for showing message box window
"""
def MessageBox(owner, title, text):
    dlg = wx.MessageDialog(owner, text, title, wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()


"""
A text field choice with label
"""
class MyTextField(wx.Panel):
    def __init__(self, parent, optionMap, option, labelText, frame):
        wx.Panel.__init__(self, parent, -1)
        self.frame = frame
        self.optionMap = optionMap
        self.option = option
        self.label = wx.StaticText(self, -1, labelText, size=(240,-1), style=wx.ALIGN_RIGHT)
        self.label.SetBackgroundColour(wx.Colour(230,230,230))
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.label.SetFont(font)
        self.label.SetSize(self.label.GetBestSize())

        self.text = wx.TextCtrl(self, -1, "", size=(110,-1))

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.sizer.Add(self.text, 0, wx.EXPAND)

        # bind events
        self.text.Bind(wx.EVT_TEXT, self.OnTextChange)

        self.SetSizer(self.sizer)
        self.SetStringSelection(optionMap.get(option,""))
        self.Layout()

    def SetStringSelection(self, str):
        if self.optionMap != None:
            self.text.SetValue(str)
            self.optionMap[self.option] = str

    def OnTextChange(self, event):
        if self.optionMap != None:
            oldVal = self.optionMap.get(self.option,"")
            newVal = self.text.GetValue()
            if newVal != oldVal:
                #print "Description modified: old={%s}, new={%s}" % (oldVal,newVal)
                self.optionMap[self.option] = newVal
                self.frame.modified = True
                self.frame.SetStatusText("Configuration modified: YES");


"""
A checkbox with label
"""
class MyCheckBox(wx.Panel):
    def __init__(self, parent, optionMap, option, labelText, dll, checked, frame):
        wx.Panel.__init__(self, parent, -1)
        self.frame = frame
        self.optionMap = optionMap
        self.option = option
        self.checked = checked
        self.dll = dll
        self.label = wx.StaticText(self, -1, labelText, size=(240,-1), style=wx.ALIGN_RIGHT)
        self.label.SetBackgroundColour(wx.Colour(230,230,230))
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.label.SetFont(font)
        self.label.SetSize(self.label.GetBestSize())

        self.check = wx.CheckBox(self, -1, dll, size=(110,-1))
        self.check.SetValue(checked)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.sizer.Add(self.check, 0, wx.EXPAND)

        # bind events
        self.check.Bind(wx.EVT_CHECKBOX, self.OnCheck)

        self.SetSizer(self.sizer)
        #self.SetStringSelection(optionMap.get(option,""))
        self.Layout()

    def OnCheck(self, event):
        self.checked = event.IsChecked()
        self.frame.modified = True
        self.frame.SetStatusText("Configuration modified: YES");


"""
A file choice with label
"""
class gdbDirPanel(wx.Panel):
    def __init__(self, parent, optionMap, option, labelText, frame):
        wx.Panel.__init__(self, parent, -1)
        self.gdbPath = optionMap.get(option,".") + "GDB"
        self.optionMap = optionMap
        self.option = option
        self.frame = frame
        self.label = wx.StaticText(self, -1, labelText, size=(300,-1), style=wx.ALIGN_LEFT)
        self.label.SetBackgroundColour(wx.Colour(230,230,230))
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.label.SetFont(font)
        self.label.SetSize(self.label.GetBestSize())

        self.logoPanel = LogoPanel(self, self)
        self.text = wx.TextCtrl(self, -1, self.gdbPath, size=(260,-1))
        self.dirButton = wx.Button(self, -1, "...", size=(30,1))

        horSizer = wx.BoxSizer(wx.HORIZONTAL)
        horSizer.Add(self.text, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        horSizer.Add(self.dirButton, 0, wx.EXPAND)

        vertSizer = wx.BoxSizer(wx.VERTICAL)
        vertSizer.Add(self.label, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=0)
        vertSizer.Add(horSizer, 0, wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.logoPanel, 0, wx.ALIGN_CENTER_VERTICAL)
        self.sizer.Add(vertSizer, 0, wx.LEFT | wx.EXPAND, border=10)

        # by default the kit panel is not refreshed on selection change
        self.refreshOnChange = False

        # bind events
        self.dirButton.Bind(wx.EVT_BUTTON, self.OnChooseDir)
        #self.text.Bind(wx.EVT_KILL_FOCUS, self.OnChange)
        self.text.Bind(wx.EVT_TEXT, self.OnChange)
        self.SetSizer(self.sizer)
        self.Layout()

    def OnChange(self, event):
        if self.optionMap != None:
            oldVal = self.optionMap.get(self.option,"")
            newVal = self.text.GetValue()
            if newVal != oldVal:
                #print "Description modified: old={%s}, new={%s}" % (oldVal,newVal)
                self.gdbPath = newVal
                self.frame.modified = True
                self.frame.SetStatusText("Configuration modified: YES");
                self.optionMap[self.option] = self.getDir()
                self.Refresh()

    def OnChooseDir(self, event):
        dlg = wx.DirDialog(self, """Select your GDB folder:
(Folder named "GDB", which is typically located
inside your kitserver folder)""",
                style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            print "You selected %s" % dlg.GetPath()
            if os.path.split(dlg.GetPath())[1].upper()=="GDB":
                self.gdbPath = dlg.GetPath()
                self.text.SetValue(self.gdbPath)
                self.frame.modified = True
                self.frame.SetStatusText("Configuration modified: YES");
                self.optionMap[self.option] = self.getDir()
                self.Refresh()
            else:
                MessageBox(self, "Bad GDB folder", """Your have selected an incorrect GDB folder. 
The folder MUST be named 'GDB'. 
Please try a different folder.""")

    def getDir(self):
        value = self.text.GetValue()
        if len(value.strip())==0:
            return ".\\"
        else:
            return os.path.dirname(value) + "\\"

    def getAbsoluteGdbPath(self):
        try: 
            if self.gdbPath[0]=='.' or self.gdbPath[0:2]=='..':
                return self.frame.kitserverPath + "\\" + self.gdbPath
            return self.gdbPath
        except:
            pass
        return ""


class LogoPanel(wx.Panel):
    def __init__(self, parent, ownerPanel=None):
        wx.Panel.__init__(self, parent, -1, size=(48, 48))
        self.SetBackgroundColour(wx.Color(180,180,200))
        self.ownerPanel = ownerPanel

        # bind events
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)

        # disable warning pop-ups
        wx.Log.EnableLogging(False)

        # draw logo
        if self.ownerPanel == None \
                or self.ownerPanel.getAbsoluteGdbPath() == None \
                or not os.path.exists(self.ownerPanel.getAbsoluteGdbPath() + "/logo.png"):
            bmp = wx.Bitmap(DEFAULT_LOGO_PNG)
        else:
            bmp = wx.Bitmap(self.ownerPanel.getAbsoluteGdbPath() + "/logo.png")
        width,height = bmp.GetSize()
        if width != 48 or height != 48:
            try: bmp = bmp.ConvertToImage().Scale(48,48).ConvertToBitmap()
            except: pass
        dc.DrawBitmap(bmp, 0, 0, True)
        return event.Skip()


class MyOptionsFileList(wx.Panel):
    """
    A drop-down list with label of options-files
    """
    def __init__(self, parent, optionsFileDir, labelText, frame):
        wx.Panel.__init__(self, parent, -1)
        self.frame = frame
        self.optionsFileDir = optionsFileDir
        self.label = wx.StaticText(self, -1, labelText, size=(100,-1), style=wx.ALIGN_RIGHT)
        self.label.SetBackgroundColour(wx.Colour(230,230,230))
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.label.SetFont(font)
        self.label.SetSize(self.label.GetBestSize())

        self.items = self.getOptionsFiles(self.optionsFileDir)
        self.choice = wx.Choice(self, -1, choices=[str(i) for i in self.items], size=(200,-1))

        # set current selection
        try: self.current = open("%s\\.optinfo" % self.optionsFileDir).read().strip()
        except: self.current = self.items[0]
        self.orgChoice = "%s" % self.current
        self.choice.SetStringSelection(self.orgChoice)

        self.dirButton = wx.Button(self, -1, "...", size=(30,1))

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.sizer.Add(self.choice, 0, wx.EXPAND)
        self.sizer.Add(self.dirButton, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, border=10)

        # by default the kit panel is not refreshed on selection change
        self.refreshOnChange = False

        # bind events
        self.choice.Bind(wx.EVT_CHOICE, self.OnSelect)
        self.dirButton.Bind(wx.EVT_BUTTON, self.OnChooseDir)

        self.SetSizer(self.sizer)
        self.Layout()

    def SetStringSelection(self, str=None):
        if str!=None and len(str)>0:
            self.current = str
            print "self.current = %s" % self.current
            if self.isModified():
                self.frame.SetStatusText("Configuration modified: YES");
            elif not self.frame.modified:
                self.frame.SetStatusText("Configuration modified: no");

    def OnSelect(self, event):
        selection = event.GetString()
        index = self.choice.GetSelection()
        self.SetStringSelection(selection)

    def OnChooseDir(self, event):
        dlg = wx.DirDialog(self, """Select your game's "folder1" folder:
(this is where your regular options file should 
be located, as well as all the alternative ones)""",
                style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            print "You selected %s" % dlg.GetPath()
            self.optionsFileDir = dlg.GetPath()
            self.items = self.getOptionsFiles(self.optionsFileDir)
            # repopulate the list
            self.choice.Clear()
            for item in self.items:
                self.choice.Append(item)
            # set current selection
            try: self.current = open("%s\\.optinfo" % self.optionsFileDir).read().strip()
            except: self.current = self.items[0]
            self.orgChoice = "%s" % self.current
            self.choice.SetStringSelection(self.orgChoice)

            # save the value in configuration file
            self.frame.optionsFileDir = self.optionsFileDir
            self.frame.saveConfig()

    def getOptionsFiles(self, dir):
        files = ["<default>"]
        if dir=="": return files
        try:
            optfiles = [v for v in os.listdir(dir) if len(v)>4 and v[-4:].lower()==".opt"]
            files = files + optfiles
        except:
            pass
        return files

    def isModified(self):
        return self.current != self.orgChoice


class MyFrame(wx.Frame):
    """
    Main window class
    """
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(FRAME_WIDTH, FRAME_HEIGHT))
        self.modified = False
        self.SetBackgroundColour(wx.Colour(192,192,192))
        self.cwd = os.getcwd()
        self.optionsFileDir = "%s\\My Documents\\KONAMI\\Pro Evolution Soccer 6\\save\\folder1" % os.environ.get("USERPROFILE")
        try:
            self.loadConfig()
        except: 
            # trigger kload selection
            self.OnSetKloadCfg(None)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        # status bar
        self.CreateStatusBar()

        self.initControls()

    def initControls(self):
        self.modified = False
        self.SetStatusText("Configuration modified: no")

        # determine where to look for kload.cfg
        try: 
            self.loadConfig()
        except: 
            MessageBox(self, "No kload.cfg", """You haven't selected the kload.cfg.
Without it, this program cannot continue.
Please restart it and select kload.cfg.""")
            self.OnExit(None)

        # read kload.cfg
        self.optionMap = self.readKloadCfg()

        # determine valid DLL names
        self.validDlls, self.dllDesc = getDLLinfo(self.cwd, self.kitserverPath)
        print "valid DLLs: %s" % self.validDlls

        # Create widgets
        ##################
        self.gdbDirPanel = gdbDirPanel(self, self.optionMap, "gdb.dir", "Location of GDB folder (gdb.dir)",self)
        self.reservedMemory = MyTextField(self, self.optionMap, "ReservedMemory", "Reserved Memory: ",self) 
        self.debug = MyTextField(self, self.optionMap, "debug", "debug (0=off,1,2): ",self) 

        self.dlls = []
        for i,dll in zip(range(len(self.validDlls)), self.validDlls):
            checked = self.isEnabled(self.optionMap,dll)
            self.dlls.append(MyCheckBox(self, self.optionMap, "DLL.%d" % i, \
                    self.dllDesc[i], dll, checked, self))
            if dll == "zlib1.dll" or dll == "libpng13.dll":
                self.dlls[-1].Enable(False)
            print "%s: %s" % (dll, checked)

        self.dxForceSWTnL = MyCheckBox(self, self.optionMap, "dx.force-SW-TnL", \
                "Force software TnL", "SW TnL", self.optionMap.get("dx.force-SW-TnL","0")=="1", self)
        self.dxEmulateHWTnL = MyCheckBox(self, self.optionMap, "dx.emulate-HW-TnL", \
                "Emulate hardware TnL", "HW TnL", self.optionMap.get("dx.emulate-HW-TnL","0")=="1", self)
        self.dxFullscreenWidth = MyTextField(self, self.optionMap, "dx.fullscreen.width", \
                "Fullscreen Width: ",self) 
        self.dxFullscreenHeight = MyTextField(self, self.optionMap, "dx.fullscreen.height", \
                "Fullscreen Height: ",self) 

        self.optionsFileList = MyOptionsFileList(self, self.optionsFileDir, "Options File",self)

        # menu
        menubar = wx.MenuBar()

        menu1 = wx.Menu()
        menu1.Append(101, "Which &kload.cfg", 
            "Show path to current kload.cfg file")
        menu1.Append(102, "&Change kload.cfg", 
            "Navigate to and load kload.cfg file")
        menu1.Append(103, "&Save changes", "Save the changes to kload.cfg")
        menu1.AppendSeparator()
        menu1.Append(104, "E&xit", "Exit the program")
        menubar.Append(menu1, "&File")

        menu3 = wx.Menu()
        menu3.Append(301, "&About", "Author and version information")
        menubar.Append(menu3, "&Help")

        self.SetMenuBar(menubar)

        # Create sizers
        #################

        # Build interface by adding widgets to sizers
        ################################################

        self.sizer.Add(self.gdbDirPanel, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=10)
        self.sizer.Add(self.reservedMemory, 0, wx.ALIGN_CENTER, border=10)
        self.sizer.Add(self.debug, 0, wx.BOTTOM | wx.ALIGN_CENTER, border=10)
        for checkbox in self.dlls:
            self.sizer.Add(checkbox, 0, wx.ALIGN_CENTER, border=10)
        self.sizer.Add(self.dxFullscreenWidth, 0, wx.TOP | wx.ALIGN_CENTER, border=10)
        self.sizer.Add(self.dxFullscreenHeight, 0, wx.BOTTOM | wx.ALIGN_CENTER, border=10)
        self.sizer.Add(self.dxForceSWTnL, 0, wx.TOP | wx.ALIGN_CENTER, border=10)
        self.sizer.Add(self.dxEmulateHWTnL, 0, wx.BOTTOM | wx.ALIGN_CENTER, border=10)
        self.sizer.Add(self.optionsFileList, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=10)

        #self.Layout()
        w,h = self.sizer.GetMinSize()
        self.SetClientSize((w+10,h))

        # Bind events
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        self.Bind(wx.EVT_MENU, self.OnShowKloadCfgPath, id=101)
        self.Bind(wx.EVT_MENU, self.OnSetKloadCfg, id=102)
        self.Bind(wx.EVT_MENU, self.OnMenuSave, id=103)
        self.Bind(wx.EVT_MENU, self.OnExit, id=104)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=301)

    def resetControls(self):
        self.sizer.DeleteWindows()
        self.initControls()
        self.sizer.Layout()
        self.Refresh()

    def isEnabled(self, map, dllname):
        for key in map.keys():
            if dllname == map[key].split('\\')[-1].strip():
                return True
        return False

    def OnMenuSave(self, event):
        if self.saveChanges():
            self.modified = False
            self.SetStatusText("Configuration modified: no");
            print "Changes saved."

    def OnShowKloadCfgPath(self, event):
        MessageBox(self, "Information", """You are currently working with:
%s""" % self.kloadCfgPath)

    def OnSetKloadCfg(self, event):
        dlg = wx.FileDialog(self, """Navigate to your kload.cfg file and select it.""",
                defaultDir=os.getcwd(),
                style=wx.DD_DEFAULT_STYLE)
        dlg.SetWildcard("kload.cfg files|kload.cfg");

        if dlg.ShowModal() == wx.ID_OK:
            self.modified = False # reset modified flag
            self.kloadCfgPath = dlg.GetPath()
            print "You selected %s" % self.kloadCfgPath

            # save the value in configuration file
            self.saveConfig()

            # re-initialize the UI
            if event!=None: 
                self.resetControls()

        else:
            print "Selection cancelled."

        # destroy the dialog after we're done
        dlg.Destroy()

    def OnAbout(self, event):
        dlg = wx.MessageDialog(self, """kload.cfg & Options File Manager.
Version %s from %s
Programmed by: Juce

This is a helper program to visually
edit "kload.cfg" file, which contains
the master configuration of kitserver.

Also, it allows to easily switch
between different versions of
options file.""" % (VERSION, DATE),
            "About the program", wx.OK | wx.ICON_INFORMATION)

        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self, evt):
        print "MyFrame.OnExit"

        # do necessary clean-up and saves
        if self.cancelledOnSaveChanges():
            return

        # Exit the program
        self.Destroy()
        sys.exit(0)

    def loadConfig(self):
        klm = open(CONFIG_FILE)
        lineCount = 0
        for line in klm:
            if lineCount == 0:
                self.kloadCfgPath = line.strip()
                self.kitserverPath = os.path.dirname(self.kloadCfgPath)
            elif lineCount == 1:
                self.optionsFileDir = line.strip()
            lineCount += 1
        klm.close()

    def saveConfig(self):
        print "Saving configuration into klm.cfg..."
        try:
            cfg = open(CONFIG_FILE, "wt")
            print >>cfg, self.kloadCfgPath
            print >>cfg, self.optionsFileDir
            print "self.kloadCfgPath = {%s}" % self.kloadCfgPath
            print "self.optionsFileDir = {%s}" % self.optionsFileDir
            cfg.close()
        except IOError:
            # unable to save configuration file
            print "Unable to save configuration file"


    """
    Shows a warning window, with a choice of saving changes,
    discarding them, or cancelling the operation.
    """
    def cancelledOnSaveChanges(self):
        try:
            if self.modified or self.optionsFileList.isModified():
                # figure out what to do with changes: Save or Discard
                dlg = wx.MessageDialog(self, """You haven't saved your changes.
Do you want to save them?""",
                        "Save or Discard changes",
                        wx.YES_NO | wx.CANCEL | wx.ICON_INFORMATION)
                retValue = dlg.ShowModal()
                dlg.Destroy()

                if retValue == wx.ID_YES:
                    # save the changes first
                    self.saveChanges(False)
                    pass
                elif retValue == wx.ID_CANCEL:
                    # cancel the operation
                    return True
        except AttributeError:
            pass
        return False

    """
    Saves the changes
    """
    def saveChanges(self, showConfirmation=True):
        success = False
        print "Saving changes..."

        if self.modified:
            # create new file
            try:
                cfg = open(self.kloadCfgPath, "wt")
            except IOError:
                MessageBox(self, "Unable to save changes", "ERROR: cannot open file %s for writing." % cfg)
                return

            try:
                # write a comment line, if not already there
                cmt = "# kload.cfg configuration file auto-generated by kload Manager"
                print >>cfg, cmt
                print >>cfg
                self.writeKloadCfg(cfg)
                success = True

            except Exception, e:
                MessageBox(self, "Unable to save changes", "ERROR during save: %s" % str(e))

            cfg.close()

        # switch options file if needed
        if self.optionsFileList.isModified():
            print "Switching options file..."
            try:
                # check for existence
                wd = self.optionsFileList.optionsFileDir
                hasDefaultCopy = os.path.exists("%s\\.default.copy" % wd)
                hasInfo = os.path.exists("%s\\.optinfo" % wd)
                # determine standard options file name
                standardopts = [v for v in os.listdir(wd) 
                        if v.startswith("KONAMI-WIN32") and v.endswith("OPT")]
                if len(standardopts)>0: standardopt = standardopts[0]
                else: standardopt = "DUMMY"
                if not hasInfo and not hasDefaultCopy:
                    # make a copy of default options file
                    outf = open("%s\\.default.copy" % wd,"wb")
                    inf = open("%s\\%s" % (wd,standardopt),"rb")
                    outf.write(inf.read())
                    inf.close()
                    outf.close()
                # copy options file
                current = self.optionsFileList.current
                if current=="<default>" : current = ".default.copy"
                inf = open("%s\\%s" % (wd,current), "rb")
                outf = open("%s\\%s" % (wd,standardopt),"wb")
                outf.write(inf.read())
                inf.close()
                outf.close()
                # update .optinfo
                outf = open("%s\\.optinfo" % wd,"wt")
                print >>outf, self.optionsFileList.current
                outf.close()

                self.optionsFileList.orgChoice = self.optionsFileList.current
                self.optionsFileList.SetStringSelection(self.optionsFileList.current)
                print "Options file switched."
            except Exception, e1:
                MessageBox(self, "Unable to switch options file", "ERROR during switch: %s" % str(e1))

        # show save confirmation message, if asked so.
        if showConfirmation:
            MessageBox(self, "Changes saved", "Your changes were successfully saved.")

        return success

    def readKloadCfg(self):
        """
        Read configuration
        """
        map = {}
        try: cfg = open(self.kloadCfgPath,"rt")
        except IOError:
            return map
        except OSError:
            return map

        for line in cfg:
            # strip off the comments
            commStart = line.find('#')
            if commStart!=-1: line = line[:commStart]

            tok = line.strip().split('=',2)
            if len(tok)==2:
                val = tok[1].strip()
                if val[0]=='"' and val[-1]=='"': val = val[1:-1]
                map[tok[0].strip()] = val

        cfg.close()
        #print map
        return map

    def writeKloadCfg(self,cfg):
        # debug
        debug = self.optionMap.get("debug","")
        if len(debug)>0:
            try: print >>cfg, "debug = %d" % int(debug)
            except: pass
        # gdbDir
        gdbDir = self.optionMap.get("gdb.dir","")
        if len(gdbDir)>0:
            print >>cfg, "gdb.dir = \"%s\"" % gdbDir
        # ReservedMemory
        reservedMemory = self.optionMap.get("ReservedMemory","")
        if len(reservedMemory)>0:
            try: print >>cfg, "ReservedMemory = %d" % int(reservedMemory)
            except: pass
        # DLLs
        print >>cfg
        print >>cfg, "DLL.num = %d" % len(self.dlls)
        kitserverShortPath = os.path.split(self.kitserverPath)[1]
        for dll in self.dlls:
            if dll.checked:
                print >>cfg, "%s = \"%s\\%s\"" % (dll.option, kitserverShortPath, dll.dll)
            else:
                print >>cfg, "#%s = \"%s\\%s\"" % (dll.option, kitserverShortPath, dll.dll)
        # dx-tools
        print >>cfg
        print >>cfg, "dx.force-SW-TnL = %d" % int(self.dxForceSWTnL.checked)
        print >>cfg, "dx.emulate-HW-TnL = %d" % int(self.dxEmulateHWTnL.checked)
        fwidth = self.optionMap.get("dx.fullscreen.width","")
        fheight = self.optionMap.get("dx.fullscreen.height","")
        if len(fwidth)==0 or len(fheight)==0:
            print >>cfg, "#dx.fullscreen.width = 1920"
            print >>cfg, "#dx.fullscreen.height = 1200"
        else:
            try:
                fw,fh = int(fwidth),int(fheight)
                print >>cfg, "dx.fullscreen.width = %d" % int(fwidth)
                print >>cfg, "dx.fullscreen.height = %d" % int(fheight)
            except:
                print >>cfg, "#dx.fullscreen.width = 640"
                print >>cfg, "#dx.fullscreen.height = 480"


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, WINDOW_TITLE)
        frame.Show(1)
        self.SetTopWindow(frame)
        return True


if __name__ == "__main__":
    #app = MyApp(redirect=True, filename="output.log")
    #app = MyApp(redirect=True)
    app = MyApp(0)
    app.MainLoop()

