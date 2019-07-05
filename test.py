import image

a=image.image(r"D:\postdoc\analyses\gpumcd_python\dicom\20181101 CTRT KNO-hals\xdr\2.25.1025001435024675917588954042793107482\dose_gpumcd.xdr")


a.imdata = a.imdata.reshape(a.imdata.shape[::-1])

a.saveas(r"D:\postdoc\analyses\gpumcd_python\dicom\20181101 CTRT KNO-hals\xdr\2.25.1025001435024675917588954042793107482\dose_gpumcd_edit.xdr")