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
	def __init__(self,value=-1):
		self.value = -1

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
	def __init__(self,first=0,second=0):
		self.first=first
		self.second=second

class PhysicsSettings(ctypes.Structure):
	_fields_ = [("photonTransportCutoff", ctypes.c_float), ("electronTransportCutoff", ctypes.c_float), ("inputMaxStepLength", ctypes.c_float), ("magneticField", Float3), ("referenceMedium", ctypes.c_int), ("useElectronInAirSpeedup", ctypes.c_int), ("electronInAirSpeedupDensityThreshold", ctypes.c_float)]

class PlanSettings(ctypes.Structure):
	_fields_ = [("goalSfom", ctypes.c_float), ("statThreshold", ctypes.c_float), ("maxNumParticles", ctypes.c_uint64), ("densityThresholdSfom", ctypes.c_float), ("densityThresholdOutput", ctypes.c_float), ("useApproximateStatistics", ctypes.c_int)]

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
				print("dens is not float")
				dens.imdata = dens.imdata.astype('<f4')
			if med.imdata.dtype != 'float32':
				print("med is not float")
				med.imdata = med.imdata.astype('<f4')
			if dens.nvox() != med.nvox():
				raise IOError("Sorry, phantoms can only be instantiated with images of identical dimensions.")

			if(False):
				self.massDensityArray_data = (ctypes.c_float * dens.nvox())()
				self.mediumIndexArray_data = (ctypes.c_float * med.nvox())()
				densarr = dens.imdata.flatten()
				medarr = med.imdata.flatten()
				print('brent',len(densarr))
				for i in range(len(densarr)):
					self.massDensityArray_data[i] = densarr[i]
					self.mediumIndexArray_data[i] = medarr[i]
					print (medarr[i])
					print (self.mediumIndexArray_data[i])
				self.massDensityArray = ctypes.cast(self.massDensityArray_data,ctypes.POINTER(ctypes.c_float))
				self.mediumIndexArray = ctypes.cast(self.mediumIndexArray_data,ctypes.POINTER(ctypes.c_float))
			self.massDensityArray = dens.get_ctypes_pointer_to_data()
			self.mediumIndexArray = med.get_ctypes_pointer_to_data()
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
			self.massDensityArray_data = (ctypes.c_float * nVoxels)()
			self.mediumIndexArray_data = (ctypes.c_float * nVoxels)()
			self.massDensityArray = ctypes.cast(self.massDensityArray_data,ctypes.POINTER(ctypes.c_float))
			self.mediumIndexArray = ctypes.cast(self.mediumIndexArray_data,ctypes.POINTER(ctypes.c_float))
		else:
			raise IOError("Could not instantiate phantom, no valid arguments provided.")


class JawInformation(ctypes.Structure):
	_fields_ = [("orientation", ModifierOrientation), ("j1", Pair), ("j2", Pair)]

class MlcInformation(ctypes.Structure):
	_fields_ = [("orientation", ModifierOrientation), ("numberLeaves", ctypes.c_int), ("leftLeaves", ctypes.POINTER(Pair)), ("rightLeaves", ctypes.POINTER(Pair))]
	def __init__(self,numberLeaves):
		elems = (Pair * numberLeaves)()
		elems2 = (Pair * numberLeaves)()
		self.leftLeaves = ctypes.cast(elems,ctypes.POINTER(Pair))
		self.rightLeaves = ctypes.cast(elems2,ctypes.POINTER(Pair))
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
		elems = (BeamInformation * numberbeamInfo)()
		self.beamInfo = ctypes.cast(elems,ctypes.POINTER(BeamInformation))
		self.numberbeamInfo = numberbeamInfo
