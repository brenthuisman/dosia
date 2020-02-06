import configparser
from os import path,getcwd
from .gpumcdwrapper import PlanSettings, PhysicsSettings, Float3

class Settings():
	def __init__(self,dosia_ini_dir=None):
		dosia_ini_file = "dosia.ini"
		if dosia_ini_dir is None:
			dosia_ini_dir = getcwd()

		defkwargs = {
			'directories':{ # relative to dosia.ini or absolute
				'material_data': path.join(dosia_ini_dir,'data/materials_clin'),
				'gpumcd_dll': path.join(dosia_ini_dir,'data/dll'),
				'hounsfield_conversion': path.join(dosia_ini_dir,'data/hounsfield')
			},
			'gpumcd_machines':{
				'MRLinac_MV7': '',
				'Agility_MV6': '',
				'Agility_MV6_FFF':'',
				'Agility_MV10':'',
				'Agility_MV10_FFF':'',
				'Agility_MV15':'',
				'Agility_MV18':''
			},
			'debug':{
				'cudaDeviceId':'0',
				'verbose':'1',
				'output':'None'
			},
			'dose':{
				'field_margin':'5',
				'dose_per_fraction':'false',
				'sum_beams':'true',
				'magnetic_field':'true',
				#'pinnacle_vmat_interpolation':'true', #the next ones
				#'monte_carlo_high_precision':'false',
				#'score_dose_to_water':'true',
				#'score_and_transport_in_water':'true'
			},
			'gpumcd_physicssettings':{
				'photonTransportCutoff':'0.01',
				'electronTransportCutoff':'0.189',
				'inputMaxStepLength':'0.75',
				'magneticField':'0,0,0',
				'referenceMedium':'-1',
				'useElectronInAirSpeedup':'true',
				'electronInAirSpeedupDensityThreshold':'0.002'
			},
			'gpumcd_plansettings':{
				'goalSfom':'2',
				'statThreshold':'0.5',
				'maxNumParticles':'1e13',
				'densityThresholdSfom':'0.2',
				'densityThresholdOutput':'0.0472',
				'useApproximateStatistics':'true'
			}
		}

		cfg = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
		cfg.optionxform = lambda option: option #prevent python lowercaseing of categories/keys
		cfg.read_dict(defkwargs)
		try:
			print(f"Loading {path.join(dosia_ini_dir,dosia_ini_file)}")
			cfg.read(path.join(dosia_ini_dir,dosia_ini_file))
		except:
			print("No ini provided, using default settings.")

		try:
			self.directories = {} #must not contain double backslashes. also test presence.
			if path.isdir("C:/ProgramData/CMS/GPUMCD"):
				self.directories['material_data'] = "C:/ProgramData/CMS/GPUMCD"
			else:
				self.directories['material_data'] = cfg.get('directories','material_data').replace('\\','/')
			assert(path.isdir(self.directories['material_data']))

			if path.isdir("C:/Program Files/CMS/Monaco"):
				self.directories['gpumcd_dll'] = "C:/Program Files/CMS/Monaco"
				from shutil import copyfile
				copyfile(path.join(dosia_ini_dir,'data/dll/libgpumcd.dll'),self.directories['gpumcd_dll'])
			else:
				self.directories['gpumcd_dll'] = cfg.get('directories','gpumcd_dll').replace('\\','/')
			assert(path.isdir(self.directories['gpumcd_dll']))

			self.directories['hounsfield_conversion'] = cfg.get('directories','hounsfield_conversion').replace('\\','/')
			assert(path.isdir(self.directories['hounsfield_conversion']))

			self.machinefiles = cfg._sections['gpumcd_machines']
			for k,v in self.machinefiles.items():
				self.machinefiles[k] = path.join(v).replace('\\','/')

			self.debug={}
			self.debug['cudaDeviceId']=cfg.getint('debug','cudaDeviceId')
			self.debug['verbose']=cfg.getint('debug','verbose')
			self.debug['output']=cfg.get('debug','output')

			self.dose={}
			self.dose['sum_beams']=cfg.getboolean('dose','sum_beams')
			self.dose['magnetic_field']=cfg.getboolean('dose','magnetic_field')
			self.dose['field_margin']=cfg.getint('dose','field_margin')
			self.dose['dose_per_fraction']=cfg.getboolean('dose','dose_per_fraction')
			# self.dose['pinnacle_vmat_interpolation']=cfg.getboolean('dose','pinnacle_vmat_interpolation')
			# self.dose['monte_carlo_high_precision']=cfg.getboolean('dose','monte_carlo_high_precision')
			# self.dose['score_dose_to_water']=cfg.getboolean('dose','score_dose_to_water')
			# self.dose['score_and_transport_in_water']=cfg.getboolean('dose','score_and_transport_in_water')

			#bool implicit cast to int. works!
			self.physicsSettings = PhysicsSettings()
			self.physicsSettings.photonTransportCutoff = cfg.getfloat('gpumcd_physicssettings','photonTransportCutoff')
			self.physicsSettings.electronTransportCutoff = cfg.getfloat('gpumcd_physicssettings','electronTransportCutoff')
			self.physicsSettings.inputMaxStepLength = cfg.getfloat('gpumcd_physicssettings','inputMaxStepLength')
			magfield = [float(x) for x in cfg.get('gpumcd_physicssettings','magneticField').split(',')]
			self.physicsSettings.magneticField = Float3(*magfield)
			self.physicsSettings.referenceMedium = cfg.getint('gpumcd_physicssettings','referenceMedium')
			self.physicsSettings.useElectronInAirSpeedup = cfg.getboolean('gpumcd_physicssettings','useElectronInAirSpeedup')
			self.physicsSettings.electronInAirSpeedupDensityThreshold = cfg.getfloat('gpumcd_physicssettings','electronInAirSpeedupDensityThreshold')

			self.planSettings = PlanSettings()
			self.planSettings.goalSfom = cfg.getfloat('gpumcd_plansettings','goalSfom')
			self.planSettings.statThreshold = cfg.getfloat('gpumcd_plansettings','statThreshold')
			self.planSettings.maxNumParticles = int(cfg.getfloat('gpumcd_plansettings','maxNumParticles'))
			self.planSettings.densityThresholdSfom = cfg.getfloat('gpumcd_plansettings','densityThresholdSfom')
			self.planSettings.densityThresholdOutput = cfg.getfloat('gpumcd_plansettings','densityThresholdOutput')
			self.planSettings.useApproximateStatistics = cfg.getboolean('gpumcd_plansettings','useApproximateStatistics')
		except Exception as e:
			print("Error parsing settings. Please check your dosia.ini for validity.")
			print(e)
			raise

		try:
			assert(path.isdir(self.directories['material_data']))
			assert(path.isdir(self.directories['gpumcd_dll']))
			assert(path.isdir(self.directories['hounsfield_conversion']))
		except AssertionError:
			print("You provided nonexisting GPUMCD directories.")
