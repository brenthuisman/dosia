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
		# print(dir(self.data))
		self.modality = self.data.Modality
		self.sopid = None
		self.studyid = self.data.StudyInstanceUID
		if self.modality not in ['CT','RTDOSE','RTPLAN']:
			NotImplementedError("You provided a file that is not a CT, RTDOSE or RTPLAN!")
			#TODO Struct?
		elif self.modality == "CT":
			self.PatientPosition=self.data.PatientPosition
			self.RescaleIntercept=self.data.RescaleIntercept
			self.RescaleSlope=self.data.RescaleSlope
			self.PatientPosition=self.data.PatientPosition
		elif self.modality == "RTDOSE":
			self.sopid = self.data.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID
		elif self.modality == "RTPLAN":
			self.sopid = self.data.SOPInstanceUID

def pydicom_casedir(dname):#,settings):
	#assert(isinstance(settings,gpumcd.Settings))
	ct_dirs = glob.glob(path.join(dname,"*PLAN"))
	upi_dirs = glob.glob(path.join(dname,"*UPI*"))

	studies = collections.defaultdict(dict)

	for ct_dir in ct_dirs:
		a = pydicom_object(ct_dir)
		if a.modality == 'CT':
			studies[a.studyid]['ct'] = image.image(ct_dir)
			#seems that the images is already in HU units
			#studies[a.studyid]['ct'].ct_to_hu(a.RescaleIntercept,a.RescaleSlope)
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
				studies[a.studyid][a.sopid]['dose'] = image.image(f)
			elif a.modality == "RTPLAN":
				studies[a.studyid][a.sopid]['plan'] = a
			else:
				IOError("Expected RTDOSE or RTPLAN, but",a.modality,"was found.")

	return studies

