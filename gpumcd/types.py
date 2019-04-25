import ctypes,operator
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
		if 'image' in kwargs:
			# contruct from image.imagehu2dens_table,dens2mat_table):
			'''
			specify an image containing hounsfield units (so, a CT), and two tables that convert these hounsfield values to densities, and densities to materials. these materials must correspond to the materials provided to gpumcd upon init.
			'''
			assert isinstance(kwargs['image'],image.image)

		elif len(args) == 0 and 'DimSize' in kwargs and 'ElementSpacing' in kwargs:
			#new blank image
			if not isinstance(kwargs['DimSize'],list) or not isinstance(kwargs['ElementSpacing'],list):
				raise IOError("New phantom must be instantiated with lists for Dimsize and ElementSpacing.")
			elif len(kwargs['DimSize']) is len(kwargs['ElementSpacing']) is 3:
				nVoxels=reduce(operator.mul,kwargs['DimSize'])
				self.numVoxels.x=kwargs['DimSize'][0]
				self.numVoxels.y=kwargs['DimSize'][1]
				self.numVoxels.z=kwargs['DimSize'][2]
				self.voxelSizes.x=kwargs['ElementSpacing'][0]
				self.voxelSizes.y=kwargs['ElementSpacing'][1]
				self.voxelSizes.z=kwargs['ElementSpacing'][2]
				self.massDensityArray_data = (ctypes.c_float * nVoxels)()
				self.mediumIndexArray_data = (ctypes.c_float * nVoxels)()
				self.massDensityArray = ctypes.cast(self.massDensityArray_data,ctypes.POINTER(ctypes.c_float))
				self.mediumIndexArray = ctypes.cast(self.mediumIndexArray_data,ctypes.POINTER(ctypes.c_float))
			else:
				raise IOError("New phantom instantiated with mismatched dimensions.")


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
