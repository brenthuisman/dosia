import ctypes,os,configparser,image,dicom
from os import path
from .types import *
from .ctypes_helpers import *

class Settings():
	def __init__(self,gpumcd_datadir):
		defkwargs = {
			'subdirectories':{
				'material_data': 'materials_clin',
				'gpumcd_dll': 'dll',
				'hounsfield_conversion': 'hounsfield'
			},
			'gpumcd_machines':{
				'MRLinac_MV7': 'machines/machine_mrl_okt2017/gpumcdToolkitMachine.vsm.gpumdt',
				'Agility_MV6_FF': 'machines/machines_van_thomas/3990Versa06MV/GPUMCD/gpumcdToolkitMachine.segments.gpumdt',
				'Agility_MV6_NoFF':'machines/machines_van_thomas/3990Versa06FFF/GPUMCD/gpumcdToolkitMachine.segments.gpumdt',
				'Agility_MV10_FF':'machines/machines_van_thomas/3991.VersaHD10MV/GPUMCD/gpumcdToolkitMachine.segments.gpumdt',
				'Agility_MV10_NoFF':'machines/machines_van_thomas/3990VersaHD10MVFFF/GPUMCD/gpumcdToolkitMachine.segments.gpumdt'
			},
			'debug':{
				'cudaDeviceId':'0',
				'verbose':'1',
				'output':'None'
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
				'magneticField':'0,1,0',
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

		ini_file = path.join(gpumcd_datadir,"dosia.ini")
		cfg = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
		cfg.optionxform = lambda option: option #prevent python lowercaseing of categories/keys
		cfg.read_dict(defkwargs)
		if path.isfile(ini_file):
			cfg.read(ini_file)
		else:
			print("No ini provided, using default settings.")

		try:
			self.directories = {} #put absolute paths in self.directories
			self.directories['material_data'] = path.join(gpumcd_datadir,cfg.get('subdirectories','material_data'))
			assert(path.isdir(self.directories['material_data']))
			self.directories['gpumcd_dll'] = path.join(gpumcd_datadir,cfg.get('subdirectories','gpumcd_dll'))
			assert(path.isdir(self.directories['gpumcd_dll']))
			self.directories['hounsfield_conversion'] = path.join(gpumcd_datadir,cfg.get('subdirectories','hounsfield_conversion'))
			assert(path.isdir(self.directories['hounsfield_conversion']))

			self.machinefiles = cfg._sections['gpumcd_machines']

			self.debug={}
			self.debug['cudaDeviceId']=cfg.getint('debug','cudaDeviceId')
			self.debug['verbose']=cfg.getint('debug','verbose')
			self.debug['output']=cfg.get('debug','output')

			self.dose={}
			self.dose['field_margin']=cfg.getfloat('dose','field_margin')
			self.dose['dose_per_fraction']=cfg.getboolean('dose','dose_per_fraction')
			self.dose['pinnacle_vmat_interpolation']=cfg.getboolean('dose','pinnacle_vmat_interpolation')
			self.dose['monte_carlo_high_precision']=cfg.getboolean('dose','monte_carlo_high_precision')
			self.dose['score_dose_to_water']=cfg.getboolean('dose','score_dose_to_water')
			self.dose['score_and_transport_in_water']=cfg.getboolean('dose','score_and_transport_in_water')

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


class CT():
	def __init__(self,settings,ct_image): #,intercept=0,slope=1):
		'''
		The supplied image is assumed to have its voxels set to HU.
		'''
		assert(isinstance(ct_image,image.image))
		assert(isinstance(settings,Settings))

		hu2dens_table=[[],[]]
		with open(path.join(settings.directories['hounsfield_conversion'],'hu2dens.ini'),'r') as f:
			for line in f.readlines():
				if line.startswith('#'):
					continue
				hu2dens_table[0].append(float(line.split()[0]))
				hu2dens_table[1].append(float(line.split()[1]))
		dens2mat_table=[[],[]]
		with open(path.join(settings.directories['hounsfield_conversion'],'dens2mat.ini'),'r') as f:
			for line in f.readlines():
				if line.startswith('#'):
					continue
				dens2mat_table[0].append(float(line.split()[0]))
				dens2mat_table[1].append(line.split()[1])

		dens=ct_image.copy()
		# dens.ct_to_hu(intercept,slope)

		if path.isdir(settings.debug['output']):
			dens.saveas(path.join(settings.debug['output'],'ct_as_hu.xdr'))

		dens.hu_to_density(hu2dens_table)
		med=dens.copy()

		self.materials = med.density_to_materialindex(dens2mat_table)
		self.phantom=Phantom(massDensityArray_image=dens,mediumIndexArray_image=med)
		self.dosemap = image.image(DimSize=med.header['DimSize'], ElementSpacing=med.header['ElementSpacing'], Offset=med.header['Offset'], dt='<f4')

		if path.isdir(settings.debug['output']):
			dens.saveas(path.join(settings.debug['output'],'dens.xdr'))
			med.saveas(path.join(settings.debug['output'],'med.xdr'))


class Accelerator():
	def __init__(self,sett,typestring,energy):
		assert(isinstance(sett,Settings))
		assert(isinstance(typestring,str))
		self.type = None
		self.energy = None #is in controlpoint
		self.filter = None #unknown
		self.leafs_per_bank = None
		self.machfile = None
		if 'MLC160' in typestring or 'M160' in typestring:
			self.type = 'Agility'
			self.energy = energy
			self.filter = True #default
			self.leafs_per_bank = 80
		elif 'MLC80' in typestring or 'M80' in typestring:
			self.type = 'MLCi80'
			self.energy = energy
			self.filter = True
			self.leafs_per_bank = 40
		else:
			ImportError("Unknown type of TreatmentMachineName found:"+typstring)

		#FIXME set machfile, for which we need to know energy and filter.
		#	sett.gpumcd_machines
	def __str__(self):
		return f"Accelerator is of type {self.type} with energy {self.energy}MV."




class Rtplan():
	def __init__(self,sett,rtplan_dicom):
		'''
		TODO:
		* Setup ASYMX/Y correctly
		* Use BeamLimitingDeviceSequence, do not assume fixed order in array.
		* Fix cumulative -> absolute weight
		* Add dynamic/fixed cp (differen first/second for Pairs)
		'''
		assert(isinstance(sett,Settings))
		assert(isinstance(rtplan_dicom,dicom.pydicom_object))

		self.accelerator = Accelerator(sett,rtplan_dicom.data.BeamSequence[0].TreatmentMachineName,rtplan_dicom.data.BeamSequence[0].ControlPointSequence[0].NominalBeamEnergy)

		if sett.debug['verbose']>0:
			print(self.accelerator)

		beamweights = []
		for b in range(rtplan_dicom.data.FractionGroupSequence[0].NumberOfBeams):
			#theres only 1 fractiongroup
			beamweights.append(float(rtplan_dicom.data.FractionGroupSequence[0].ReferencedBeamSequence[b].BeamMeterset))

		self.beams=[] #for each beam, controlpoints
		for i,bw in enumerate(beamweights):
			#total weight of cps in beam is 1
			# convert cumulative weights to relative weights and then absolute weights using bw.
			nbcps = rtplan_dicom.data.BeamSequence[i].NumberOfControlPoints
			self.beams.append(make_c_array(ControlPoint,nbcps))
			for cpi in range(nbcps):
				# python has no references, so keep this in mind:
				# from: rtplan_dicom.data.BeamSequence[i].ControlPointSequence[cpi]
				# to: self.beams[i][cpi]
				# print("cpi",cpi)
				self.beams[i][cpi] = ControlPoint()

				self.beams[i][cpi].collimator.perpendicularJaw.orientation = ModifierOrientation(0) # ASYMX
				self.beams[i][cpi].collimator.parallelJaw.orientation = ModifierOrientation() # default = MLCi80 = None
				if self.accelerator.type != "MLCi80":
					self.beams[i][cpi].collimator.parallelJaw.orientation = ModifierOrientation(1) # ASYMY

				self.beams[i][cpi].collimator.mlc = MlcInformation(self.accelerator.leafs_per_bank)

				self.beams[i][cpi].beamInfo.relativeWeight = rtplan_dicom.data.BeamSequence[i].ControlPointSequence[cpi].CumulativeMetersetWeight * bw
				#isoc only in first cp
				self.beams[i][cpi].beamInfo.isoCenter = Float3(*rtplan_dicom.data.BeamSequence[i].ControlPointSequence[0].IsocenterPosition)
				self.beams[i][cpi].beamInfo.gantryAngle = Pair(rtplan_dicom.data.BeamSequence[i].ControlPointSequence[cpi].GantryAngle)
				#TableTopEccentricAngle only in first cp
				self.beams[i][cpi].beamInfo.couchAngle = Pair(rtplan_dicom.data.BeamSequence[i].ControlPointSequence[0].TableTopEccentricAngle)
				#BeamLimitingDeviceAngle only in first cp
				self.beams[i][cpi].beamInfo.collimatorAngle = Pair(rtplan_dicom.data.BeamSequence[i].ControlPointSequence[0].BeamLimitingDeviceAngle)

				for l in range(self.accelerator.leafs_per_bank):
					# print(i,cpi,l)
					# rightleaves: eerste helft.
					self.beams[i][cpi].collimator.mlc.rightLeaves[l] = Pair(rtplan_dicom.data.BeamSequence[i].ControlPointSequence[cpi].BeamLimitingDevicePositionSequence[-1].LeafJawPositions[l])
					#leftleaves : tweede helft.
					self.beams[i][cpi].collimator.mlc.leftLeaves[l] = Pair(rtplan_dicom.data.BeamSequence[i].ControlPointSequence[cpi].BeamLimitingDevicePositionSequence[-1].LeafJawPositions[l+self.accelerator.leafs_per_bank])

				# #check: do we have ASYMX? If yes, easy. If now, then
				# if self.beams[i][cpi].collimator.mlc.perpendicularJaw.orientation.value != -1:
				# 	#geen ASYMX, dus min van elke bank nemen voor fieldmin/max
				# 	self.beams[i][cpi].collimator.mlc.perpendicularJaw.j1 =
				# 	self.beams[i][cpi].collimator.mlc.perpendicularJaw.j2 =


				# self.beams[i][cpi].beamInfo.fieldMin =
				# self.beams[i][cpi].beamInfo.fieldMax =

				# self.beams[i][cpi].collimator.mlc.perpendicularJaw.j1 =
				# self.beams[i][cpi].collimator.mlc.perpendicularJaw.j2 =

				#




# for cp in data.BeamSequence[0].ControlPointSequence:
# 	weights_beam_0.append( cp.CumulativeMetersetWeight )

# for i in range(len(weights_beam_0)):
# 	print(i, '\t', weights_beam_0[i], '\t', end="")
# 	try:
# 		weights_beam_0[i] = weights_beam_0[i+1] - weights_beam_0[i]
# 		print(weights_beam_0[i])
# 	except:
# 		pass


# was dis?:
#for beam in data.BeamSequence:
	#i = 0
	#for cp in beam.ControlPointSequence:
		##print(i,cp.CumulativeMetersetWeight)
		#weights_beam_0.append( cp.CumulativeMetersetWeight )
		#i+=1




	#def setcp(self,index,)



	# machine:
	#   beamsequence>beam1>TreatmentMachineName = NKIAgility6MV
	# OR
	#   beamsequence>beam1>beamtype = static #meaning?
	#   beamsequence>beam1>radiationtype = Photon
	#   beamsequence>beam1>controlpointsequence>cp1>NominalBeamEnergy = 6

	pass


class Engine():
	'''
	Works on Windows 64bit platform only.
	'''
	def __init__(self,settings,phantom,materials,machfile):
		self.settings = settings
		self.phantom = phantom
		self.materials = materials
		self.machfile = machfile

		self.__gpumcd_object__ = __gpumcd__(self.settings.directories['gpumcd_dll'])

		self.__lasterror__ = ctypes.create_string_buffer(1000)

		# self.__gpumcd_object__.get_available_vram(0) #FIXME deze boyo geeft error...

		max_streams = np.floor(self.__gpumcd_object__.get_available_vram(self.settings.debug['cudaDeviceId'])/self.__gpumcd_object__.estimate_vram_consumption(self.phantom.nvox()))
		self.num_parallel_streams = min(max_streams,3)
		# self.num_parallel_streams = 1

		#print (self.num_parallel_streams)

		self.__lasterrorcode__ = self.__gpumcd_object__.init(
			self.settings.debug['cudaDeviceId'],
			self.settings.debug['verbose'],
			str2charp(self.settings.directories['material_data']),
			*strlist2charpp(self.materials),
			self.settings.physicsSettings,
			self.phantom,
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

	def execute_segments(self,controlpoints):
		assert(isinstance(controlpoints,ControlPoint))
		self.__lasterrorcode__ = self.__gpumcd_object__.execute_segments(
			*c_array_to_pointer(controlpoints,True),
			self.settings.planSettings
		)

	def get_dose(self,dosemap):
		assert(isinstance(dosemap,image.image))
		assert(self.phantom.nvox() == dosemap.nvox())
		self.__gpumcd_object__.get_dose(dosemap.get_ctypes_pointer_to_data())
		indata = np.asarray(dosemap.imdata, order='F')
		dosemap.imdata = indata.reshape(tuple(reversed(dosemap.header['DimSize']))).swapaxes(0, dosemap.header['NDims'] - 1)


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
