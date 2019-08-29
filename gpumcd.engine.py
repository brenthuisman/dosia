import image,numpy as np,dicom,glob,collections
from os import path, makedirs
import gpumcd

casedir = r"d:\postdoc\analyses\gpumcd_python\dicom\20181101 CTRT KNO-hals"

sett = gpumcd.Settings("d:\\postdoc\\gpumcd_data")

studies = dicom.pydicom_casedir(casedir)

for studyid,v in studies.items():
	# print ('brent',studyid,'\n')
	v['ct_im'].saveas(path.join(casedir,"xdr","ct_dump.xdr"))
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

			p=gpumcd.Rtplan(sett, d['plan'])
			ct_obj.dosemap.zero_out()

			for i,beam in enumerate(p.beams):
				eng=gpumcd.Engine(sett,ct_obj,p.accelerator.machfile)
				eng.execute_segments(beam)
				if eng.lasterror()[0] != 0:
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
			# quit()