import image,gpumcd,numpy as np,pydicom,glob,collections
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
			self.DoseSummationType = str(self.data.DoseSummationType)
		elif self.modality == "RTPLAN":
			self.sopid = str(self.data.SOPInstanceUID)
			self.PatientPosition = str(self.data.PatientSetupSequence[0].PatientPosition)
			self.NumberOfFractionsPlanned = int(self.data.FractionGroupSequence[0].NumberOfFractionsPlanned)
			self.NumberOfBeams = int(self.data.FractionGroupSequence[0].NumberOfBeams)

			# sum BeamDoses if all in the same point as secondary check for amount of dose to expect in tps dose. BeamDose is specified as per fraction
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

def pydicom_casedir(dname,loadimages=True):
	ct_dirs = glob.glob(path.join(dname,"*PLAN"))
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
				studies[a.studyid]['ct_im'].ct_to_hu(a.RescaleIntercept,a.RescaleSlope)
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
					if str(a.data.DoseUnits) != "GY":
						raise NotImplementedError("The provided dicom dose image has relative units.")
					if str(a.data.DoseType) != "PHYSICAL":
						raise NotImplementedError("The provided dicom dose image is not in physical units.")
					if str(a.data.DoseSummationType) not in ["PLAN","FRACTION"]:
						raise NotImplementedError("Dose was not computed for 'PLAN' or 'FRACTION'.")
					studies[a.studyid][a.sopid]['dose_im'] = image.image(f)
					studies[a.studyid][a.sopid]['dose_im'].mul(a.data.DoseGridScaling)
			elif a.modality == "RTPLAN":
				studies[a.studyid][a.sopid]['plan'] = a
				if loadimages and a.PatientPosition != 'HFS':
					raise NotImplementedError("Patient (Plan) is not in HFS position.")
			else:
				IOError("Expected RTDOSE or RTPLAN, but",a.modality,"was found.")

	return studies

