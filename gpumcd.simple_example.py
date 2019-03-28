import ctypes,numpy as np
from nki import gpumcd
from os import path
import image

rootdir = "D:/postdoc/analyses/gpumcd_python"

print('Start of program.')

def strlist2charpp(stringlist):
	argc = len(stringlist)
	Args = ctypes.c_char_p * (len(stringlist)+1)
	argv = Args(*[ctypes.c_char_p(arg.encode("utf-8")) for arg in stringlist])
	return argc,argv

def str2charp(string):
	return ctypes.c_char_p(string.encode("utf-8"))

def make_c_array(obj_of_type,N):
	#todo: init each member or not
	return (obj_of_type * N)()

def c_array_to_pointer(array, return_tuple=False):
	if return_tuple == True:
		return len(array), ctypes.cast(array,ctypes.POINTER(type(array[0])))
	else:
		return ctypes.cast(array,ctypes.POINTER(type(array[0])))


materials=["Water"]

physicsSettings = gpumcd.PhysicsSettings()
planSettings = gpumcd.PlanSettings()

physicsSettings.photonTransportCutoff = 0.01
physicsSettings.electronTransportCutoff = 0.189
physicsSettings.inputMaxStepLength = 0.75
physicsSettings.magneticField = gpumcd.Float3(0,0,0)
physicsSettings.referenceMedium = -1
physicsSettings.useElectronInAirSpeedup = 1
physicsSettings.electronInAirSpeedupDensityThreshold = 0.002

planSettings.goalSfom = 1
planSettings.statThreshold = 0.5
planSettings.maxNumParticles = int(1e13)
planSettings.densityThresholdSfom = 0.2
planSettings.densityThresholdOutput = 0.0472
planSettings.useApproximateStatistics = 1

phantom = gpumcd.Phantom(50*50*50)
phantom.numVoxels.x = 50
phantom.numVoxels.y = 50
phantom.numVoxels.z = 50

phantom.voxelSizes.x = 0.2
phantom.voxelSizes.y = 0.2
phantom.voxelSizes.z = 0.2

phantom.phantomCorner.x = -5.0
phantom.phantomCorner.y = -5.0
phantom.phantomCorner.z = -5.0

nvox = phantom.numVoxels.x*phantom.numVoxels.y*phantom.numVoxels.z
for i in range(nvox):
	phantom.massDensityArray[i]=1
	phantom.mediumIndexArray[i]=0

lasterror=ctypes.create_string_buffer(1000)

print('Scene definition loaded.')

##TODO abspath doesnt work for some reason?
libgpumcd = ctypes.CDLL(rootdir+"/libgpumcd.dll")

print('libgpumcd loaded, starting gpumcd init...')

## TODO libgpumcd.initGpumcd.argtypes = ([c_char_p, c_int, c_char_p] etc etc

retval = libgpumcd.initGpumcd(
	0,
	0,
	str2charp("D:/postdoc/gpumcd_data/materials_clin"),
	*strlist2charpp(materials),
	physicsSettings,
	phantom,
	str2charp("D:/postdoc/gpumcd_data/machines/machine_van_sami/brentAgility.beamlets.gpumdt"),
	2,
	ctypes.byref(lasterror)
)

print('gpumcd init done.')

print(retval,lasterror.value.decode('utf-8'))

BeamFrames = make_c_array(gpumcd.BeamFrame,2)
BeamFrames[0]=gpumcd.BeamFrame(1)
BeamFrames[0].beamInfo[0].relativeWeight = 100
BeamFrames[0].beamInfo[0].isoCenter.x=0
BeamFrames[0].beamInfo[0].isoCenter.y=0
BeamFrames[0].beamInfo[0].isoCenter.z=0
BeamFrames[0].beamInfo[0].collimatorAngle.first=0
BeamFrames[0].beamInfo[0].collimatorAngle.second=0
BeamFrames[0].beamInfo[0].couchAngle.first=0
BeamFrames[0].beamInfo[0].couchAngle.second=0
BeamFrames[0].beamInfo[0].gantryAngle.first=0
BeamFrames[0].beamInfo[0].gantryAngle.second=0
BeamFrames[0].beamInfo[0].fieldMax.first=2
BeamFrames[0].beamInfo[0].fieldMax.second=2
BeamFrames[0].beamInfo[0].fieldMin.first=-2
BeamFrames[0].beamInfo[0].fieldMin.second=-2
BeamFrames[1]=gpumcd.BeamFrame(1)
BeamFrames[1].beamInfo[0].relativeWeight = 100
BeamFrames[1].beamInfo[0].isoCenter.x=0
BeamFrames[1].beamInfo[0].isoCenter.y=0
BeamFrames[1].beamInfo[0].isoCenter.z=0
BeamFrames[1].beamInfo[0].collimatorAngle.first=0
BeamFrames[1].beamInfo[0].collimatorAngle.second=0
BeamFrames[1].beamInfo[0].couchAngle.first=0
BeamFrames[1].beamInfo[0].couchAngle.second=0
BeamFrames[1].beamInfo[0].gantryAngle.first=90
BeamFrames[1].beamInfo[0].gantryAngle.second=90
BeamFrames[1].beamInfo[0].fieldMax.first=1
BeamFrames[1].beamInfo[0].fieldMax.second=1
BeamFrames[1].beamInfo[0].fieldMin.first=-1
BeamFrames[1].beamInfo[0].fieldMin.second=-1

print('executing simulation...')

retval = libgpumcd.execute_beamlets(
	*c_array_to_pointer(BeamFrames,True),
	planSettings
)

print(retval)

dose = image.image(DimSize=[50,50,50], ElementSpacing=[0.2,0.2,0.2], dt='<f4')

libgpumcd.getDose(dose.get_ctypes_pointer_to_data())

dose.saveas(path.join(rootdir,'dose.xdr'))