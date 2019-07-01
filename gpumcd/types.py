import ctypes,operator,numpy as np
from functools import reduce
import image

class ModifierOrientation(ctypes.Structure):
	'''
    NOT_PRESENT = -1,
    IECX = 0,
    IECY = 1
	'''
	_fields_ = [("value", ctypes.c_int)]
	def __init__(self,v=-1):
		self.value = v

class Int3(ctypes.Structure):
	_fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int), ("z", ctypes.c_int)]
	def __init__(self,x=0,y=0,z=0):
		self.x=x
		self.y=y
		self.z=z

class Float3(ctypes.Structure):
	_fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]
	def __init__(self,x=0,y=0,z=0):
		self.x=x
		self.y=y
		self.z=z

class Pair(ctypes.Structure):
	_fields_ = [("first", ctypes.c_float), ("second", ctypes.c_float)]
	def __init__(self,first=0,second=None):
		self.first=first
		if second == None:
			self.second=first
		else:
			self.second=second

class PhysicsSettings(ctypes.Structure):
	_fields_ = [("photonTransportCutoff", ctypes.c_float), ("electronTransportCutoff", ctypes.c_float), ("inputMaxStepLength", ctypes.c_float), ("magneticField", Float3), ("referenceMedium", ctypes.c_int), ("useElectronInAirSpeedup", ctypes.c_int), ("electronInAirSpeedupDensityThreshold", ctypes.c_float)]
	def __init__(self):
		self.photonTransportCutoff = 0.01
		self.electronTransportCutoff = 0.189
		self.inputMaxStepLength = 0.75
		self.magneticField = Float3(0,0,0)
		self.referenceMedium = -1
		self.useElectronInAirSpeedup = 1
		self.electronInAirSpeedupDensityThreshold = 0.002

class PlanSettings(ctypes.Structure):
	_fields_ = [("goalSfom", ctypes.c_float), ("statThreshold", ctypes.c_float), ("maxNumParticles", ctypes.c_uint64), ("densityThresholdSfom", ctypes.c_float), ("densityThresholdOutput", ctypes.c_float), ("useApproximateStatistics", ctypes.c_int)]
	def __init__(self):
		self.goalSfom = 2
		self.statThreshold = 0.5
		self.maxNumParticles = int(1e13)
		self.densityThresholdSfom = 0.2
		self.densityThresholdOutput = 0.0472
		self.useApproximateStatistics = 1

class Phantom(ctypes.Structure):
	'''
	use the massDensityArray_data and mediumIndexArray_data members. they're not part of the struct, but are what the massDensityArray and mediumIndexArray pointers point to.
	'''
	_fields_ = [("numVoxels", Int3), ("voxelSizes", Float3), ("phantomCorner", Float3), ("massDensityArray", ctypes.POINTER(ctypes.c_float)), ("mediumIndexArray", ctypes.POINTER(ctypes.c_float))]
	def __init__(self,*args,**kwargs):
		if 'massDensityArray_image' in kwargs and 'mediumIndexArray_image' in kwargs:
			'''
			specify an image containing hounsfield units (so, a CT), and two tables that convert these hounsfield values to densities, and densities to materials (hu2dens_table,dens2mat_table as kwargs). these materials must correspond to the materials provided to gpumcd upon init.
			'''
			dens = kwargs['massDensityArray_image']
			med = kwargs['mediumIndexArray_image']
			if not isinstance(med,image.image) or not isinstance(dens,image.image):
				raise IOError("Could not instantiate phantom, either or both massDensityArray_image and mediumIndexArray_image are not valid instances of image.image.")
			if dens.ndim() != 3 or med.ndim() is not 3:
				raise IOError("Sorry, phantoms can only be instantiated with 3D images.")
			if dens.imdata.dtype != 'float32':
				# print("dens is not float")
				dens.imdata = dens.imdata.astype('<f4')
			if med.imdata.dtype != 'float32':
				# print("med is not float")
				med.imdata = med.imdata.astype('<f4')
			if dens.nvox() != med.nvox():
				raise IOError("Sorry, phantoms can only be instantiated with images of identical dimensions.")

			nVoxels =  med.header['DimSize'][0]* med.header['DimSize'][1]* med.header['DimSize'][2]
			self.__massDensityArray_data = (ctypes.c_float * nVoxels)()
			self.__mediumIndexArray_data = (ctypes.c_float * nVoxels)()

			# put data in right order, as if saving to disk.
			dens_imdata = np.asarray(dens.imdata.swapaxes(0, dens.header['NDims'] - 1),order='C').flatten()
			med_imdata = np.asarray(med.imdata.swapaxes(0, med.header['NDims'] - 1),order='C').flatten()
			for i,(d,m) in enumerate(zip( dens_imdata,med_imdata ) ):
				self.__massDensityArray_data[i] = d
				self.__mediumIndexArray_data[i] = m

			self.numVoxels.x = med.header['DimSize'][0]
			self.numVoxels.y = med.header['DimSize'][1]
			self.numVoxels.z = med.header['DimSize'][2]
			# Convert mm to cm
			self.voxelSizes.x = med.header['ElementSpacing'][0]/10.
			self.voxelSizes.y = med.header['ElementSpacing'][1]/10.
			self.voxelSizes.z = med.header['ElementSpacing'][2]/10.
			# Half voxel shift, and divison by ten
			self.phantomCorner.x = med.header['Offset'][0]/10. - med.header['ElementSpacing'][0]/20.
			self.phantomCorner.y = med.header['Offset'][1]/10. - med.header['ElementSpacing'][1]/20.
			self.phantomCorner.z = med.header['Offset'][2]/10. - med.header['ElementSpacing'][2]/20.

		elif isinstance(args[0],int):
			'''
			"Default" constructor, reserving int values that you provide in massDensityArray_data and mediumIndexArray_data. Rest is up to you!
			'''
			nVoxels=args[0]
			#these members musnt be garbage collected away after __init__, but otherwise you should use the pointer
			self.__massDensityArray_data = (ctypes.c_float * nVoxels)()
			self.__mediumIndexArray_data = (ctypes.c_float * nVoxels)()
		else:
			raise IOError("Could not instantiate phantom, no valid arguments provided.")

		self.massDensityArray = ctypes.cast(self.__massDensityArray_data,ctypes.POINTER(ctypes.c_float))
		self.mediumIndexArray = ctypes.cast(self.__mediumIndexArray_data,ctypes.POINTER(ctypes.c_float))

	def nvox(self):
		return self.numVoxels.x*self.numVoxels.y*self.numVoxels.z

class JawInformation(ctypes.Structure):
	_fields_ = [("orientation", ModifierOrientation), ("j1", Pair), ("j2", Pair)]

class MlcInformation(ctypes.Structure):
	_fields_ = [("orientation", ModifierOrientation), ("numberLeaves", ctypes.c_int), ("leftLeaves", ctypes.POINTER(Pair)), ("rightLeaves", ctypes.POINTER(Pair))]
	def __init__(self,numberLeaves):
		self.__leftLeaves_data = (Pair * numberLeaves)()
		self.__rightLeaves_data = (Pair * numberLeaves)()
		self.leftLeaves = ctypes.cast(self.__leftLeaves_data,ctypes.POINTER(Pair))
		self.rightLeaves = ctypes.cast(self.__rightLeaves_data,ctypes.POINTER(Pair))
		self.numberLeaves = numberLeaves

class ModifierInformation(ctypes.Structure):
	_fields_ = [("parallelJaw", JawInformation), ("perpendicularJaw", JawInformation), ("mlc", MlcInformation)]

class BeamInformation(ctypes.Structure):
	_fields_ = [("relativeWeight", ctypes.c_float), ("isoCenter", Float3), ("gantryAngle", Pair), ("couchAngle", Pair), ("collimatorAngle", Pair), ("fieldMin", Pair), ("fieldMax", Pair)]

class ControlPoint(ctypes.Structure):
	_fields_ = [("collimator", ModifierInformation), ("beamInfo", BeamInformation)]

class BeamFrame(ctypes.Structure):
	_fields_ = [("numberbeamInfo", ctypes.c_int), ("beamInfo", ctypes.POINTER(BeamInformation))]
	def __init__(self,numberbeamInfo):
		self.__beamInfo_data = (BeamInformation * numberbeamInfo)()
		self.beamInfo = ctypes.cast(self.__beamInfo_data,ctypes.POINTER(BeamInformation))
		self.numberbeamInfo = numberbeamInfo
