import sys,image
from scipy import ndimage
import numpy as np

dicom_directory = r"D:\postdoc\analyses\gpumcd_python\dicom\20181101 CTRT KNO-hals\2. HalsSupracl + C   3.0  B40s PLAN"

dicom_file = r"D:\postdoc\analyses\gpumcd_python\dicom\stijn\IMRTa\Monaco\F180307A_MonacoRecalc_Dose.dcm"

xdr_file = r"D:\postdoc\analyses\gpumcd_python\med.xdr"

dicom_directory_image = image.image(dicom_directory)
# dicom_file_image = image.image(dicom_file)
xdr_file_image = image.image(xdr_file)

print(dicom_directory_image.imdata.shape)
print(dicom_directory_image.header['ElementSpacing'])
print(dicom_directory_image.header['Offset'])
print(dicom_directory_image.header['NDims'])
print(dicom_directory_image.header['DimSize'])

# print(dicom_file_image.header['ElementSpacing'])
# print(dicom_file_image.header['Offset'])
# print(dicom_file_image.header['NDims'])
# print(dicom_file_image.header['DimSize'])

# print(xdr_file_image.header['ElementSpacing'])
# print(xdr_file_image.header['Offset'])
# print(xdr_file_image.header['NDims'])
# print(xdr_file_image.header['DimSize'])





# dicom_directory_image.imdata = ndimage.zoom(dicom_directory_image.imdata,0.3,order=1)

# dicom_directory_image.imdata = dicom_directory_image.imdata.reshape(dicom_directory_image.imdata.shape[::-1])




# dicom_directory_image.saveas(r"D:\postdoc\analyses\gpumcd_python\TESTDCMDIR.mhd")


xdr_file_image.resample([3,3,3])
xdr_file_image.saveas(r"D:\postdoc\analyses\gpumcd_python\xdrresized.mhd")

dicom_directory_image.resample([3,3,3])
print(dicom_directory_image.imdata.shape)
print(dicom_directory_image.header['ElementSpacing'])
print(dicom_directory_image.header['Offset'])
print(dicom_directory_image.header['NDims'])
print(dicom_directory_image.header['DimSize'])


# dicom_directory_image.imdata = dicom_directory_image.imdata.reshape(dicom_directory_image.imdata.shape[::-1])



dicom_directory_image.saveas(r"D:\postdoc\analyses\gpumcd_python\TESTDCMDIR_RESIZED.mhd")







quit()








# fname = sys.argv[-1]

# data = pydicom.dcmread(fname,force=True)

# print(dir(data))


try:
	print (data.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID) # if fname is a dose, this value corresponds to the plan's SOPInstanceUID
	print("dis nen doos")
except:
	print (data.SOPInstanceUID)
	print("ne planneke")

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