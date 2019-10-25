import medimage as image,numpy as np,dicom,glob,collections
from os import path, makedirs
import gpumcd

sett = gpumcd.Settings()

casedir = r"Z:\brent\dicom_incoming\20190412_w19_1149\DICOM"

def printit(studies):
	for studyid,v in studies.items():
		print('brent',studyid,'\n')
		print(v)
		if isinstance(v,dict): #skip ct
			print(v['plan'].data.BeamSequence[0].TreatmentMachineName)


for dirr in glob.glob(casedir+"/*/*"):
	print (dirr)
	try:
		studies = dicom.build_casedir(dirr,loadimages=False)
		printit(studies)
	except KeyError: #probably one more subdir
		try:
			studies = dicom.build_casedir(glob.glob(dirr+'/*')[0])
			printit(studies)
		except:
			print("invalid dir encountered, skipping...")
			pass

