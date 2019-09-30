from medimage import image
from .settings import Settings
from .gpumcdwrapper import Phantom
from os import path

class CT():
	def __init__(self,settings,ct_image): #,intercept=0,slope=1):
		'''
		The supplied image is assumed to have its voxels set to HU.
		'''
		assert(isinstance(ct_image,image))
		assert(isinstance(settings,Settings))

		hu2dens_table=[[],[]]
		with open(path.join(settings.directories['hounsfield_conversion'],'hu2dens.ini'),'r') as f:
			for line in f.readlines():
				if line.startswith('#'):
					continue
				hu2dens_table[0].append(float(line.split()[0]))
				hu2dens_table[1].append(float(line.split()[1]))
		dens2mat_table=[[],[]]
		with open(path.join(settings.directories['hounsfield_conversion'],'dens2mat.ini'),'r') as f:
			for line in f.readlines():
				if line.startswith('#'):
					continue
				dens2mat_table[0].append(float(line.split()[0]))
				dens2mat_table[1].append(line.split()[1])

		dens=ct_image.copy()
		# dens.ct_to_hu(intercept,slope)

		if path.isdir(settings.debug['output']):
			dens.saveas(path.join(settings.debug['output'],'ct_as_hu.xdr'))

		dens.hu_to_density(hu2dens_table)
		med=dens.copy()

		self.materials = med.density_to_materialindex(dens2mat_table)
		self.materials.append("Tungsten") # collimator material

		self.phantom=Phantom(massDensityArray_image=dens,mediumIndexArray_image=med)
		self.dosemap = image(DimSize=med.header['DimSize'], ElementSpacing=med.header['ElementSpacing'], Offset=med.header['Offset'], dt='<f4')

		if path.isdir(settings.debug['output']):
			dens.saveas(path.join(settings.debug['output'],'dens.xdr'))
			med.saveas(path.join(settings.debug['output'],'med.xdr'))
