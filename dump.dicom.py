import image,numpy as np,dicom,glob,collections
from os import path, makedirs
import gpumcd

sett = gpumcd.Settings("d:\\postdoc\\gpumcd_data")

casedir = r"Z:\brent\dicom_incoming\20190412_w19_1149\DICOM"

for dirr in glob.glob(casedir+"/*/*"):
	print (dirr)
	try:
		studies = dicom.pydicom_casedir(dirr)
		for studyid,v in studies.items():
			print ('brent',studyid,'\n')
			dicom.run_casedir(sett,dirr,v)
	except KeyError: #probably one more subdir
		try:
			studies = dicom.pydicom_casedir(glob.glob(dirr+'/*')[0])
			for studyid,v in studies.items():
				print ('brent',studyid,'\n')
				dicom.run_casedir(sett,dirr,v)
		except:
			print("invalid dir encountered, skipping...")
			pass

