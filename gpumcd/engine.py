import numpy as np, ctypes, medimage as image
from os import path
from .settings import Settings
from .ct import CT
from .accelerator import Accelerator
from .ctypes_helpers import c_array_to_pointer, str2charp, strlist2charpp
from .gpumcdwrapper import __gpumcd__, BeamFrame, Segment

class Engine():
	'''
	Works on Windows 64bit platform only.
	'''
	def __init__(self,settings,ct,accel):
		assert(isinstance(settings,Settings))
		assert(isinstance(ct,CT))
		assert(isinstance(accel,Accelerator) or isinstance(accel,str))
		self.settings = settings
		self.settings.physicsSettings.magneticField = accel.b
		self.ct = ct
		if isinstance(accel,str):
			self.machfile = accel #assume string to machine file path was given
			self.materials = self.ct.materials
		else:
			self.machfile = accel.machfile
			self.materials = self.ct.materials + accel.materials

		if not path.isfile(path.join(self.settings.directories['gpumcd_dll'],"GPUMonteCarloDoseLibrary.dll")):
			print("GPUMonteCarloDoseLibrary.dll not found, brace for impact!")
			# TODO convert to Error and handle somewhere else?

		self.__gpumcd_object__ = __gpumcd__(self.settings.directories['gpumcd_dll'])

		self.__lasterror__ = ctypes.create_string_buffer(1000)

		self.num_parallel_streams = 1
		max_streams = np.floor(self.__gpumcd_object__.get_available_vram(self.settings.debug['cudaDeviceId'])/self.__gpumcd_object__.estimate_vram_consumption(self.ct.phantom.nvox()))
		if max_streams > 1:
			self.num_parallel_streams = 2 # more doesnt really make it faster anyway.
		if max_streams == 0:
			print(f"Possible problem: {self.__gpumcd_object__.estimate_vram_consumption(self.ct.phantom.nvox())} MB VRAM estimated required, but only {self.__gpumcd_object__.get_available_vram(self.settings.debug['cudaDeviceId'])} MB VRAM found. We'll try to run the simulation anyway, but it may fail.")

		self.__lasterrorcode__ = self.__gpumcd_object__.init(
			self.settings.debug['cudaDeviceId'],
			self.settings.debug['verbose'],
			str2charp(self.settings.directories['material_data']),
			*strlist2charpp(self.materials),
			self.settings.physicsSettings,
			self.ct.phantom,
			str2charp(self.machfile),
			self.num_parallel_streams,
			ctypes.byref(self.__lasterror__)
		)

	def lasterror(self):
		return self.__lasterrorcode__,self.__lasterror__.value.decode('utf-8')

	def execute_beamlets(self,beamframes):
		assert(isinstance(beamframes,BeamFrame))
		self.__lasterrorcode__ = self.__gpumcd_object__.execute_beamlets(
			*c_array_to_pointer(beamframes,True),
			self.settings.planSettings
		)

	def execute_segments(self,segments):
		assert(isinstance(segments[0],Segment))
		self.__lasterrorcode__ = self.__gpumcd_object__.execute_segments(
			*c_array_to_pointer(segments,True),
			self.settings.planSettings
		)

	def get_dose(self,dosemap):
		'''
		Add dose to provided dosemap voxel by voxel.
		'''
		#cant write to self.ct.dosemap directly, because self will be destroyed after this function exits!
		assert(isinstance(dosemap,image.image))
		assert(self.ct.phantom.nvox() == dosemap.nvox())
		newdose = image.image(DimSize=dosemap.header['DimSize'], ElementSpacing=dosemap.header['ElementSpacing'], Offset=dosemap.header['Offset'], dt='<f4')
		self.__gpumcd_object__.get_dose(newdose.get_ctypes_pointer_to_data())
		newdose.imdata = np.asarray(newdose.imdata, order='F').reshape(tuple(reversed(newdose.imdata.shape))).swapaxes(0, len(newdose.imdata.shape) - 1)
		dosemap.add(newdose)

