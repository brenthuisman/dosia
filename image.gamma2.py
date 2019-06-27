import image

i1 = image.image(r"D:\postdoc\analyses\gpumcd_python\dose_1.xdr")
i2 = image.image(r"D:\postdoc\analyses\gpumcd_python\dose_2.xdr")

gamma = i1.compute_gamma(i2,1,2)
gamma.saveas(r"D:\postdoc\analyses\gpumcd_python\dose_gamma.xdr")