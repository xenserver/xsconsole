# (c) 2007-2009 Citrix Systems Inc.
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

if __name__ == "__main__":
	raise Exception("This script is a plugin for xsconsole and cannot run independently")
	
from XSConsoleStandard import *

pool_conf = '/etc/xensource/pool.conf'
interface_reconfigure = '/opt/xensource/libexec/interface-reconfigure'
inventory_file = '/etc/xensource-inventory'
network_reset = '/tmp/network-reset'

# read inventory file
def read_inventory():
	f = open(inventory_file, 'r')
	inventory = {}
	for l in f.readlines():
		kv = l.split('=')
		inventory[kv[0]] = kv[1][1:-2]
	return inventory
	
def write_inventory(inventory):
	f = open(inventory_file, 'w')
	for k in inventory:
		f.write(k + "='" + inventory[k] + "'\n")
	f.close()

def biosdevname(d):
	try:
		p = popen('biosdevname -i ' + d)
		return p.read()
	except:
		return d
		
class NetworkResetDialogue(Dialogue):
	def __init__(self):
		Dialogue.__init__(self)
		data = Data.Inst()
		data.Update() # Pick up current 'connected' states
		choiceDefs = []

		self.mac = None
		self.dev2mac = {}
			
		# Determine pool role
		self.master_ip = None
		try:
			f = open(pool_conf, 'r')
			l = f.readline()
			ls = l.split(':')
			if ls[0] == 'slave':
				self.master_ip = ls[1]
		finally:
			f.close()
		
		# Find existing network interfaces (MACs)
		sysfs = '/sys/class/net/'
		currentPIF = None
		# iterate over all devices
		for d in os.listdir(sysfs):
			# only continue if it is a physical device
			if os.access(sysfs + d + '/device', os.F_OK):
				# try to get the MAC
				m = None
				try:
					f = open(sysfs + d + '/address', 'r')
					m = f.readline()[:-1].lower()
					if m != 'fe:ff:ff:ff:ff:ff':
						self.dev2mac[biosdevname(d)] = m
				finally:
					f.close()
		self.devices = self.dev2mac.keys()
		self.devices.sort()
		for d in self.devices:
			choiceDefs.append(ChoiceDef(self.dev2mac[d] + ' (' + d + ')', lambda: self.HandleNICChoice(self.nicMenu.ChoiceIndex())))
					
		if len(choiceDefs) == 0:
			XSLog('Configure Management Interface found no PIFs to present')
			choiceDefs.append(ChoiceDef(Lang("<No interfaces present>"), None))

		self.nicMenu = Menu(self, None, "Configure Management Interface", choiceDefs)
		
		self.modeMenu = Menu(self, None, Lang("Select IP Address Configuration Mode"), [
			ChoiceDef(Lang("DHCP"), lambda: self.HandleModeChoice('DHCP') ),
			ChoiceDef(Lang("Static"), lambda: self.HandleModeChoice('STATIC') )
			])
		
		# Get best guess of current values
		self.mode = 'DHCP'
		self.IP = '0.0.0.0'
		self.netmask = '0.0.0.0'
		self.gateway = '0.0.0.0'
		self.dns = '0.0.0.0'
		
		self.ChangeState('INITIAL')
				
	def BuildPane(self):
		pane = self.NewPane(DialoguePane(self.parent))
		pane.TitleSet(Lang("Emergency Network Reset"))
		pane.AddBox()
		
	def UpdateFieldsINITIAL(self):
		pane = self.Pane()
		pane.ResetFields()
		
		pane.AddTitleField(Lang("Select NIC for Management Interface"))
		pane.AddMenuField(self.nicMenu)
		pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

	def UpdateFieldsMODE(self):
		pane = self.Pane()
		pane.ResetFields()
		
		pane.AddTitleField(Lang("Select DHCP or static IP address configuration"))
		pane.AddMenuField(self.modeMenu)
		pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )

	def UpdateFieldsMASTERIP(self):
		pane = self.Pane()
		pane.ResetFields()
		pane.AddTitleField(Lang("Specify Pool Master's IP Address"))
		pane.AddWrappedTextField(Lang("The host is a pool slave."))
		pane.AddWrappedTextField(Lang("Please confirm or correct the IP address of the pool master."))
		pane.NewLine()				
		pane.AddInputField(Lang("IP Address",  14),  self.master_ip, 'master_ip')		
		pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
		if pane.CurrentInput() is None:
			pane.InputIndexSet(0)
				
	def UpdateFieldsSTATICIP(self):
		pane = self.Pane()
		pane.ResetFields()
		pane.AddTitleField(Lang("Enter static IP address configuration"))
		pane.AddInputField(Lang("IP Address",  14),  self.IP, 'IP')
		pane.AddInputField(Lang("Netmask",  14),  self.netmask, 'netmask')
		pane.AddInputField(Lang("Gateway",  14),  self.gateway, 'gateway')
		pane.AddInputField(Lang("DNS Server",  14),  self.dns, 'dns')
		pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
		if pane.InputIndex() is None:
			pane.InputIndexSet(0) # Activate first field for input
					
	def UpdateFieldsPRECOMMIT(self):
		pane = self.Pane()
		pane.ResetFields()
		
		pane.AddTitleField(Lang("Press <Enter> to reset the network configuration"))
		pane.AddWrappedTextField(Lang("This will cause the host to reboot."))
		
		pane.AddWrappedTextField(Lang("The management interface will be configured as follows:"))
		pane.NewLine()
		
		pane.AddStatusField(Lang("NIC",  16),  self.mac + ' (' + self.device + ')')
		pane.AddStatusField(Lang("IP Mode",  16),  self.mode)
		if self.mode == 'static':
			pane.AddStatusField(Lang("IP Address",  16),  self.IP)
			pane.AddStatusField(Lang("Netmask",  16),  self.netmask)
			pane.AddStatusField(Lang("Gateway",  16),  self.gateway)
			pane.AddStatusField(Lang("DNS Server",  16),  self.dns)
								
		pane.AddKeyHelpField( { Lang("<Enter>") : Lang("OK"), Lang("<Esc>") : Lang("Cancel") } )
					
	def UpdateFields(self):
		self.Pane().ResetPosition()
		getattr(self, 'UpdateFields'+self.state)() # Despatch method named 'UpdateFields'+self.state
	
	def ChangeState(self, inState):
		self.state = inState
		self.BuildPane()
		self.UpdateFields()
							
	def HandleKeyINITIAL(self, inKey):
		return self.nicMenu.HandleKey(inKey)

	def HandleKeyMODE(self, inKey):
		return self.modeMenu.HandleKey(inKey)

	def HandleKeyMASTERIP(self, inKey):
		handled = True
		pane = self.Pane()
		if pane.CurrentInput() is None:
			pane.InputIndexSet(0)
		if inKey == 'KEY_ENTER':
			inputValues = pane.GetFieldValues()
			self.master_ip = inputValues['master_ip']
			try:
				failedName = Lang('Master IP')
				IPUtils.AssertValidIP(self.master_ip)
				self.ChangeState('PRECOMMIT')
			except:
				pane.InputIndexSet(None)
				Layout.Inst().PushDialogue(InfoDialogue(Lang('Invalid ')+failedName))
		elif pane.CurrentInput().HandleKey(inKey):
			pass # Leave handled as True
		else:
			handled = False
		return handled
		
	def HandleKeySTATICIP(self, inKey):
		handled = True
		pane = self.Pane()
		if inKey == 'KEY_ENTER':
			if pane.IsLastInput():
				inputValues = pane.GetFieldValues()
				self.IP = inputValues['IP']
				self.netmask = inputValues['netmask']
				self.gateway = inputValues['gateway']
				self.dns = inputValues['dns']
				try:
					failedName = Lang('IP Address')
					IPUtils.AssertValidIP(self.IP)
					failedName = Lang('Netmask')
					IPUtils.AssertValidNetmask(self.netmask)
					failedName = Lang('Gateway')
					IPUtils.AssertValidIP(self.gateway)
					failedName = Lang('DNS Server')
					IPUtils.AssertValidIP(self.dns)
					self.ChangeState('PRECOMMIT')
				except:
					pane.InputIndexSet(None)
					Layout.Inst().PushDialogue(InfoDialogue(Lang('Invalid ')+failedName))
			else:
				pane.ActivateNextInput()
		elif inKey == 'KEY_TAB':
			pane.ActivateNextInput()
		elif inKey == 'KEY_BTAB':
			pane.ActivatePreviousInput()
		elif pane.CurrentInput().HandleKey(inKey):
			pass # Leave handled as True
		else:
			handled = False
		return handled

	def HandleKeyPRECOMMIT(self, inKey):
		handled = True
		pane = self.Pane()
		if inKey == 'KEY_ENTER':
			self.Commit()
			
			# Reboot
			Layout.Inst().ExitBannerSet(Lang("Rebooting..."))
			Layout.Inst().ExitCommandSet('/sbin/shutdown -r now')
			XSLog('Initiating reboot')
		else:
			handled = False
		return handled
		
	def HandleKey(self,  inKey):
		handled = False
		if hasattr(self, 'HandleKey'+self.state):
			handled = getattr(self, 'HandleKey'+self.state)(inKey)
		
		if not handled and inKey == 'KEY_ESCAPE':
			Layout.Inst().PopDialogue()
			handled = True

		return handled
			
	def HandleNICChoice(self,  inChoice):
		if inChoice is None:
			self.mac = None
			self.ChangeState('PRECOMMIT')
		else:
			self.device = self.devices[inChoice]
			self.mac = self.dev2mac[self.device]
			self.ChangeState('MODE')
		
	def HandleModeChoice(self,  inChoice):
		if inChoice == 'DHCP':
			self.mode = 'dhcp'
			if self.master_ip == None:
				self.ChangeState('PRECOMMIT')
			else:
				self.ChangeState('MASTERIP')
		else:
			self.mode = 'static'
			self.ChangeState('STATICIP')
			
	def Commit(self):
		# Update master's IP, if needed and given
		if self.master_ip != None:
			try:
				f = open(pool_conf, 'w')
				f.write('slave:' + self.master_ip)
			finally:
				f.close()
		
		# Construct bridge name for management interface based on convention
		if self.device[:3] == 'eth':
			bridge = 'xenbr' + self.device[3:]
		else:
			bridge = 'br' + self.device

		# Ensure xapi is not running
		os.system('service xapi stop >/dev/null 2>/dev/null')

		# Reconfigure new management interface
		if_args = ' --force ' + bridge + ' rewrite --mac=' + self.mac + ' --device=' + self.device + ' --mode=' + self.mode
		if self.mode == 'static':
			if_args += ' --ip=' + self.IP + ' --netmask=' + self.netmask
			if self.gateway != '':
				if_args += ' --gateway=' + self.gateway
		os.system(interface_reconfigure + if_args + ' >/dev/null 2>/dev/null')

		# Update interfaces in inventory file
		inventory = read_inventory()
		inventory['MANAGEMENT_INTERFACE'] = bridge
		inventory['CURRENT_INTERFACES'] = ''
		write_inventory(inventory)

		# Write trigger file for XAPI to continue the network reset on startup
		try:
			f = file(network_reset, 'w')
			f.write('mac\t' + self.mac + '\n')
			f.write('device\t' + self.device + '\n')
			f.write('mode\t' + self.mode + '\n')
			if self.mode == 'static':
				f.write('ip\t' + self.IP + '\n')
				f.write('netmask\t' + self.netmask + '\n')
				if self.gateway != '':
					f.write('gateway\t' + self.gateway + '\n')
				if self.dns != '':
					f.write('dns\t' + self.dns + '\n')
		finally:
			f.close()

		# Reset the domain 0 network interface naming configuration
		# back to a fresh-install state for the currently-installed
		# hardware.
		os.system("/etc/sysconfig/network-scripts/interface-rename.py --reset-to-install")

class XSFeatureNetworkReset:
	@classmethod
	def StatusUpdateHandler(cls, inPane):
		data = Data.Inst()
		
		inPane.AddTitleField(Lang("Emergency Network Reset"))
		inPane.AddWrappedTextField("This option will reset the configuration of this host's network interfaces. This will cause the host to reboot.")
				
		inPane.AddKeyHelpField( {
			Lang("<Enter>") : Lang("Reset Networking")
		} )
	
	@classmethod
	def ActivateHandler(cls):
		DialogueUtils.AuthenticatedOnly(lambda: Layout.Inst().PushDialogue(NetworkResetDialogue()))
		
	def Register(self):
		Importer.RegisterNamedPlugIn(
			self,
			'EMERGENCY_NETWORK_RESET', # Key of this plugin for replacement, etc.
			{
				'menuname' : 'MENU_NETWORK',
				'menupriority' : 800,
				'menutext' : Lang('Emergency Network Reset') ,
				'needsauth' : False,
				'statusupdatehandler' : XSFeatureNetworkReset.StatusUpdateHandler,
				'activatehandler' : XSFeatureNetworkReset.ActivateHandler
			}
		)

# Register this plugin when module is imported
XSFeatureNetworkReset().Register()
