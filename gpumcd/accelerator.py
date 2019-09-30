from .settings import Settings

class Accelerator():
	def __init__(self,sett,typestring,energy):
		## Actually, it would be nicer if we could get this from just the typestring and the number and values of "MODIFIER-NAME" in the machine file. Or map typestring to machine in dosia.ini instead of here
		## TODO instead of parallelJaw, set orientations of jaws here.
		assert(isinstance(sett,Settings))
		assert(isinstance(typestring,str))
		typestring = typestring.upper()
		self.type = None
		self.energy = None #is in controlpoint
		self.filter = None #unknown
		self.leafs_per_bank = None
		self.machfile = None
		self.parallelJaw = True
		if 'MLC160' in typestring or 'M160' in typestring:
			self.type = 'Agility'
			self.energy = energy
			self.filter = True #default
			self.leafs_per_bank = 80
			self.parallelJaw = False # Agility heeft GEEN parallelJaw
			if energy == 6:
				self.machfile = sett.machinefiles['Agility_MV6_FF']
			if energy == 10:
				self.machfile = sett.machinefiles['Agility_MV10_FF']
		elif 'MRL' in typestring:
			self.type = 'MLCi80'
			self.energy = energy
			self.filter = True
			self.leafs_per_bank = 40
			ImportError("MLCi80 found, but no such machine exists in machine library.")
		elif 'MLC80' in typestring or 'M80' in typestring:
			self.type = 'MLCi80'
			self.energy = energy
			self.filter = True
			self.leafs_per_bank = 40
			ImportError("MLCi80 found, but no such machine exists in machine library.")
		else:
			ImportError("Unknown type of TreatmentMachineName found:"+typestring)

		# with open(self.machfile, 'r') as myfile:
		# 	self.machfile = myfile.read()
		# print(self.machfile)

	def __str__(self):
		return f"Accelerator is of type {self.type} with energy {self.energy}MV."
