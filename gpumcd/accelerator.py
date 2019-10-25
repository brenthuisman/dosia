from .settings import Settings
from .gpumcdwrapper import ModifierOrientation
import dicom
from os import path

class Accelerator():
	def __init__(self,rtplan_dicom,sett=None):
		'''
		Given an rtplan (in the form of a pydicom_object), this class extracts a correct Accelerator class that can be used by Dosia. If a valid Settings object is also provided, with valid machine_files present, this class will set the correct machine file inder its `machfile` member.

		Not all important parameters are easily extracted from a machine file (especially vsm machine files), so they are defined here.
		'''
		assert(isinstance(sett,Settings))
		assert(isinstance(rtplan_dicom,dicom.pydicom_object))

		self.type = None
		self.energy = None
		self.fff = None
		self.leafs_per_bank = None
		self.machfile = None
		self.parallelJawOrientation = None
		self.perpendicularJawOrientation = None
		self.mlcOrientation = None
		self.parallelJawName = [] #it is important these are lists!
		self.perpendicularJawName = [] #it is important these are lists!
		self.mlcName = [] #it is important these are lists!

		machinestring = str(rtplan_dicom.data.BeamSequence[0].TreatmentMachineName).upper()
		self.energy = int(rtplan_dicom.data.BeamSequence[0].ControlPointSequence[0].NominalBeamEnergy)
		try:
			if "NON_STANDARD" in rtplan_dicom.data.BeamSequence[0].ControlPointSequence[0].PrimaryFluenceModeSequence[0].FluenceMode and "FFF" in rtplan_dicom.data.BeamSequence[0].ControlPointSequence[0].PrimaryFluenceModeSequence[0].FluenceModeID:
				self.fff = True
			else:
				self.fff = False
		except:
			#usually the above fields wont be present at all if its not FFF
			self.fff = False

		if '160' in machinestring or 'MLC160' in machinestring or 'M160' in machinestring or 'AGILITY' in machinestring:
			self.type = 'Agility'
			self.leafs_per_bank = 80
			self.parallelJawOrientation = ModifierOrientation(-1)
			self.perpendicularJawOrientation = ModifierOrientation(1)
			self.mlcOrientation = ModifierOrientation(0)
			self.parallelJawName = ['X','ASYMX'] #it does not exist, but may be given
			self.perpendicularJawName = ['Y','ASYMY']
			self.mlcName = ['MLCX']
			if sett != None:
				if self.energy == 6 and not self.fff:
					self.machfile = sett.machinefiles['Agility_MV6']
				elif self.energy == 10 and not self.fff:
					self.machfile = sett.machinefiles['Agility_MV10']
				elif self.energy == 6 and self.fff:
					self.machfile = sett.machinefiles['Agility_MV6_FFF']
				elif self.energy == 10 and self.fff:
					self.machfile = sett.machinefiles['Agility_MV10_FFF']
				elif self.energy == 15:
					self.machfile = sett.machinefiles['Agility_MV15']
				else:
					ImportError(f"Agility accelerator found, but unavailable energy {self.energy} encountered.")
		elif 'MRL' in machinestring:
			self.type = 'MRL'
			self.leafs_per_bank = 80
			self.parallelJawOrientation = ModifierOrientation(-1)
			self.perpendicularJawOrientation = ModifierOrientation(0)
			self.mlcOrientation = ModifierOrientation(1)
			self.parallelJawName = ['Y','ASYMY'] #it does not exist, but may be given
			self.perpendicularJawName = ['X','ASYMX']
			self.mlcName = ['MLCY']
			if sett != None:
				if self.energy == 7:
					self.machfile = sett.machinefiles['MRLinac_MV7']
				else:
					ImportError(f"Agility accelerator found, but unavailable energy {self.energy} encountered.")
		elif 'MLC80' in machinestring or 'M80' in machinestring:
			self.type = 'MLCi80'
			self.leafs_per_bank = 40
			ImportError("MLCi80 found, but no such machine exists in machine library.")
		else:
			ImportError(f"Unknown type of TreatmentMachineName found: {machinestring}")

		self.setmaterials()

	def setmaterials(self):
		if path.isfile(self.machfile):
			self.materials = []
			with open(self.machfile, 'r') as myfile:
				self.machfile_contents = myfile.readlines()
				for line in self.machfile_contents:
					try:
						pieces = line.split(":")
						if "MEDIUM-NAME" in pieces[0].strip():
							self.materials.append(pieces[1].strip())
					except:
						pass
			#print(self.materials)
		else:
			print("Invalid machine file provided, can't load materials.")

	def setmachfile(self,fname):
		self.machfile = fname
		self.setmaterials()

	def __str__(self):
		return f"Accelerator is of type {self.type}"+('FFF' if self.fff else '')+f" with energy {self.energy}MV and machinefile {self.machfile}."
