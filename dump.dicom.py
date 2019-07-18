import image,numpy as np,dicom,glob,collections
from os import path, makedirs
import gpumcd


casedir = r"Z:\brent\dicom_incoming\20190412_w19_1149\DICOM"
for dirr in glob.glob(casedir+"/*/*"):
	# print (dirr)
	s = dicom.pydicom_casedir(dirr,False)

	for studyid,v in s.items():
		for sopid,d in v.items():
			if isinstance(d,dict):
				try:
					# print(d['dose'].data.DoseUnits)
					# print(d['dose'].data.DoseType)
					print(d['dose'].data.DoseSummationType)
					# print(d['dose'].data.DoseGridScaling)
				except KeyError:
					print ("there was no dose in",dirr,studyid,sopid)

quit()

casedir = r"d:\postdoc\analyses\gpumcd_python\dicom\20181101 CTRT KNO-hals"

sett = gpumcd.Settings("d:\\postdoc\\gpumcd_data")

studies = dicom.pydicom_casedir(casedir)

for studyid,v in studies.items():
	# v['ct'].saveas(path.join(casedir,"xdr","ct_dump.xdr"))
	for sopid,d in v.items():
		if isinstance(d,dict):
			d['dose'].saveas(path.join(casedir,"xdr",sopid,"dose_tps.xdr"))
			ctcpy = v['ct']
			ctcpy.crop_as(d['dose'])
			ctcpy.saveas(path.join(casedir,"xdr",sopid,"ct_on_dosegrid.xdr"))
			ct_obj = gpumcd.CT(sett,ctcpy)

			p=gpumcd.Rtplan(sett, d['plan'])
			ct_obj.dosemap.zero_out()

			for i,beam in enumerate(p.beams):
				eng=gpumcd.Engine(sett,ct_obj,p.accelerator.machfile)
				eng.execute_segments(beam)
				print (eng.lasterror())
				eng.get_dose(ct_obj.dosemap)
			ct_obj.dosemap.saveas(path.join(casedir,"xdr",sopid,"dose_gpumcd.xdr"))
