import medimage as image

tps = image.image("D:/postdoc/analyses/gpumcd_python/dicom/20181101 CTRT KNO-hals/1. UPI263538/2.25.117736802457958133832899838499337503296")
xdr = image.image("D:/postdoc/analyses/gpumcd_python/ct.xdr")

tps.saveas("D:/postdoc/analyses/gpumcd_python/TEST2.dcm")
xdr.saveas("D:/postdoc/analyses/gpumcd_python/TEST.dcm")