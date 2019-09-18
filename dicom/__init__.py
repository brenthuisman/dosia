import medimage as image,gpumcd,numpy as np,pydicom,glob,collections
from os import path

class pydicom_object():
	'''
	The purpose of this class is to help understand what type of dicomfile is being read. Inputs can be files or dirs. methods include modality of the file (CT, RTPLAN or RTDOSE), SOPInstanceUID in order to link with other dicom objects.

	Plan and dose are linked through sopid. plan, dose and ct are linked through studyid.
	'''
	def __init__(self,fname):
		if path.isdir(fname):
			#pydicom doesnt read dicom dirs, so lets take the first file
			fname = glob.glob(path.join (fname,'*'))[0]
		if not path.isfile(fname):
			IOError("You provided a filename or directoryname which does not exist!")
		self.filename = fname
		self.data = pydicom.dcmread(fname,force=True)
		self.modality = str(self.data.Modality)
		self.sopid = None
		self.studyid = self.data.StudyInstanceUID
		if self.modality not in ['CT','RTDOSE','RTPLAN']:
			NotImplementedError("You provided a file that is not a CT, RTDOSE or RTPLAN!")
			#TODO Struct?
		elif self.modality == "CT":
			self.PatientPosition = str(self.data.PatientPosition)
			self.RescaleIntercept = float(self.data.RescaleIntercept)
			self.RescaleSlope = float(self.data.RescaleSlope)
		elif self.modality == "RTDOSE":
			self.sopid = str(self.data.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID)
			self.DoseUnits = str(self.data.DoseUnits)
			self.DoseType = str(self.data.DoseType)
			self.DoseSummationType = str(self.data.DoseSummationType)
			assert self.DoseUnits == "GY", "This dose image is not in GY units."
			assert self.DoseType == "PHYSICAL", "This dose image is not physical dose."
			assert self.DoseSummationType in ["PLAN","FRACTION"], "This dose image is not per plan or fraction."
		elif self.modality == "RTPLAN":
			self.sopid = str(self.data.SOPInstanceUID)
			self.PatientPosition = str(self.data.PatientSetupSequence[0].PatientPosition)
			assert self.PatientPosition == 'HFS', "Patient (Plan) is not in HFS position."
			self.NumberOfFractionsPlanned = int(self.data.FractionGroupSequence[0].NumberOfFractionsPlanned)
			self.NumberOfBeams = int(self.data.FractionGroupSequence[0].NumberOfBeams)

			# sum BeamDoses if all in the same point as secondary check for amount of dose to expect in tps dose. BeamDose is specified as per fraction
			try:
				self.BeamDoseSpecificationPoint = self.data.FractionGroupSequence[0].ReferencedBeamSequence[0].BeamDoseSpecificationPoint
				self.BeamDose = self.data.FractionGroupSequence[0].ReferencedBeamSequence[0].BeamDose
				for beam in self.data.FractionGroupSequence[0].ReferencedBeamSequence[1:]:
					if self.BeamDoseSpecificationPoint == beam.BeamDoseSpecificationPoint:
						self.BeamDose += beam.BeamDose
					else:
						self.BeamDoseSpecificationPoint = None
						self.BeamDose = None
				if self.BeamDoseSpecificationPoint != None:
					self.BeamDoseSpecificationPoint = [x*0.1 for x in self.BeamDoseSpecificationPoint] #to cm
			except AttributeError:
				# plan base no beamdosespec
				self.BeamDoseSpecificationPoint = None
				self.BeamDose = None


def pydicom_casedir(dname,loadimages=True):
	ct_dirs = glob.glob(path.join(dname,"*PLAN*"))
	upi_dirs = glob.glob(path.join(dname,"*UPI*"))

	studies = collections.defaultdict(dict)

	for ct_dir in ct_dirs:
		a = pydicom_object(ct_dir)
		if a.modality == 'CT':
			studies[a.studyid]['ct'] = a
			if loadimages:
				if a.PatientPosition != 'HFS':
					raise NotImplementedError("Patient (Dose) is not in HFS position.")
				studies[a.studyid]['ct_im'] = image.image(ct_dir)
				# studies[a.studyid]['ct_im'].ct_to_hu(a.RescaleIntercept,a.RescaleSlope)
		else:
			IOError("Expected CT image, but",a.modality,"was found.")

	for upi_dir in upi_dirs:
		files_in_upi = glob.glob(path.join(upi_dir,'*'))
		for f in files_in_upi:
			a = pydicom_object(f)
			try:
				studies[a.studyid][a.sopid]
			except:
				studies[a.studyid][a.sopid]={}
			if a.modality == "RTDOSE":
				studies[a.studyid][a.sopid]['dose'] = a
				if loadimages:
					# if str(a.data.DoseUnits) != "GY":
					# 	raise NotImplementedError("The provided dicom dose image has relative units.")
					# if str(a.data.DoseType) != "PHYSICAL":
					# 	raise NotImplementedError("The provided dicom dose image is not in physical units.")
					# if str(a.data.DoseSummationType) not in ["PLAN","FRACTION"]:
					# 	raise NotImplementedError("Dose was not computed for 'PLAN' or 'FRACTION'.")
					studies[a.studyid][a.sopid]['dose_im'] = image.image(f)
					studies[a.studyid][a.sopid]['dose_im'].mul(a.data.DoseGridScaling)
			elif a.modality == "RTPLAN":
				studies[a.studyid][a.sopid]['plan'] = a
				# if loadimages and a.PatientPosition != 'HFS':
				# 	raise NotImplementedError("Patient (Plan) is not in HFS position.")
			else:
				IOError("Expected RTDOSE or RTPLAN, but",a.modality,"was found.")

	return studies

def run_casedir(sett,casedir,v):
	for sopid,d in v.items():
		if isinstance(d,dict):
			gpumcd_factor = False
			try:
				tpsdosespecpt = d['dose_im'].get_value(d['plan'].BeamDoseSpecificationPoint)
				assert(d['plan'].BeamDose*0.9 < tpsdosespecpt < d['plan'].BeamDose*1.1)
			except:
				print("TPS dose it outside of expected planned dose per fraction in beamdosespecificationpoint. Your TPS probably exported the PLAN dose instead of FRACTION dose, GPUMCD dose will be multiplied with the number of fractions.")
				gpumcd_factor = True
			d['dose_im'].saveas(path.join(casedir,"xdr",sopid,"dose_tps.xdr"))
			ctcpy = v['ct_im']
			ctcpy.crop_as(d['dose_im'])
			ctcpy.saveas(path.join(casedir,"xdr",sopid,"ct_on_dosegrid.xdr"))
			ct_obj = gpumcd.CT(sett,ctcpy)

			try:
				p=gpumcd.Rtplan(sett, d['plan'])
			except:
				print("Invalid plan found:",d['plan'].filename,"Skipping...")
				continue
			ct_obj.dosemap.zero_out()

			for beam in p.beams:
				eng=gpumcd.Engine(sett,ct_obj,p.accelerator.machfile)
				eng.execute_segments(beam)
				print (eng.lasterror())
				eng.get_dose(ct_obj.dosemap)

			if gpumcd_factor:
				ct_obj.dosemap.mul(d['plan'].NumberOfFractionsPlanned)
			else:
				# From what I've seen, dosemaps are exported per plan REGARDLESS of value of DoseSummationType. we try anyway.
				if d['dose'].DoseSummationType == 'PLAN':
					print("Dose was computed for whole PLAN, multiplying GPUMCD dose with number of fractions.")
					ct_obj.dosemap.mul(d['plan'].NumberOfFractionsPlanned)
				else:
					assert d['dose'].DoseSummationType == 'FRACTION'

			ct_obj.dosemap.saveas(path.join(casedir,"xdr",sopid,"dose_gpumcd.xdr"))