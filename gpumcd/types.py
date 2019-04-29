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
		self.materials=[]
		if isinstance(args[0],image.image):
			'''
			specify an image containing hounsfield units (so, a CT), and two tables that convert these hounsfield values to densities, and densities to materials (hu2dens_table,dens2mat_table as kwargs). these materials must correspond to the materials provided to gpumcd upon init.
			'''
			im = args[0]
			if im.ndim() is not 3:
				raise IOError("Sorry, phantoms can only be instantiated with 3D images.")
			self.massDensityArray_data = (ctypes.c_float * im.nvox())()
			self.mediumIndexArray_data = (ctypes.c_float * im.nvox())()
			self.massDensityArray = ctypes.cast(self.massDensityArray_data,ctypes.POINTER(ctypes.c_float))
			self.mediumIndexArray = ctypes.cast(self.mediumIndexArray_data,ctypes.POINTER(ctypes.c_float))
			if 'hu2dens_table' in kwargs and 'dens2mat_table' in kwargs:
				self.__hu2dens2mat__(im.imdata,self.massDensityArray_data,self.mediumIndexArray_data,**kwargs)
				self.materials.extend(kwargs['dens2mat_table'][1])

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
	def __hu2dens2mat__(self,*args,**kwargs):
		try:
			hu_arr = args[0] #numpy array with CT values
			dens_arr = args[1]
			mat_arr = args[2]
			hu2dens_table = kwargs['hu2dens_table'] #list of two lists
			dens2mat_table = kwargs['dens2mat_table'] #list of two lists
		except:
			raise IOError("You called __hu2dens2mat__ with wrong or invalid arguments.")

		continuous_material_index_axis = list(range(len(dens2mat_table[0])))
		for i,value in enumerate(hu_arr):
			dens_arr[i] = np.interp(value,hu2dens_table[0],hu2dens_table[1])
			if dens_arr[i] < 0:
				dens_arr[i] = 0
			mat_arr[i] = np.interp(dens_arr[i],dens2mat_table[0],continuous_material_index_axis)


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
