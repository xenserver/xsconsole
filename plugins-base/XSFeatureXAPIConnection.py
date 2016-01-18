# Copyright (c) 2015 Citrix Systems Inc.
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
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

if __name__ == "__main__":
    raise Exception("This script is a plugin for xsconsole and cannot run independently")

from XSConsoleStandard import *

class XSFeatureXAPIConnection:
    @classmethod
    def ReadyHandler(cls):
        def HandleRestartChoice(inChoice):
            if inChoice == 'y':
                try:
                    XSLog('Attempting to restart xapi')
                    Layout.Inst().TransientBanner(Lang("Restarting xapi...."))
                    Data.Inst().StartXAPI()
                    XSLog('Restarted xapi')
                except Exception, e:
                    XSLogFailure('Failed to restart xapi', e)
                    Layout.Inst().PushDialogue(InfoDialogue(Lang('Restart Failed'), Lang('Xapi did not restart successfully.  More information may be available in the file /var/log/xensource.log.')))

        if not Data.Inst().IsXAPIRunning() and State.Inst().RebootMessage() is None:
            XSLog("Displaying 'xapi is not running' dialogue")
            Layout.Inst().PushDialogue(QuestionDialogue(
                Lang("The underlying Xen API xapi is not running.  This console will have reduced functionality.  "
                     "Would you like to attempt to restart xapi?"), lambda x: HandleRestartChoice(x)))

        if Auth.Inst().IsXenAPIConnectionBroken():
            XSLog("Displaying 'XenAPI connection timeout' dialogue")
            Layout.Inst().PushDialogue(InfoDialogue(
                Lang("The XenAPI connection has timed out.  This console will have reduced functionality.  "
                    "If this host is a pool slave, the master might be unreachable.")))

    def Register(self):
        data = Data.Inst()
        appName = data.derived.app_name('')
        fullAppName = data.derived.full_app_name('')
        Importer.RegisterNamedPlugIn(
            self,
            'XAPI_CONNECTION', # Key of this plugin for replacement, etc.
            {
                'readyhandler' : XSFeatureXAPIConnection.ReadyHandler,
                'readyhandlerpriority' : 800,
            }
        )

# Register this plugin when module is imported
XSFeatureXAPIConnection().Register()
