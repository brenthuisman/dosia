import ctypes

class ModifierOrientation(ctypes.Structure):
	_fields_ = [("value", ctypes.c_int)]

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
	_fields_ = [("numVoxels", Int3), ("voxelSizes", Float3), ("phantomCorner", Float3), ("massDensityArray", ctypes.POINTER(ctypes.c_float)), ("mediumIndexArray", ctypes.POINTER(ctypes.c_float))]
	def __init__(self,numVoxels):
		elems = (ctypes.c_float * numVoxels)()
		elems2 = (ctypes.c_float * numVoxels)()
		self.massDensityArray = ctypes.cast(elems,ctypes.POINTER(ctypes.c_float))
		self.mediumIndexArray = ctypes.cast(elems2,ctypes.POINTER(ctypes.c_float))

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
