import image

im=image.image("/home/brent/data/phd/art2_lyso_box/stage2_box15_ibacuts/data/source-160.mhd")
im.imdata[0:50,:,:,:] = 0
im.saveas("/home/brent/data/phd/art2_lyso_box/stage2_box15_ibacuts/data/source-160-0.mhd")

#this image has FOP at x=+50mm. We want to zero out in a window of +/-5cm around this point. Since we dont have to zero out post FOP (is already zero), we just need to zero all negative X voxels. NOTE, image is 4D.
