import tableio,os,copy
from subprocess import call

'''
This script converts a macfile to output compatible with rtkDrawGeometricPhantom.

The script is _very_ limited. It only deals with non-nested boxes, with units in mm.
'''

class tovoxel:
	def __init__(self,macfile,spacing=2,containsize=700):
		#size doesn't really matter, other than that it musnt be too large (memory) and should be able to contain the phantom, we crop afterwards anyway.
		self.spacing=float(spacing)
		self.spacingstr=str(spacing)
		#containsize must be uneven for correct trunctation. centervoxel is aligned at 0,0,0.
		self.containsize=float(containsize)-self.spacing/2.
		self.containsizestr=str(self.containsize)
		self.sizeinvox = str(int(self.containsize / self.spacing)) #size of the container in voxels
		self.macfile = macfile
		self.densityfile =   macfile[:-4]+".densityfile.txt"
		self.phantomfile =   macfile[:-4]+".phantomfile.txt"
		self.maskfile =      macfile[:-4]+".maskfile000.txt"
		self.imagefile =     macfile[:-4]+".imagefile.mhd"
		self.maskimagefile = macfile[:-4]+".maskfile000.mhd"
		# predefined background, set to Air.
		# TODO: option to change this.
		# reason not to use the /gate/world is that this volume usually is a volume too large.
		self.density = [[-1000,0,'Vacuum']]
		self.phantom = [["[Box]","A="+self.containsizestr,"B="+self.containsizestr,"C="+self.containsizestr,"x=0","y=0","z=0","beta=0","gray=-1000"]]
		self.mask =    [["[Box]","A="+self.containsizestr,"B="+self.containsizestr,"C="+self.containsizestr,"x=0","y=0","z=0","beta=0","gray=-1000"]]

		self.boxes = [] #intermediate description of the phantom, only contains geometry

		self.loadmac(macfile)
		self.setdensity()
		self.setphantom()

	def loadmac(self,filename):
		print("NOTE! Your macfile must have mm as unit for length!")
		print("NOTE! This tools puts centers on the voxel center. So only uneven sized output possible.")
		sourcefile = open(filename,'r')
	
		capture_box = 0

		for index, line in enumerate(sourcefile):
			newline = line.strip()
			if len(newline)==0:
				continue
			
			newline=newline.split()
		
			if "/daughters/insert" in newline[0]:
				#we are reading a new volume.
				#TODO make sure previous volume was completely read (no missing field)
				if newline[1] == 'box':
					capture_box = 1
					self.boxes.append(["",0,0,0,0,0,0])
					continue
				if newline[1] != 'box':
					capture_box = 0
					#TODO handle other shapes
					continue
	
			if capture_box == 1:
				if "setMaterial" in newline[0]:
					self.boxes[-1][0] = newline[1]
					continue
				
				if "setXLength" in newline[0]:
					#TODO deal with unit in newline[2]
					self.boxes[-1][1] = float(newline[1])/2.
					#half a spacing because it is halfX/Y/Z.
					continue
				
				if "setYLength" in newline[0]:
					self.boxes[-1][2] = float(newline[1])/2.
					continue
				
				if "setZLength" in newline[0]:
					self.boxes[-1][3] = float(newline[1])/2.
					continue
				
				if "setTranslation" in newline[0]:
					self.boxes[-1][4] = float(newline[1])#/(self.spacing/2.)#suddenly, this MUST remain in real coords, not voxelcoords.
					self.boxes[-1][5] = float(newline[2])#/(self.spacing/2.)
					self.boxes[-1][6] = float(newline[3])#/(self.spacing/2.)
					continue
	
		sourcefile.close()

	def setdensity(self):
		for index, box in enumerate(self.boxes):
			self.density.append([index*2, index*2+2, box[0]])
			box[0] = 1000+index*2+1

	def writedensityfile(self,filename):
		tableio.write(self.density,filename)

	def setphantom(self):
		for box in self.boxes:
			self.phantom.append(["[Box]","A="+str(box[1]),"B="+str(box[2]),"C="+str(box[3]),"x="+str(box[4]),
			"y="+str(box[5]),"z="+str(box[6]),"beta=0","gray="+str(box[0])])
			self.mask.append(["[Box]","A="+str(box[1]),"B="+str(box[2]),"C="+str(box[3]),"x="+str(box[4]),
			"y="+str(box[5]),"z="+str(box[6]),"beta=0","gray=1000"])

	def writephantomfile(self,filename):
		tableio.write(self.phantom,filename)

	def makeimage(self):
		self.writedensityfile(self.densityfile)
		print("Your densityfile was saved as",self.densityfile)
		self.writephantomfile(self.phantomfile)
		print("Your phantomfile was saved as",self.phantomfile)
		call(["rtkdrawgeometricphantom","--phantomfile",self.phantomfile,"--dimension",self.sizeinvox,"--spacing",self.spacingstr,"--output",self.imagefile])
		call(["clitkCropImage","-i",self.imagefile,"-o",self.imagefile,"--BG=-1000"])
		#call(["clitkImageConvert","-i",self.imagefile,"-o",self.imagefile,"-c"])
		print("Your image was saved as",self.imagefile)

	def makemask(self):
		for i in range(1,len(self.mask)):
			mask = copy.deepcopy(self.mask)
			mask[i][-1] = "gray=1001"
			#tableio.print2d(mask)
			maskfile = self.maskfile.replace("000",str(i))
			maskimagefile = self.maskimagefile.replace("000",str(i))
			tableio.write(mask,maskfile)
			print("Your maskfile was saved as",maskfile)
			call(["rtkdrawgeometricphantom","--phantomfile",maskfile,"--dimension",self.sizeinvox,"--spacing",self.spacingstr,"--output",maskimagefile])
			call(["clitkCropImage","-i",maskimagefile,"-o",maskimagefile,"--BG=-1000"])
			call(["clitkBinarizeImage","-i",maskimagefile,"-o",maskimagefile,"-l","0.5","-u","1.5"]) #the intensity egion that is 1, and not 0
			#call(["clitkImageConvert","-i",maskimagefile,"-o",maskimagefile,"-c"])
			print("Your mask was saved as",maskimagefile)
