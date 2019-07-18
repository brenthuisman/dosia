import ctypes,os,configparser,image,dicom
from os import path
from .types import *
from .ctypes_helpers import *

class Settings():
	def __init__(self,gpumcd_datadir=None):
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

		cfg = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
		cfg.optionxform = lambda option: option #prevent python lowercaseing of categories/keys
		cfg.read_dict(defkwargs)
		try:
			cfg.read(path.join(gpumcd_datadir,"dosia.ini"))
		except:
			print("No ini provided, using default settings.")

		if gpumcd_datadir is None:
			gpumcd_datadir = ''

		try:
			self.directories = {} #put absolute paths in self.directories
			self.directories['material_data'] = path.join(gpumcd_datadir,cfg.get('subdirectories','material_data')).replace('\\','/')
			self.directories['gpumcd_dll'] = path.join(gpumcd_datadir,cfg.get('subdirectories','gpumcd_dll')).replace('\\','/')
			self.directories['hounsfield_conversion'] = path.join(gpumcd_datadir,cfg.get('subdirectories','hounsfield_conversion')).replace('\\','/')

			self.machinefiles = cfg._sections['gpumcd_machines']
			for k,v in self.machinefiles.items():
				self.machinefiles[k] = path.join(gpumcd_datadir,v).replace('\\','/')

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

		try:
			assert(path.isdir(self.directories['material_data']))
			assert(path.isdir(self.directories['gpumcd_dll']))
			assert(path.isdir(self.directories['hounsfield_conversion']))
		except AssertionError:
			print("You provided nonexisting GPUMCD directories.")




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
		self.materials.append("Tungsten") # collimator material

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
		self.parallelJaw = True
		if 'MLC160' in typestring or 'M160' in typestring:
			self.type = 'Agility'
			self.energy = energy
			self.filter = True #default
			self.leafs_per_bank = 80
			self.parallelJaw = False # Agility heeft GEEN parallelJaw
			if energy == 6:
				self.machfile = sett.machinefiles['Agility_MV6_FF']
			if energy == 10:
				self.machfile = sett.machinefiles['Agility_MV10_FF']
		elif 'MLC80' in typestring or 'M80' in typestring:
			self.type = 'MLCi80'
			self.energy = energy
			self.filter = True
			self.leafs_per_bank = 40
			ImportError("MLCi80 found, but no such machine exists in machine library.")
		else:
			ImportError("Unknown type of TreatmentMachineName found:"+typstring)

		# with open(self.machfile, 'r') as myfile:
		# 	self.machfile = myfile.read()
		# print(self.machfile)

	def __str__(self):
		return f"Accelerator is of type {self.type} with energy {self.energy}MV."


class Rtplan():
	def __init__(self,sett,rtplan_dicom):
		'''
		This class parses an RTplan dicom object into a series of segments that can be fed to GPUMCD.

		Some terminology: a controlpoint is a snapshot of the accelerator state at a given point. A Segment is a 'unit' of irradiation associated with a beamweight. Typically this will be the space between two controlpoints: the beamweight is the difference between the cumulative meterset weight and the controlpoint-pair describes the initial and final state of the machine for this segment. Not that Pinnacle has it's own method of interpolation, as it cannot handle dynamic segments during dose calculation.

		Typically, N controlpoints result in N-1 segments.

		Although I could not find an explicit statement on the subject, all spatial distances are returned in units of mm by pydicom. We therefore convert mm to cm. Implicit proof:
		https://pydicom.github.io/pydicom/stable/auto_examples/input_output/plot_read_rtplan.html
		'''
		scale = 0.1 #mm to cm
		assert(isinstance(sett,Settings))
		assert(isinstance(rtplan_dicom,dicom.pydicom_object))

		self.accelerator = Accelerator(sett,rtplan_dicom.data.BeamSequence[0].TreatmentMachineName,rtplan_dicom.data.BeamSequence[0].ControlPointSequence[0].NominalBeamEnergy)

		self.sett = sett
		firstsegmentonly = False
		if sett.debug['verbose']>0:
			print(self.accelerator)

		self.beamweights = []
		for b in range(rtplan_dicom.data.FractionGroupSequence[0].NumberOfBeams):
			#theres only 1 fractiongroup
			self.beamweights.append(float(rtplan_dicom.data.FractionGroupSequence[0].ReferencedBeamSequence[b].BeamMeterset))

		self.beams=[] #for each beam, controlpoints
		for bi,bw in enumerate(self.beamweights):
			#total weight of cps in beam is 1
			# convert cumulative weights to relative weights and then absolute weights using bw.

			nbcps = rtplan_dicom.data.BeamSequence[bi].NumberOfControlPoints
			nsegments = (nbcps-1)
			if firstsegmentonly:
				nsegments = 1
				if bi > 0:
					break

			mlcx_index = None
			asymy_index = None
			asymx_index = None
			for bld_index in range(len(rtplan_dicom.data.BeamSequence[bi].BeamLimitingDeviceSequence)):
				thistype = rtplan_dicom.data.BeamSequence[bi].BeamLimitingDeviceSequence[bld_index].RTBeamLimitingDeviceType
				if "MLCX" in thistype:
					mlcx_index = bld_index
				if "ASYMY" in thistype:
					asymy_index = bld_index
				if "ASYMX" in thistype:
					asymx_index = bld_index

			#following only available in first cp
			isoCenter = [coor*scale for coor in rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[0].IsocenterPosition]
			couchAngle = rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[0].PatientSupportAngle #or TableTopEccentricAngle?
			collimatorAngle = rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[0].BeamLimitingDeviceAngle

			# N cps = N-1 segments
			self.beams.append(make_c_array(Segment,nsegments))

			for cpi in range(nsegments):
				cp_this = rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[cpi]
				cp_next = rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[cpi+1]

				self.beams[bi][cpi] = Segment()

				self.beams[bi][cpi].collimator.perpendicularJaw.orientation = ModifierOrientation(1) # ASYMY

				if self.accelerator.parallelJaw:
					self.beams[bi][cpi].collimator.parallelJaw.orientation = ModifierOrientation(0)
				else:
					self.beams[bi][cpi].collimator.parallelJaw.orientation = ModifierOrientation(-1)

				self.beams[bi][cpi].collimator.mlc = MlcInformation(self.accelerator.leafs_per_bank)

				# Now, let's see what our dicom gives us about this beam

				self.beams[bi][cpi].beamInfo.relativeWeight = (cp_next.CumulativeMetersetWeight-cp_this.CumulativeMetersetWeight) * bw
				self.beams[bi][cpi].beamInfo.gantryAngle = Pair(cp_this.GantryAngle,cp_next.GantryAngle)
				#following only available in first cp
				self.beams[bi][cpi].beamInfo.isoCenter = Float3(*isoCenter)
				self.beams[bi][cpi].beamInfo.couchAngle = Pair(couchAngle)
				self.beams[bi][cpi].beamInfo.collimatorAngle = Pair(collimatorAngle)

				# MLCX
				mlcx_r = []
				mlcx_l = []
				for l in range(self.accelerator.leafs_per_bank):
					# leftleaves: eerste helft.
					lval = cp_this.BeamLimitingDevicePositionSequence[mlcx_index].LeafJawPositions[l]*scale
					rval = cp_this.BeamLimitingDevicePositionSequence[mlcx_index].LeafJawPositions[l+self.accelerator.leafs_per_bank]*scale
					lval_next = cp_next.BeamLimitingDevicePositionSequence[mlcx_index].LeafJawPositions[l]*scale
					rval_next = cp_next.BeamLimitingDevicePositionSequence[mlcx_index].LeafJawPositions[l+self.accelerator.leafs_per_bank]*scale

					self.beams[bi][cpi].collimator.mlc.rightLeaves[l] = Pair(rval,rval_next)
					self.beams[bi][cpi].collimator.mlc.leftLeaves[l] = Pair(lval,lval_next)

					mlcx_r.extend([rval,rval_next])
					mlcx_l.extend([lval,lval_next])

				# prep for field extremeties
				self.beams[bi][cpi].beamInfo.fieldMin = Pair()
				self.beams[bi][cpi].beamInfo.fieldMax = Pair()

				#ASYM X. ASYMX may be present in plan, even if accelerator doesnt have it.
				# if self.beams[bi][cpi].collimator.parallelJaw.orientation.value != -1:
				if asymx_index is not None:
					self.beams[bi][cpi].collimator.parallelJaw.j1 = Pair(cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].collimator.parallelJaw.j2 = Pair(cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale)
					# x coords of field size
					self.beams[bi][cpi].beamInfo.fieldMin.first = min(cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].beamInfo.fieldMax.first = max(cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale)
				else:
					#if no ASYM X, then we must get extreme field borders from MLCX
					print("No ASYMX jaw found in dicom, using leaf extrema to find field extrema.")
					raise NotImplementedError("For missing ASYMX, we need to find leaf extrema within ASYMY bounds. This has not been implemented yet.")
					# self.beams[bi][cpi].collimator.parallelJaw.j1 = Pair(min(mlcx_l)*scale)
					# self.beams[bi][cpi].collimator.parallelJaw.j2 = Pair(max(mlcx_r)*scale)
					# self.beams[bi][cpi].beamInfo.fieldMax.first = min(mlcx_l)
					# self.beams[bi][cpi].beamInfo.fieldMin.first = max(mlcx_r)

				# ASYM Y
				self.beams[bi][cpi].collimator.perpendicularJaw.j1 = Pair(cp_this.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[0]*scale)
				self.beams[bi][cpi].collimator.perpendicularJaw.j2 = Pair(cp_this.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[1]*scale)

				# y coords of fieldsize
				self.beams[bi][cpi].beamInfo.fieldMin.second = min(cp_this.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[0]*scale)
				self.beams[bi][cpi].beamInfo.fieldMax.second = max(cp_this.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[1]*scale)

				# apply field margins
				self.beams[bi][cpi].beamInfo.fieldMin.first -= self.sett.dose['field_margin']*scale
				self.beams[bi][cpi].beamInfo.fieldMin.second -= self.sett.dose['field_margin']*scale
				self.beams[bi][cpi].beamInfo.fieldMax.first += self.sett.dose['field_margin']*scale
				self.beams[bi][cpi].beamInfo.fieldMax.second += self.sett.dose['field_margin']*scale


		if sett.debug['verbose']>0:
			sumweights=0
			for beam in self.beams:
				beamweight=0
				for segment in beam:
					sumweights+=segment.beamInfo.relativeWeight
					beamweight+=segment.beamInfo.relativeWeight
				print(f"beamweight {beamweight}")
			print(f"total weight {sumweights}")



class Engine():
	'''
	Works on Windows 64bit platform only.
	'''
	def __init__(self,settings,ct,machfile):
		self.settings = settings
		self.ct = ct
		self.machfile = machfile

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
			*strlist2charpp(self.ct.materials),
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
			ctypes.POINTER(Segment),
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
