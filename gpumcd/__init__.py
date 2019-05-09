import ctypes
from .types import *
from .ctypes_helpers import *
from os import path
import os
import configparser

class Settings():
	def __init__(self,gpumcd_datadir):
		defkwargs = {
			'subdirectories':{
				'gpumcd_material_data_dir': 'materials_clin',
				'gpumcd_dll_dir': 'dll',
				'hounsfield_conversion_dir': 'hounsfield'
			},
			'gpumcd_machines':{
				'MRLinac_MV7': 'machines/machine_mrl_okt2017/gpumcdToolkitMachine.vsm.gpumdt',
				'Agility_MV6_FF': 'machines/machines_van_thomas/3990Versa06MV/GPUMCD/gpumcdToolkitMachine.segments.gpumdt',
				'Agility_MV6_NoFF':'machines/machines_van_thomas/3990Versa06FFF/GPUMCD/gpumcdToolkitMachine.segments.gpumdt',
				'Agility_MV10_FF':'machines/machines_van_thomas/3991.VersaHD10MV/GPUMCD/gpumcdToolkitMachine.segments.gpumdt',
				'Agility_MV10_NoFF':'machines/machines_van_thomas/3990VersaHD10MVFFF/GPUMCD/gpumcdToolkitMachine.segments.gpumdt'
			},
			'debug':{
				'gpu_device':'0',
				'verbose':'1',
				'output':'false'
			},
			'dose':{
				'field_margin':'5',
				'dose_per_fraction':'false',
				'pinnacle_vmat_interpolation':'true',
				'monte_carlo_high_precision':'false',
				'score_dose_to_water':'true',
				'score_and_transport_in_water':'true'
			},
			'gpumcd_physicssettings':{
				'photonTransportCutoff':'0.01',
				'electronTransportCutoff':'0.189',
				'inputMaxStepLength':'0.75',
				'referenceMedium':'-1',
				'useElectronInAirSpeedup':'true',
				'electronInAirSpeedupDensityThreshold':'0.002'
			},
			'gpumcd_plansettings':{
				'goalSfom':'1',
				'statThreshold':'0.5',
				'maxNumParticles':'1e13',
				'densityThresholdSfom':'0.2',
				'densityThresholdOutput':'0.0472',
				'useApproximateStatistics':'true'
			}
		}

		ini_file = path.join(gpumcd_datadir,"dosia.ini")
		cfg = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
		cfg.optionxform = lambda option: option #prevent python lowercaseing
		cfg.read_dict(defkwargs)
		if os.path.isfile(ini_file):
			cfg.read(ini_file)
		else:
			print("No ini provided, using default settings.")
		self.__dict__.update(cfg._sections)

		# Now, overwrite all nonstrings.
		self.debug['gpu_device']=cfg.getint('debug','gpu_device')
		self.debug['verbose']=cfg.getint('debug','verbose')
		self.debug['output']=cfg.getboolean('debug','output')

		self.dose['field_margin']=cfg.getfloat('dose','field_margin')
		self.dose['dose_per_fraction']=cfg.getboolean('dose','dose_per_fraction')
		self.dose['pinnacle_vmat_interpolation']=cfg.getboolean('dose','pinnacle_vmat_interpolation')
		self.dose['monte_carlo_high_precision']=cfg.getboolean('dose','monte_carlo_high_precision')
		self.dose['score_dose_to_water']=cfg.getboolean('dose','score_dose_to_water')
		self.dose['score_and_transport_in_water']=cfg.getboolean('dose','score_and_transport_in_water')

		self.gpumcd_physicssettings['photonTransportCutoff']=cfg.getfloat('gpumcd_physicssettings','photonTransportCutoff')
		self.gpumcd_physicssettings['electronTransportCutoff']=cfg.getfloat('gpumcd_physicssettings','electronTransportCutoff')
		self.gpumcd_physicssettings['inputMaxStepLength']=cfg.getfloat('gpumcd_physicssettings','inputMaxStepLength')
		self.gpumcd_physicssettings['referenceMedium']=cfg.getint('gpumcd_physicssettings','referenceMedium')
		self.gpumcd_physicssettings['useElectronInAirSpeedup']=cfg.getboolean('gpumcd_physicssettings','useElectronInAirSpeedup')
		self.gpumcd_physicssettings['electronInAirSpeedupDensityThreshold']=cfg.getfloat('gpumcd_physicssettings','electronInAirSpeedupDensityThreshold')

		self.gpumcd_plansettings['goalSfom']=cfg.getfloat('gpumcd_plansettings','goalSfom')
		self.gpumcd_plansettings['statThreshold']=cfg.getfloat('gpumcd_plansettings','statThreshold')
		self.gpumcd_plansettings['maxNumParticles']=int(cfg.getfloat('gpumcd_plansettings','maxNumParticles'))
		self.gpumcd_plansettings['densityThresholdSfom']=cfg.getfloat('gpumcd_plansettings','densityThresholdSfom')
		self.gpumcd_plansettings['densityThresholdOutput']=cfg.getfloat('gpumcd_plansettings','densityThresholdOutput')
		self.gpumcd_plansettings['useApproximateStatistics']=cfg.getboolean('gpumcd_plansettings','useApproximateStatistics')

		self.gpumcd_datadir = gpumcd_datadir


class Engine():
	'''
	Works on Windows 64bit platform only.
	'''
	def __init__(self,settings):
		self.lasterror=ctypes.create_string_buffer(1000)
		self.settings = settings
		defkwargs = {
		'cudaDeviceId':0,
		'logging':0,
		'gpumcd_material_data_dir':None,
		'materials_nb':1,
		'materials_':["Water"],
		'physicsSettings_':PhysicsSettings(),
		'phantom_':PlanSettings(),
		'machineFile':None,
		'num_parallel_streams_':1,
		'description':ctypes.byref(self.lasterror)
		}

		self.__dict__.update(defkwargs)
		self.__gpumcd_object__ = __gpumcd__(gpumcd_datadir)


	# 0,
	# 0,
	# gpumcd.str2charp("D:/postdoc/gpumcd_data/materials_clin"),
	# *gpumcd.strlist2charpp(materials),
	# physicsSettings,
	# phantom,
	# gpumcd.str2charp("D:/postdoc/gpumcd_data/machines/machine_van_sami/brentAgility.beamlets.gpumdt"),
	# n_streams,
	# ctypes.byref(lasterror)







class __gpumcd__():
	'''
	Don't use directly.

	Works on Windows 64bit platform only.
	'''
	def __init__(self,dll_path):
		libgpumcd_fname = "libgpumcd.dll"
		assert(path.isdir(dll_path))
		assert(path.isfile(path.join(dll_path,libgpumcd_fname)))

		os.chdir(dll_path)
		libgpumcd = ctypes.CDLL(path.join(dll_path,libgpumcd_fname))
		print (path.join(dll_path,libgpumcd_fname),'loaded.')

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
