import image,numpy as np,dicom,glob,collections
from os import path, makedirs
import gpumcd

casedir = r"D:\postdoc\analyses\gpumcd_python\dicom\20181101 CTRT KNO-hals"

sett = gpumcd.Settings("D:\\postdoc\\gpumcd_data")
sett.debug['verbose']=3 #wanna see errythang
sett.debug['verbose']=3 #wanna see errythang

studies = dicom.pydicom_casedir(casedir)

for studyid,v in studies.items():
	# print ('brent',studyid,'\n')
	v['ct'].saveas(path.join(casedir,"xdr","ct_dump.xdr"))
	v['ct'].resample([3,3,3])
	v['ct'].saveas(path.join(casedir,"xdr","ct.xdr"))
	v['ct_obj'] = gpumcd.CT(sett,v['ct'])
	for sopid,d in v.items():
		if isinstance(d,dict):
			d['dose'].saveas(path.join(casedir,"xdr",sopid,"dose.xdr"))
			d['dose'].crop_as(v['ct'])
			d['dose'].saveas(path.join(casedir,"xdr",sopid,"dose_ctgrid.xdr"))

			p=gpumcd.Rtplan(sett, d['plan'])

			for beam in p.beams:
				gpumcd.Engine(sett,v['ct_obj'])












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