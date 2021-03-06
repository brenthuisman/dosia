import medimage as image,numpy as np,dicom,glob,os,collections
import gpumcd
from collections import Counter

sett = gpumcd.Settings()
loadimages = False
verbose = False

dumpdir = r"Z:\brent\dicom_incoming\20190412_w19_1149\DICOM"

# dumpdir = Path(r"D:\tmp\test")
# [print(a) for a in dumpdir.rglob('*') if a.is_file()]

# dcms = [dicom.pydicom_object(a) for a in dumpdir.rglob('*') if a.is_file()]
dcms = []
notdcms = []
problem = []
problemtypes = Counter()

studies = collections.defaultdict(dict)

for dirpath, dirnames, filenames in os.walk(dumpdir):
	if len(filenames) > 0:
		firstfname = os.path.join(dirpath, filenames[0])
		try: #catch any problematic dcm
			# test if in CT dir
			dicomobj = dicom.pydicom_object(firstfname)
			if dicomobj.valid and dicomobj.sopid is None:
				#we've got a CT on our hands boys, yeehaw
				dcms.append(firstfname)
				studies[dicomobj.studyid]['ct'] = dirpath
				if loadimages:
					if dicomobj.PatientPosition != 'HFS':
						NotImplementedError("Patient (Dose) is not in HFS position.")
					studies[dicomobj.studyid]['ct_im'] = image.image(dirpath)
			elif dicomobj.valid and dicomobj.sopid is not None:
				#this aint no CT-dir, therefore, iterate over all files to see whats what.
				for filename in filenames:
					fname = os.path.join(dirpath, filename)
					dicomobj = dicom.pydicom_object(fname)

					if dicomobj.valid:
						dcms.append(fname)
					else:
						notdcms.append(fname)

					#did we make a dict for this sopid already?
					try:
						studies[dicomobj.studyid][dicomobj.sopid]
					except:
						studies[dicomobj.studyid][dicomobj.sopid]={}

					if dicomobj.modality == "RTDOSE":
						studies[dicomobj.studyid][dicomobj.sopid]['dose'] = dicomobj
						if loadimages:
							studies[dicomobj.studyid][dicomobj.sopid]['dose_im'] = image.image(filename)
							studies[dicomobj.studyid][dicomobj.sopid]['dose_im'].mul(dicomobj.data.DoseGridScaling)
					elif dicomobj.modality == "RTPLAN":
						studies[dicomobj.studyid][dicomobj.sopid]['plan'] = dicomobj
					else:
						IOError("Expected RTDOSE or RTPLAN, but",dicomobj.modality,"was found.")
			else:
				notdcms.append(firstfname)
		except Exception as e:
			if verbose:
				print(f"Problem with {dirpath}: {e}")
			problem.append(dirpath)
			problemtypes[str(e)]+=1


print(f"DCMS {len(dcms)}")
print(f"not DCMS {len(notdcms)}")
print(f"problem DCMS {len(problem)}")
print(problemtypes.most_common())


if verbose:
	[print(f"stud {a.studyid}sop {a.sopid}") for a in dcms]

def printit(studies):
	for studyid,study in studies.items():
		# print('brent',studyid)
		# print(type(study))
		for sopid,sop in study.items():
			if isinstance(sop,dict): # filter cts weg
				#FIXME: check wether SOP has both plan and dose.
				# print(sopid)
				#print(sop)
				# sop['dose']
				# sop['plan']
				# study['ct']
				try:
					a=sop['plan'].filename
					# print(sopid)
					# print(sop['plan'].filename)
					# print(sop['plan'].data.BeamSequence[0].TreatmentMachineName)
				except:
					print("EXCEPT: NO PLAN FOUND!!!!!")
					print(f"{len(list(sop))} other items found in this sop.")
					print(f"First: {list(sop)[0]}. Filename:")
					print(sop[list(sop)[0]].filename)
					# print(sop['plan'].data)


		# print(v)

		# if isinstance(v,dict): #skip ct
		# 	for sop in v.values():
		# 		print(sop['plan'].data.BeamSequence[0].TreatmentMachineName)
			# try:
			# 	print(v['plan'].data.BeamSequence[0].TreatmentMachineName)
			# except KeyError:
			# 	print (v.keys())

printit(studies)
# for dirr in glob.glob(casedir+"/*/*"):
# 	print (dirr)
# 	try:
# 		studies = dicom.build_casedir(dirr,loadimages=False)
# 		printit(studies)
# 	except KeyError: #probably one more subdir
# 		try:
# 			studies = dicom.build_casedir(glob.glob(dirr+'/*')[0])
# 			printit(studies)
# 		except:
# 			print("invalid dir encountered, skipping...")
# 			pass

