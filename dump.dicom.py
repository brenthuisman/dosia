import image,numpy as np,pydicom,glob,collections
from os import path
from os import makedirs

##############################################################################

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
			self.ct={}
			self.ct['PatientPosition']=self.data.PatientPosition
			self.ct['RescaleIntercept']=self.data.RescaleIntercept
			self.ct['RescaleSlope']=self.data.RescaleSlope
			self.ct['PatientPosition']=self.data.PatientPosition
		elif self.modality == "RTDOSE":
			self.sopid = self.data.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID
		elif self.modality == "RTPLAN":
			self.sopid = self.data.SOPInstanceUID

def pydicom_casedir(dname):
	ct_dirs = glob.glob(path.join(dname,"*PLAN"))
	upi_dirs = glob.glob(path.join(dname,"*UPI*"))

	studies = collections.defaultdict(dict)

	for ct_dir in ct_dirs:
		a = pydicom_object(ct_dir)
		if a.modality == 'CT':
			studies[a.studyid]['ct'] = ct_dir
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
				studies[a.studyid][a.sopid]['dose'] = f
			elif a.modality == "RTPLAN":
				studies[a.studyid][a.sopid]['plan'] = f
			else:
				IOError("Expected RTDOSE or RTPLAN, but",a.modality,"was found.")

	# todo: return studies[list(studies.keys())[0]] if len(studies)==1
	return studies


##############################################################################

casedir = r"D:\postdoc\analyses\gpumcd_python\dicom\20181101 CTRT KNO-hals"

studies = pydicom_casedir(casedir)

for studyid,v in studies.items():
	ct=image.image(v['ct'])
	ct.resample([3,3,3])
	ct.saveas(path.join(casedir,"xdr","ct.xdr"))
	for sopid,d in v.items():
		if isinstance(d,dict):
			# try:
			# 	d['plan']
			# except:
			# 	print('geen plan?')
			# try:
			b=image.image(d['dose'])
			b.saveas(path.join(casedir,"xdr",sopid,"dose.xdr"))
			b.crop_as(ct)
			b.saveas(path.join(casedir,"xdr",sopid,"dose_ctgrid.xdr"))
			# except:
			# 	print('geen dose?')














quit()


##############################################################################

#print(dir(data.BeamSequence[0].ControlPointSequence[0]))

# for key, val in data.items():
# 	if str(key).startswith("_"):
# 		continue
# 	print(key, val)

# weights_beam_0 = []

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