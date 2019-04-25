import ctypes
from .types import *
from .ctypes_helpers import *
from os import path
import os

# class Engine():
# 	'''
# 	Works on Windows 64bit platform only.
# 	'''
# 	def __init__(self,**kwargs):
# 		defkwargs = {
# 		'cudaDeviceId':0,
# 		'logging':0,
# 		'gpumcd_material_data_dir':'D:/postdoc/gpumcd_data/materials_clin',
# 		'materials_nb',
# 		'materials_',
# 		'physicsSettings_',
# 		'phantom_',
# 		'machineFile',
# 		'num_parallel_streams_',
# 		'description'
# 		}
#         self.__dict__.update(defkwargs)
#         self.__dict__.update(kwargs)
# 		self.__gpumcd_object__ = Gpumcd()


# 	0,
# 	0,
# 	gpumcd.str2charp("D:/postdoc/gpumcd_data/materials_clin"),
# 	*gpumcd.strlist2charpp(materials),
# 	physicsSettings,
# 	phantom,
# 	gpumcd.str2charp("D:/postdoc/gpumcd_data/machines/machine_van_sami/brentAgility.beamlets.gpumdt"),
# 	n_streams,
# 	ctypes.byref(lasterror)







class __gpumcd__():
	'''
	Don't use directly.

	Works on Windows 64bit platform only.
	'''
	def __init__(self):
		os.chdir(path.join(path.dirname(path.abspath(__file__)),"dll"))
		print (path.join(path.dirname(path.abspath(__file__)),"dll","libgpumcd.dll"))
		libgpumcd = ctypes.CDLL(path.join(path.dirname(path.abspath(__file__)),"dll","libgpumcd.dll"))

		self.init = libgpumcd.init_gpumcd
		self.init.argtypes = [
			ctypes.c_int,
			ctypes.c_int,
			ctypes.c_char_p,
			ctypes.c_int,
			ctypes.POINTER(ctypes.c_char_p),
			PhysicsSettings,
			Phantom,
			ctypes.c_char_p,
			ctypes.c_int,
			ctypes.c_voidp ] # https://stackoverflow.com/questions/9126031/python-ctypes-sending-pointer-to-structure-as-parameter-to-native-library
		self.init.restype  = ctypes.c_int

		self.execute_segments = libgpumcd.execute_segments
		self.execute_segments.argtypes = [
			ctypes.c_int,
			ctypes.POINTER(ControlPoint),
			PlanSettings ]
		self.execute_segments.restype  = ctypes.c_int

		self.execute_beamlets = libgpumcd.execute_beamlets
		self.execute_beamlets.argtypes = [
			ctypes.c_int,
			ctypes.POINTER(BeamFrame),
			PlanSettings ]
		self.execute_beamlets.restype  = ctypes.c_int

		self.get_dose = libgpumcd.get_dose
		self.get_dose.argtypes = [
			ctypes.POINTER(ctypes.c_float) ]
		self.get_dose.restype  = ctypes.c_int

		self.get_available_vram = libgpumcd.get_available_vram
		self.get_available_vram.argtypes = [
			ctypes.c_int ]
		self.get_available_vram.restype  = ctypes.c_int

		self.estimate_vram_consumption = libgpumcd.estimate_vram_consumption
		self.estimate_vram_consumption.argtypes = [
			ctypes.c_int ]
		self.estimate_vram_consumption.restype  = ctypes.c_int
